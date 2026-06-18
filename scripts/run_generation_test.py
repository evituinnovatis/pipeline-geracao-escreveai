from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from escreveai.aws import criar_s3_client
from escreveai.briefing import brief_para_consulta_rag
from escreveai.config import load_settings
from escreveai.context_builder import montar_contexto_rag
from escreveai.db_aurora import conexao_pg
from escreveai.embeddings import criar_embeddings_bge_m3
from escreveai.generation import (
    gerar_projeto_com_validacao,
    gerar_projeto_llm_only,
)
from escreveai.llm import (
    criar_chain_geracao,
    criar_llm_groq,
    criar_parser_projeto,
    criar_parser_projeto_llm_only,
    criar_prompt_geracao,
    criar_prompt_geracao_llm_only,
)
from escreveai.pipeline_report import imprimir_resumo_pipeline
from escreveai.rag_selection import (
    montar_auditoria,
    selecionar_contexto_rag_robusto,
)
from escreveai.reference_files import baixar_documentos_referencia
from escreveai.retrieval import recuperar_chunks_candidatos


RAG_MIN_SCORE_THRESHOLD = 0.5


BRIEF_USUARIO: dict[str, Any] = {
    "titulo": "Financiamento Adicional para o Projeto de Paz e Desenvolvimento",
    "areasRelacionadas": [
        "Educacao",
        "Agricultura",
        "Economia",
    ],
    "areasRelacionadasOutro": (
        "Construção da paz, reintegração social e apoio a populações deslocadas"
    ),
    "resumo": (
        "Financiamento adicional para consolidar o Projeto de Paz e Desenvolvimento "
        "na Colômbia, expandindo ações para Valle del Cauca e fortalecendo "
        "iniciativas locais de desenvolvimento e paz."
    ),
    "objetivos": (
        "Apoiar populações vulneráveis, de baixa renda e deslocadas em comunidades "
        "rurais e urbanas afetadas por conflito, reduzindo sua exposição à violência "
        "e promovendo reintegração social e econômica sustentável."
    ),
    "publicoAlvo": (
        "Populações vulneráveis, famílias de baixa renda, pessoas deslocadas pela "
        "violência, comunidades rurais e urbanas afetadas por conflito, organizações "
        "parceiras, unidades territoriais e comunidades indígenas."
    ),
    "metasEtapasFases": (
        "Expansão para Valle del Cauca, consolidação de subprojetos regionais, "
        "fortalecimento institucional de organizações parceiras e unidades "
        "territoriais, coordenação, avaliação, supervisão e estudos do projeto."
    ),
    "entregaveis": (
        "Subprojetos territoriais, apoio social, econômico, ambiental e comunitário, "
        "fortalecimento institucional, planos de desenvolvimento indígena, estudos, "
        "monitoramento e planos de mitigação ambiental."
    ),
    "resultadoEsperado": (
        "Consolidação da estratégia de construção da paz, melhoria da qualidade de "
        "vida de comunidades vulneráveis, reintegração de famílias deslocadas e "
        "fortalecimento da capacidade local de planejar, implementar e monitorar "
        "iniciativas de desenvolvimento e paz."
    ),
    "duracaoPeriodo": "",
    "ragContextSource": "external",
    "outputMode": "draft",
}


def imprimir_resultados(resultados: list[dict[str, Any]]) -> None:
    for i, r in enumerate(resultados, start=1):
        print("=" * 120)
        print(f"Resultado {i}")
        print(f"Projeto: {r['projeto_titulo']}")
        print(f"Área: {r['projeto_area']}")
        print(f"Origem: {r['projeto_origem']}")
        print(f"Chunk ID: {r['chunk_id']}")
        print(f"Projeto ID: {r['projeto_id']}")
        print(f"Chunk index: {r['chunk_index']}")
        print(f"Páginas: {r['page_start']} - {r['page_end']}")
        print(f"Token count: {r['token_count']}")
        print(f"Char count: {r['char_count']}")
        print(f"Modelo embedding: {r['model_embedding']}")
        print(f"Dimensões: {r['dimensions']}")
        print(f"Score similaridade: {r['score_similaridade']:.4f}")
        print(f"Distância cosseno: {r['distancia_cosseno']:.4f}")
        print()
        print(r["texto_chunk"][:300])
        print()


def main() -> None:
    settings = load_settings(PROJECT_ROOT / ".env")

    embeddings = criar_embeddings_bge_m3(
        model_name=settings.embedding_model_name,
        use_fp16=settings.embedding_use_fp16,
        batch_size=settings.embedding_batch_size,
        max_length=settings.embedding_max_length,
    )

    llm = criar_llm_groq(
        api_key=settings.groq_api_key,
        model=settings.groq_generation_model,
        temperature=0,
    )

    # Chain do caminho RAG (contrato estrito, com referências obrigatórias).
    parser = criar_parser_projeto()
    prompt = criar_prompt_geracao()
    chain = criar_chain_geracao(llm=llm, prompt=prompt, parser=parser)

    # Chain do caminho de fallback LLM-only (sem referências rastreáveis).
    parser_llm_only = criar_parser_projeto_llm_only()
    prompt_llm_only = criar_prompt_geracao_llm_only()
    chain_llm_only = criar_chain_geracao(
        llm=llm, prompt=prompt_llm_only, parser=parser_llm_only
    )

    consulta_rag = brief_para_consulta_rag(BRIEF_USUARIO)

    with conexao_pg(settings.database_url) as conn:
        chunks_candidatos = recuperar_chunks_candidatos(
            conn=conn,
            embeddings=embeddings,
            consulta=consulta_rag,
            rag_context_source=BRIEF_USUARIO["ragContextSource"],
            dimensions=settings.embedding_dimensions,
        )

        print(f"chunks_candidatos: {len(chunks_candidatos)}")

        selecao = selecionar_contexto_rag_robusto(
            chunks_candidatos=chunks_candidatos,
            rag_context_source=BRIEF_USUARIO["ragContextSource"],
            min_score_threshold=RAG_MIN_SCORE_THRESHOLD,
            top_projects_internal=3,
            top_projects_external=3,
            top_projects_both_internal=2,
            top_projects_both_external=1,
            top_chunks_per_project=5,
        )

        if selecao.modo_geracao == "llm_only":
            resultado_geracao = gerar_projeto_llm_only(
                chain=chain_llm_only,
                consulta_rag=consulta_rag,
                modo_saida=BRIEF_USUARIO["outputMode"],
                format_instructions=parser_llm_only.get_format_instructions(),
                motivo_fallback=selecao.motivo_fallback,
            )
        else:
            imprimir_resultados(selecao.chunks_finais)

            contexto_rag = montar_contexto_rag(selecao.chunks_finais)
            print(contexto_rag)

            resultado_geracao = gerar_projeto_com_validacao(
                chain=chain,
                consulta_rag=consulta_rag,
                contexto_rag=contexto_rag,
                modo_saida=BRIEF_USUARIO["outputMode"],
                format_instructions=parser.get_format_instructions(),
                resultados=selecao.chunks_finais,
            )

        auditoria = montar_auditoria(
            selecao=selecao,
            consulta_rag=consulta_rag,
            modelo=settings.groq_generation_model,
        )

        print(f"modo_geracao: {selecao.modo_geracao}")
        print(resultado_geracao)
        print(auditoria)

        if selecao.modo_geracao == "rag" and selecao.chunks_finais:
            projeto_ids = list({
                str(c["projeto_id"]) for c in selecao.chunks_finais
            })
            s3_client = criar_s3_client(
                region_name=settings.aws_region,
                profile_name=settings.aws_profile,
            )
            arquivos_baixados = baixar_documentos_referencia(
                conn=conn,
                s3_client=s3_client,
                projeto_ids=projeto_ids,
                pasta_destino=str(PROJECT_ROOT / settings.references_dir),
            )
            print(arquivos_baixados)

        imprimir_resumo_pipeline(
            chunks_candidatos,
            selecao,
            top_chunks_per_project=5,
        )


if __name__ == "__main__":
    main()