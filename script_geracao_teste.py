#!/usr/bin/env python
# coding: utf-8

# ### **Script Teste de Geração**
# ##### Validar: Retrievel funcionando, Prompt + Contexto e Resposta com Rastreabilidade

# In[3]:


import os
import sys
import contextlib
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

import psycopg
from pgvector.psycopg import register_vector

from langchain_core.embeddings import Embeddings
from langchain_groq import ChatGroq

from FlagEmbedding import BGEM3FlagModel
from groq import Groq

from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from pathlib import Path
import boto3


# ##### Carregar Variáveis de Ambiente

# In[4]:


load_dotenv()

API_GRQ_LLM=os.getenv("API_KEY_GROQ_ESCREVEAI_VICTOR")
DATABASE_URL=os.getenv("DATABASE_URL")

#GROQ_GENERATION_MODEL = "llama-3.1-8b-instant"
GROQ_GENERATION_MODEL = "openai/gpt-oss-120b"


# In[5]:


required_envs = {
    "API_KEY_GROQ_ESCREVEAI_VICTOR": API_GRQ_LLM,
    "DATABASE_URL": DATABASE_URL,
}

missing = [key for key, value in required_envs.items() if not value]

if missing:
    raise ValueError(f"Variáveis de ambiente ausentes: {missing}")


# ##### Estabelecer Conexões Aurora AWS e GROQ

# In[6]:


# Estabeler conexão com o banco de dados
# Função para abrir conexão com o Aurora AWS
def abrir_conexao_pg():
    conn = psycopg.connect(
        DATABASE_URL,
        autocommit=False,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )
    register_vector(conn)
    return conn

conn = abrir_conexao_pg()

# Estabelecer conexão com o S3
AWS_REGION = "us-east-1"
AWS_PROFILE = "victor.eduardo"

session = boto3.Session(
    profile_name=AWS_PROFILE,
    region_name=AWS_REGION,
)

s3_client = session.client("s3")
sts_client = session.client("sts")

# Estabelecer conexão com o Groq
client = Groq(api_key=API_GRQ_LLM)


# #### **Modelo de Embedding do Input do Usuário**

# In[7]:


class BGE_M3_Embeddings(Embeddings):
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        use_fp16: bool = True,
        batch_size: int = 12,
        max_length: int = 8192,
    ):
        self.model = BGEM3FlagModel(
            model_name,
            use_fp16=use_fp16,
        )
        self.batch_size = batch_size
        self.max_length = max_length

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            max_length=self.max_length,
        )["dense_vecs"]

        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(
            [text],
            batch_size=1,
            max_length=self.max_length,
        )["dense_vecs"][0]

        return embedding.tolist()


# Modelo de embeddings da resposta do usuário da EscreveAI
modelo_baai_embeddings = BGE_M3_Embeddings(
    model_name="BAAI/bge-m3",
    use_fp16=True,
    batch_size=12,
    max_length=8192,
    )


# ##### **Instânciar LLM de Geração**

# In[8]:


# Modelo de LLM usado na geração da resposta do usuário
llm_groq = ChatGroq(
    model=GROQ_GENERATION_MODEL,
    temperature=0.1,
    api_key=API_GRQ_LLM,
)


# In[9]:


# Função para transformar o briefing inteiro em uma consulta semântica única

def brief_para_consulta_rag(brief: dict) -> str:
    areas = ", ".join(brief.get("areasRelacionadas", []))

    if "Outro" in brief.get("areasRelacionadas", []):
        outro = brief.get("areasRelacionadasOutro", "").strip()
        if outro:
            areas += f", {outro}"

    partes_projetos = [
        f"Título do projeto: {brief.get('titulo', '')}",
        f"Áreas relacionadas: {areas}",
        f"Resumo do projeto: {brief.get('resumo', '')}",
        f"Objetivos: {brief.get('objetivos', '')}",
        f"Público-alvo: {brief.get('publicoAlvo', '')}",
        f"Metas, etapas e fases: {brief.get('metasEtapasFases', '')}",
        f"Entregáveis: {brief.get('entregaveis', '')}",
        f"Resultado esperado: {brief.get('resultadoEsperado', '')}",
        f"Duração/período: {brief.get('duracaoPeriodo', '')}",
    ]

    return "\n".join(
        parte for parte in partes_projetos
        if parte.split(":", 1)[1].strip()
    )


# In[10]:


brief_usuario = {
    "titulo": "Capacitação em IA para professores",
    "areasRelacionadas": ["Educação", "Tecnologia"],
    "areasRelacionadasOutro": "",
    "resumo": "Projeto de formação continuada para professores da educação básica sobre uso pedagógico de inteligência artificial.",
    "objetivos": "Capacitar docentes para usar IA na criação de planos de aula, avaliação e personalização da aprendizagem.",
    "publicoAlvo": "Professores da educação básica da rede pública.",
    "metasEtapasFases": "Diagnóstico, oficinas práticas, acompanhamento pedagógico e avaliação final.",
    "entregaveis": "Materiais didáticos, trilha formativa, relatório de impacto e plano de continuidade.",
    "resultadoEsperado": "Professores capazes de aplicar ferramentas de IA de forma ética, crítica e produtiva.",
    "duracaoPeriodo": "12",
    "ragContextSource": "internal",
    "outputMode": "draft",
}

consulta_rag = brief_para_consulta_rag(brief_usuario)
print(consulta_rag)


# In[11]:


brief_usuario = {
    "titulo": "Restauração das fachadas da Faculdade de Medicina da UFRGS",
    "areasRelacionadas": ["Cultura", "Patrimônio Histórico", "Educação"],
    "areasRelacionadasOutro": "Intervenções em bens imóveis tombados/acautelados",
    "resumo": "Restauração das fachadas sul e noroeste do Antigo Prédio da Faculdade de Medicina da UFRGS, em Porto Alegre.",
    "objetivos": "Preservar o patrimônio histórico da UFRGS e recuperar elementos arquitetônicos das fachadas.",
    "publicoAlvo": "Comunidade acadêmica, escolas públicas e público geral.",
    "metasEtapasFases": "Planejamento, licitação, execução do restauro, ações educativas, divulgação e prestação de contas.",
    "entregaveis": "Fachadas restauradas, visitas guiadas, palestra/seminário, vídeo institucional e relatório final.",
    "resultadoEsperado": "Patrimônio restaurado, valorização da memória da UFRGS e ampliação do acesso à educação patrimonial.",
    "duracaoPeriodo": "12",
    "ragContextSource": "external",
    "outputMode": "draft",
}

consulta_rag = brief_para_consulta_rag(brief_usuario)


# In[ ]:


brief_usuario = {
    "titulo": "Restauração das fachadas do Antigo Prédio da Faculdade de Medicina da UFRGS",
    "areasRelacionadas": ["Cultura", "Patrimônio Histórico", "Educação"],
    "areasRelacionadasOutro": "Intervenções em bens imóveis tombados/acautelados",
    "resumo": (
        "Projeto de restauração das fachadas sul e noroeste do Antigo Prédio da Faculdade "
        "de Medicina da UFRGS, em Porto Alegre, patrimônio histórico e cultural protegido "
        "nos âmbitos municipal, estadual e federal. A proposta busca recuperar elementos "
        "arquitetônicos ornamentais da edificação e ampliar o acesso público à memória "
        "histórica da universidade por meio de ações de educação patrimonial, visitas "
        "guiadas, palestra/seminário e produção audiovisual."
    ),
    "objetivos": (
        "Preservar um bem público de valor histórico, cultural e arquitetônico; restaurar "
        "as fachadas sul e noroeste do Antigo Prédio da Faculdade de Medicina da UFRGS; "
        "recuperar revestimentos, frisos, cornijas, elementos escultóricos, balaustradas "
        "e pintura; promover educação patrimonial; estimular o pertencimento social e "
        "fortalecer a valorização do patrimônio cultural edificado."
    ),
    "publicoAlvo": (
        "Comunidade acadêmica da UFRGS, estudantes de graduação, especialmente de "
        "Arquitetura e Urbanismo, professores e alunos de escolas públicas, pesquisadores, "
        "servidores, ex-alunos da Faculdade de Medicina e público geral interessado em "
        "patrimônio histórico e cultural."
    ),
    "metasEtapasFases": (
        "Pré-produção: elaboração e organização da documentação para licitação, alinhamento "
        "da equipe, produção de materiais gráficos, ações iniciais de comunicação e contato "
        "com possíveis palestrantes. Produção/execução: instalação do canteiro de obras, "
        "remoções e demolições necessárias, recuperação dos revestimentos, restauração de "
        "elementos ornamentais, pintura das fachadas, instalação de sistema de proteção "
        "para trabalho em altura, visitas técnicas, divulgação e realização de palestra/"
        "seminário. Pós-produção: divulgação da intervenção por banners informativos e "
        "elaboração do relatório de prestação de contas."
    ),
    "entregaveis": (
        "Fachadas sul e noroeste restauradas; visitas técnicas guiadas; atividades de "
        "educação patrimonial com escolas públicas; palestra ou seminário gratuito; "
        "materiais gráficos e de divulgação; vídeo de 3 a 7 minutos produzido pela UFRGS TV; "
        "banners informativos; relatório de prestação de contas."
    ),
    "resultadoEsperado": (
        "Recuperação material e simbólica de parte relevante do patrimônio histórico da "
        "UFRGS; ampliação do acesso público à história do prédio; fortalecimento da educação "
        "patrimonial; maior valorização da memória universitária e urbana de Porto Alegre; "
        "contribuição para a preservação de bens culturais brasileiros e para a cadeia "
        "produtiva da cultura local e regional."
    ),
    "duracaoPeriodo": "12",
    "ragContextSource": "external",
    "outputMode": "draft",
}

consulta_rag = brief_para_consulta_rag(brief_usuario)


# In[90]:


brief_usuario = {
    "titulo": "Financiamento Adicional para o Projeto de Paz e Desenvolvimento",
    "areasRelacionadas": [
        "Educacao",
        "Agricultura",
        "Economia"
    ],
    "areasRelacionadasOutro": "Construção da paz, reintegração social e apoio a populações deslocadas",
    "resumo": "Financiamento adicional para consolidar o Projeto de Paz e Desenvolvimento na Colômbia, expandindo ações para Valle del Cauca e fortalecendo iniciativas locais de desenvolvimento e paz.",
    "objetivos": "Apoiar populações vulneráveis, de baixa renda e deslocadas em comunidades rurais e urbanas afetadas por conflito, reduzindo sua exposição à violência e promovendo reintegração social e econômica sustentável.",
    "publicoAlvo": "Populações vulneráveis, famílias de baixa renda, pessoas deslocadas pela violência, comunidades rurais e urbanas afetadas por conflito, organizações parceiras, unidades territoriais e comunidades indígenas.",
    "metasEtapasFases": "Expansão para Valle del Cauca, consolidação de subprojetos regionais, fortalecimento institucional de organizações parceiras e unidades territoriais, coordenação, avaliação, supervisão e estudos do projeto.",
    "entregaveis": "Subprojetos territoriais, apoio social, econômico, ambiental e comunitário, fortalecimento institucional, planos de desenvolvimento indígena, estudos, monitoramento e planos de mitigação ambiental.",
    "resultadoEsperado": "Consolidação da estratégia de construção da paz, melhoria da qualidade de vida de comunidades vulneráveis, reintegração de famílias deslocadas e fortalecimento da capacidade local de planejar, implementar e monitorar iniciativas de desenvolvimento e paz.",
    "duracaoPeriodo": "",
    "ragContextSource": "external",
    "outputMode": "draft",
}


# ##### **Validar Embedding**

# In[12]:


consulta_rag = brief_para_consulta_rag(brief_usuario)

vetor_query = modelo_baai_embeddings.embed_query(consulta_rag)

print("---------------------------------")
print(" ---   VERIFICAR EMBEDDING    ---")
print("---------------------------------")
print(type(vetor_query))
print(len(vetor_query))
print(vetor_query[:5])
print("---------------------------------")


# ##### **Verificar colunas e tipos das tabelas do banco de dados Aurora AWS**

# In[13]:


# Verificar colunas das tabelas e tipos

with conn.cursor() as cur:
    cur.execute("""
        SELECT 
            table_schema,
            table_name,
            column_name,
            data_type,
            udt_name,
            ordinal_position
        FROM information_schema.columns
        WHERE table_schema = 'rag'
          AND table_name IN (
              'arquivos_documentos_rag',
              'chunks',
              'chunks_embeddings',
              'projetos_referencia_rag'
          )
        ORDER BY table_name, ordinal_position;
    """)

    colunas = cur.fetchall()

for row in colunas:
    print(row)


# In[14]:


def buscar_chunks_similares(
    consulta: str,
    top_k: int = 12,
    dimensions: int = 1024,
    rag_context_source: str = "both",
):
    vetor = modelo_baai_embeddings.embed_query(consulta)

    if len(vetor) != dimensions:
        raise ValueError(
            f"Dimensão inválida do vetor da query: {len(vetor)}. "
            f"Esperado: {dimensions}."
        )

    filtros = [
        "ce.chunk_embedding IS NOT NULL",
        "ce.dimensions = %s",
    ]

    params_filtros = [dimensions]

    if rag_context_source == "internal":
        filtros.append("LOWER(TRIM(p.origin)) = LOWER(TRIM(%s))")
        params_filtros.append("Innovatis")

    elif rag_context_source == "external":
        filtros.append("LOWER(TRIM(p.origin)) <> LOWER(TRIM(%s))")
        params_filtros.append("Innovatis")

    elif rag_context_source == "both":
        pass

    else:
        raise ValueError(
            "rag_context_source inválido. Use: 'internal', 'external' ou 'both'."
        )

    where_clause = " AND ".join(filtros)

    sql = f"""
        SELECT
            c.id AS chunk_id,
            c.projetos_referencia_rag_id AS projeto_id,
            p.title_project AS projeto_titulo,
            p.area AS projeto_area,
            p.origin AS projeto_origem,
            p.status AS projeto_status,

            c.raw_text AS texto_chunk,
            c.page_start,
            c.page_end,
            c.chunk_index,
            c.token_count,
            c.char_count,
            c.source_origin,

            ce.model_embedding,
            ce.dimensions,

            1 - (ce.chunk_embedding <=> %s::vector) AS score_similaridade,
            ce.chunk_embedding <=> %s::vector AS distancia_cosseno

        FROM rag.chunks_embeddings ce

        JOIN rag.chunks c
            ON c.id = ce.chunk_id

        JOIN rag.projetos_referencia_rag p
            ON p.id = c.projetos_referencia_rag_id

        WHERE {where_clause}

        ORDER BY ce.chunk_embedding <=> %s::vector

        LIMIT %s;
    """

    params = [vetor, vetor] + params_filtros + [vetor, top_k]

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

    return [dict(zip(columns, row)) for row in rows]


# In[15]:

# Buscar chunks similares
resultados = buscar_chunks_similares(
    consulta=consulta_rag,
    top_k=6,
    dimensions=1024,
    rag_context_source=brief_usuario["ragContextSource"],
)

print(len(resultados))


# In[16]:


# ============================================================
# 10. Visualização textual dos chunks retornados
# ============================================================

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


# In[17]:


def montar_contexto_rag(resultados: List[dict]) -> str:
    blocos = []

    for i, r in enumerate(resultados, start=1):
        texto = (r.get("texto_chunk") or "").strip()

        score = r.get("score_similaridade")
        score_fmt = f"{score:.4f}" if isinstance(score, (int, float)) else "N/A"

        bloco = f"""
[FONTE {i}]
projeto_id: {r.get("projeto_id")}
chunk_id: {r.get("chunk_id")}
projeto_titulo: {r.get("projeto_titulo")}
area: {r.get("projeto_area")}
origem: {r.get("projeto_origem")}
paginas: {r.get("page_start")} - {r.get("page_end")}
chunk_index: {r.get("chunk_index")}
score_similaridade: {score_fmt}

trecho:
{texto}
""".strip()

        blocos.append(bloco)

    return "\n\n" + ("\n\n" + "-" * 100 + "\n\n").join(blocos)


# In[18]:


contexto_rag = montar_contexto_rag(resultados)
print(contexto_rag)


# SCHEMA CONTRATUAL (Pydantic)

# In[19]:


class ReferenciaUsada(BaseModel):
    projeto_id: str = Field(..., description="ID do projeto recuperado no RAG.")
    projeto_titulo: str = Field(..., description="Título do projeto recuperado.")
    origem: Optional[str] = Field(None, description="Origem da referência.")
    chunk_ids: List[str] = Field(
        ..., min_length=1, description="Chunks usados como referência."
    )
    paginas: List[str] = Field(
        default_factory=list, description="Páginas associadas aos chunks."
    )
    score_medio: float = Field(
        ..., ge=-1.0, le=1.0, description="Score médio de similaridade."
    )
    justificativa_uso: str = Field(
        ..., min_length=20, description="Justificativa do uso da referência."
    )


class ProjetoGerado(BaseModel):
    titulo: str = Field(..., min_length=5)
    area: List[str] = Field(..., min_length=1)
    resumo: str = Field(..., min_length=50)
    objetivos: List[str] = Field(..., min_length=1)
    publico_alvo: str = Field(..., min_length=10)
    metas_etapas_fases: List[str] = Field(..., min_length=1)
    entregaveis: List[str] = Field(..., min_length=1)
    resultado_esperado: str = Field(..., min_length=30)
    duracao_periodo: str = Field(..., min_length=1)
    projetos_referencia_usados: List[ReferenciaUsada] = Field(..., min_length=1)


def validar_referencias_contra_retrieval(
    projeto: ProjetoGerado,
    resultados: list[dict],
) -> None:
    chunks_recuperados = {str(r["chunk_id"]) for r in resultados}
    projetos_recuperados = {str(r["projeto_id"]) for r in resultados}

    for ref in projeto.projetos_referencia_usados:
        if str(ref.projeto_id) not in projetos_recuperados:
            raise ValueError(
                f"projeto_id inválido: {ref.projeto_id} não está nos resultados recuperados."
            )

        for chunk_id in ref.chunk_ids:
            if str(chunk_id) not in chunks_recuperados:
                raise ValueError(
                    f"chunk_id inválido: {chunk_id} não está nos resultados recuperados."
                )


def gerar_projeto_com_validacao(
    chain,
    consulta_rag: str,
    contexto_rag: str,
    modo_saida: str,
    format_instructions: str,
    resultados: list[dict],
) -> dict:
    """
    Fluxo: LLM -> parse JSON -> validação Pydantic -> validação contra retrieval.
    Retorna dict com status 'ok' ou 'failed_validation'.
    """
    try:
        projeto_gerado = chain.invoke({
            "briefing": consulta_rag,
            "contexto_rag": contexto_rag,
            "modo_saida": modo_saida,
            "format_instructions": format_instructions,
        })
        validar_referencias_contra_retrieval(projeto_gerado, resultados)
        return {
            "status": "ok",
            "projeto": projeto_gerado.model_dump(),
        }
    except (ValidationError, OutputParserException) as e:
        return {
            "status": "failed_validation",
            "erro": "Falha na validação do schema Pydantic.",
            "detalhes": str(e),
        }
    except ValueError as e:
        return {
            "status": "failed_validation",
            "erro": str(e),
        }
    except Exception as e:
        return {
            "status": "failed_validation",
            "erro": f"Erro inesperado na geração: {e}",
        }


# PROMPT

# In[20]:


parser = PydanticOutputParser(pydantic_object=ProjetoGerado)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
Você é um especialista em escrita de projetos institucionais.

Use o briefing do usuário e as fontes RAG recuperadas para gerar um documento estruturado.

Regras obrigatórias:
- A saída deve seguir exatamente o schema fornecido.
- Não inclua texto fora do JSON.
- Não invente projeto_id, chunk_id, score, páginas ou títulos de referência.
- Só use referências presentes em FONTES RAG.
- Use as fontes como referência, mas não copie literalmente.
- Caso uma informação não esteja no briefing nem nas fontes, não trate como fato.

{format_instructions}
"""
    ),
    (
        "human",
        """
BRIEFING DO USUÁRIO:
{briefing}

FONTES RAG:
{contexto_rag}

MODO DE SAÍDA:
{modo_saida}
"""
    )
])


# CHAIN

# In[21]:


chain = prompt | llm_groq | parser


# In[22]:


resultado_geracao = gerar_projeto_com_validacao(
    chain=chain,
    consulta_rag=consulta_rag,
    contexto_rag=contexto_rag,
    modo_saida=brief_usuario["outputMode"],
    format_instructions=parser.get_format_instructions(),
    resultados=resultados,
)

print(resultado_geracao["status"])
if resultado_geracao["status"] == "ok":
    gerar_projeto = resultado_geracao["projeto"]
    print(gerar_projeto)
else:
    print(resultado_geracao)


# #### **Puxar projetos que são referência**

# In[23]:


def baixar_documentos_referencia(
    conn,
    projeto_ids: list[str],
    pasta_destino: str = "referencias_projeto_doc",
):
    pasta = Path.cwd() / pasta_destino
    pasta.mkdir(parents=True, exist_ok=True)

    sql = """
        SELECT
            projetos_referencia_rag_id,
            s3_bucket,
            s3_key,
            filename
        FROM rag.arquivos_documentos_rag
        WHERE projetos_referencia_rag_id = ANY(%s)
    """

    with conn.cursor() as cur:
        cur.execute(sql, (projeto_ids,))
        arquivos = cur.fetchall()

    arquivos_baixados = []

    for projeto_id, bucket, key, filename in arquivos:

        caminho_local = (
            pasta /
            f"{projeto_id}_{filename}"
        )

        try:
            s3_client.download_file(
                Bucket=bucket,
                Key=key,
                Filename=str(caminho_local),
            )

            arquivos_baixados.append({
                "projeto_id": str(projeto_id),
                "filename": filename,
                "bucket": bucket,
                "key": key,
                "caminho_local": str(caminho_local),
                "status": "baixado",
            })

        except Exception as e:
            arquivos_baixados.append({
                "projeto_id": str(projeto_id),
                "filename": filename,
                "bucket": bucket,
                "key": key,
                "erro": str(e),
                "status": "erro",
            })

    return arquivos_baixados


# In[24]:


projeto_ids = list({
    r["projeto_id"]
    for r in resultados
})


# In[26]:


arquivos_baixados = baixar_documentos_referencia(
    conn=conn,
    projeto_ids=projeto_ids,
)

