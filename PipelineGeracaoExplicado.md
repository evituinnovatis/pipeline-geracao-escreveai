# Pipeline RAG de Geração de Projetos - EscreveAI

## 1. Visão Geral

Este documento descreve o pipeline atual de geração de projetos institucionais usando RAG, LangChain, Groq, embeddings BGE-M3 e Aurora PostgreSQL com pgvector.

O pipeline ainda está em fase de protótipo, mas já cobre os elementos essenciais de um sistema RAG:

- entrada estruturada do usuário;
- geração de embedding da consulta;
- retrieval por similaridade semântica;
- montagem de contexto com rastreabilidade;
- geração com LLM;
- saída em JSON;
- recuperação opcional dos documentos originais usados como referência via S3.

O fluxo atual é:

```text
Formulário do usuário
        |
        v
Briefing estruturado
        |
        v
Texto consolidado para busca semântica
        |
        v
Embedding com BAAI/bge-m3
        |
        v
Busca vetorial no Aurora PostgreSQL com pgvector
        |
        v
Recuperação dos chunks mais similares
        |
        v
Montagem do contexto RAG rastreável
        |
        v
Prompt LangChain
        |
        v
ChatGroq
        |
        v
PydanticOutputParser + validação contratual
        |
        v
Resposta final em JSON
        |
        v
Download opcional dos documentos de referência no S3
```

O script atual também inicializa conexões externas antes da execução do RAG:

- carrega variáveis de ambiente com `load_dotenv()`;
- lê `API_KEY_GROQ_ESCREVEAI_VICTOR` e `DATABASE_URL`;
- abre conexão com Aurora PostgreSQL usando `psycopg`;
- registra o tipo `vector` com `register_vector(conn)`;
- cria uma sessão AWS com o profile `victor.eduardo` na região `us-east-1`;
- instancia clientes S3, STS e Groq.

O modelo de geração configurado no script é:

```python
GROQ_GENERATION_MODEL = "openai/gpt-oss-120b"
```

## 2. Objetivo do Sistema

O sistema tem como objetivo gerar projetos institucionais a partir de um briefing preenchido pelo usuário.

A resposta final deve conter, no mínimo:

- título;
- área;
- resumo;
- objetivos;
- público-alvo;
- metas, etapas e fases;
- entregáveis;
- resultado esperado;
- duração/período;
- projetos de referência usados.

O diferencial do sistema é que a geração não depende apenas do conhecimento geral da LLM. Ela utiliza uma base de projetos anteriores, armazenada no banco de dados, para recuperar referências semanticamente próximas ao briefing do usuário.

## 3. Entrada do Usuário na Plataforma

O usuário preenche um formulário na plataforma com campos estruturados.

Os principais campos são:

```ts
{
  titulo: string;
  areasRelacionadas: string[];
  areasRelacionadasOutro?: string;
  resumo: string;
  objetivos: string;
  publicoAlvo: string;
  metasEtapasFases: string;
  entregaveis: string;
  resultadoEsperado: string;
  duracaoPeriodo: string;
  ragContextSource: "internal" | "external" | "both";
  outputMode: "draft" | "complete";
}
```

Esses campos representam o briefing inicial do projeto.

Exemplo:

```python
brief_usuario = {
    "titulo": "Restauração das fachadas do Antigo Prédio da Faculdade de Medicina da UFRGS",
    "areasRelacionadas": ["Cultura", "Patrimônio Histórico", "Educação"],
    "areasRelacionadasOutro": "Intervenções em bens imóveis tombados/acautelados",
    "resumo": "Projeto de restauração das fachadas sul e noroeste do Antigo Prédio da Faculdade de Medicina da UFRGS...",
    "objetivos": "Preservar um bem público de valor histórico, cultural e arquitetônico...",
    "publicoAlvo": "Comunidade acadêmica da UFRGS, estudantes, professores, escolas públicas e público geral...",
    "metasEtapasFases": "Pré-produção, produção/execução e pós-produção...",
    "entregaveis": "Fachadas restauradas, visitas técnicas guiadas, atividades de educação patrimonial...",
    "resultadoEsperado": "Recuperação material e simbólica de parte relevante do patrimônio histórico da UFRGS...",
    "duracaoPeriodo": "12",
    "ragContextSource": "external",
    "outputMode": "draft",
}
```

No script atual existem vários exemplos de `brief_usuario`. Como o dicionário é sobrescrito ao longo do arquivo, o briefing efetivamente usado nas células seguintes é o último definido antes da etapa de embedding. Na versão atual do script, esse briefing final é:

```python
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
```

Portanto, na execução atual, o RAG consulta apenas projetos externos, isto é, projetos com `origin` diferente de `Innovatis`.

## 4. Papel de Cada Campo do Formulário

### titulo

Indica o tema central do projeto. É um campo importante para o retrieval porque geralmente concentra as entidades principais do projeto.

### areasRelacionadas

Ajuda a direcionar a busca semântica por domínio.

Exemplos:

- Cultura;
- Patrimônio Histórico;
- Educação;
- Tecnologia;
- Meio Ambiente;
- Saúde.

### areasRelacionadasOutro

Complementa a área quando o usuário seleciona "Outro".

No caso de patrimônio cultural, por exemplo:

```text
Intervenções em bens imóveis tombados/acautelados
```

### resumo

É uma descrição geral do projeto.

Esse campo costuma ser um dos mais relevantes para gerar o embedding da consulta, porque explica o problema, o objeto da intervenção e o contexto geral.

### objetivos

Define a intenção do projeto. É útil tanto para retrieval quanto para geração da resposta final.

### publicoAlvo

Informa quem será impactado. Pode influenciar a busca por projetos semelhantes voltados para públicos parecidos.

### metasEtapasFases

Descreve a estrutura operacional do projeto. Ajuda a LLM a gerar uma proposta com etapas coerentes.

### entregaveis

Indica produtos concretos do projeto. Ajuda a geração a manter uma estrutura prática e mensurável.

### resultadoEsperado

Ajuda a LLM a formular impacto, justificativa e resultado final.

### duracaoPeriodo

Indica a duração estimada do projeto. Atualmente é usado na geração da resposta, mas não tem peso especial no retrieval.

### ragContextSource

Controla a origem das referências usadas pelo RAG.

Valores possíveis:

```text
internal -> usar apenas projetos internos
external -> usar apenas projetos externos
both     -> usar internos e externos
```

A regra de negócio atual é:

```text
origin = 'Innovatis'  -> projeto interno
origin != 'Innovatis' -> projeto externo
```

### outputMode

Controla o nível de detalhamento da resposta final.

Valores possíveis:

```text
draft    -> esboço
complete -> projeto completo
```

Esse campo não deve impactar o embedding. Ele deve impactar o prompt da LLM.

## 5. Transformação do Briefing em Consulta RAG

O formulário do usuário é estruturado em campos, mas o modelo de embedding recebe texto.

Por isso, o pipeline transforma o briefing em uma consulta semântica única.

Função atual:

```python
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
```

Esse texto consolidado é chamado de `consulta_rag`.

Exemplo:

```text
Título do projeto: Restauração das fachadas do Antigo Prédio da Faculdade de Medicina da UFRGS
Áreas relacionadas: Cultura, Patrimônio Histórico, Educação
Resumo do projeto: Projeto de restauração das fachadas sul e noroeste...
Objetivos: Preservar um bem público de valor histórico...
Público-alvo: Comunidade acadêmica da UFRGS...
Metas, etapas e fases: Pré-produção, produção/execução e pós-produção...
Entregáveis: Fachadas restauradas, visitas técnicas guiadas...
Resultado esperado: Recuperação material e simbólica...
Duração/período: 12
```

## 6. Por Que Usar Uma Consulta Consolidada?

No estágio atual do MVP, a estratégia usada é:

```text
briefing completo -> um único embedding -> uma busca vetorial
```

Essa abordagem é simples, eficiente e suficiente para validar o pipeline.

Alternativas mais avançadas seriam:

- embedding separado por campo;
- multi-query retrieval;
- pesos diferentes por campo;
- reranking;
- busca híbrida lexical + vetorial;
- expansão de consulta;
- diversificação por projeto.

Essas estratégias podem ser adicionadas depois, mas aumentam a complexidade.

Para o protótipo, a consulta consolidada é uma boa escolha porque:

- preserva o contexto geral do projeto;
- reduz chamadas ao modelo de embedding;
- simplifica o SQL;
- facilita inspeção dos resultados;
- já permite avaliar a qualidade do RAG.

## 7. Modelo de Embedding Usado

O modelo de embedding usado é:

```text
BAAI/bge-m3
```

Classe atual:

```python
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
```

No pipeline atual, o método usado no retrieval é `embed_query()`.

Ele recebe a consulta consolidada e retorna um vetor numérico.

O vetor esperado tem 1024 dimensões.

Por isso o pipeline valida:

```python
if len(vetor) != dimensions:
    raise ValueError(...)
```

## 8. Estrutura da Base de Dados RAG

O banco usado é Aurora PostgreSQL com pgvector.

O schema relevante é:

```text
rag
```

As principais tabelas são:

- `rag.projetos_referencia_rag`;
- `rag.arquivos_documentos_rag`;
- `rag.chunks`;
- `rag.chunks_embeddings`;
- `rag.ingestion_jobs`.

## 9. Tabela rag.projetos_referencia_rag

Essa tabela armazena os metadados dos projetos de referência.

Campos relevantes:

- `id`;
- `title_project`;
- `area`;
- `origin`;
- `status`;
- `uploaded_at`;
- `processed_at`.

`id` é o identificador único do projeto.

`title_project` é o título do projeto de referência.

`area` representa a lista de áreas relacionadas ao projeto.

Exemplo:

```python
["Cultura", "Patrimônio Histórico", "Educação"]
```

`origin` indica a fonte de origem do projeto.

Regra atual:

```text
Innovatis        -> interno
diferente disso  -> externo
```

`status` pode ser usado futuramente para filtrar apenas projetos processados ou aprovados.

## 10. Tabela rag.arquivos_documentos_rag

Essa tabela representa os arquivos associados a projetos.

Campos relevantes:

- `id`;
- `projetos_referencia_rag_id`;
- `s3_bucket`;
- `s3_key`;
- `filename`;
- `mime_type`;
- `size_bytes`;
- `sha256`;
- `processing_status`;
- `criado_em`;
- `atualizado_em`;
- `criado_por`.

Essa tabela é importante para rastrear o arquivo original, especialmente quando os projetos vêm de PDFs armazenados em S3.

Ela permite responder perguntas como:

- de qual arquivo veio esse chunk?
- qual era o nome do PDF?
- onde ele está armazenado?
- qual era o status do processamento?

No retrieval principal, essa tabela ainda não entra na busca vetorial. Porém, no final do script atual, ela já é usada em uma etapa posterior para localizar e baixar os documentos originais dos projetos retornados pelo RAG.

## 11. Tabela rag.chunks

Essa tabela armazena os trechos textuais extraídos dos documentos.

Campos relevantes:

- `id`;
- `projetos_referencia_rag_id`;
- `raw_text`;
- `page_start`;
- `page_end`;
- `token_count`;
- `chunk_index`;
- `criado_em`;
- `criado_por`;
- `source_origin`;
- `char_count`.

`id` é o identificador único do chunk.

`projetos_referencia_rag_id` é a chave que liga o chunk ao projeto de referência.

`raw_text` é o texto bruto do chunk. Esse é o texto usado como contexto para a LLM.

`page_start` e `page_end` indicam as páginas do documento original onde o chunk aparece.

`chunk_index` é o índice sequencial do chunk dentro do documento/projeto.

`token_count` e `char_count` são informações úteis para controle de tamanho do contexto.

`source_origin` é um campo auxiliar de origem do chunk.

## 12. Tabela rag.chunks_embeddings

Essa tabela armazena os embeddings dos chunks.

Campos relevantes:

- `id`;
- `chunk_id`;
- `chunk_embedding`;
- `model_embedding`;
- `dimensions`;
- `criado_em`.

`chunk_id` liga o embedding ao chunk textual.

`chunk_embedding` é o vetor numérico usado na busca semântica. Esse campo é do tipo `vector`, via pgvector.

`model_embedding` é o nome do modelo usado na geração do embedding.

Exemplo:

```text
BAAI/bge-m3
```

No script atual, o nome do modelo não está sendo usado como filtro obrigatório.

`dimensions` indica o número de dimensões do embedding.

No pipeline atual:

```text
1024
```

Esse campo é usado como filtro para garantir que a consulta está comparando vetores compatíveis.

## 13. Relacionamento Entre as Tabelas

O relacionamento principal do RAG é:

```text
rag.chunks_embeddings.chunk_id
        |
        v
rag.chunks.id
        |
        v
rag.chunks.projetos_referencia_rag_id
        |
        v
rag.projetos_referencia_rag.id
```

Em termos práticos:

```text
embedding -> chunk textual -> projeto de origem
```

Isso permite que o retrieval retorne não apenas o texto mais parecido, mas também:

- projeto de origem;
- área;
- origem interna/externa;
- páginas;
- índice do chunk;
- score de similaridade;
- distância cosseno.

## 14. Função de Busca por Similaridade

A função principal de retrieval é:

```python
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
```

Na execução atual do script, a função é chamada assim:

```python
resultados = buscar_chunks_similares(
    consulta=consulta_rag,
    top_k=6,
    dimensions=1024,
    rag_context_source=brief_usuario["ragContextSource"],
)
```

Como o `brief_usuario` ativo usa `"ragContextSource": "external"`, essa chamada recupera até 6 chunks de projetos externos.

## 15. O Que Essa Função Faz na Prática

A função executa os seguintes passos:

1. Recebe a consulta textual consolidada.
2. Gera o embedding da consulta com BGE-M3.
3. Valida se o vetor tem 1024 dimensões.
4. Cria filtros SQL.
5. Aplica filtro de origem: `internal`, `external` ou `both`.
6. Executa busca vetorial no pgvector.
7. Ordena os chunks pela menor distância cosseno.
8. Retorna os `top_k` chunks mais similares.

Após a busca, o script também imprime uma visualização textual dos chunks retornados, incluindo:

- título do projeto;
- área;
- origem;
- `chunk_id`;
- `projeto_id`;
- `chunk_index`;
- páginas;
- `token_count`;
- `char_count`;
- modelo de embedding;
- dimensões;
- score de similaridade;
- distância cosseno;
- primeiros 300 caracteres do chunk.

Essa visualização é diagnóstica e ajuda a inspecionar a qualidade das fontes antes da chamada à LLM.

## 16. Similaridade Cosseno e Distância Cosseno

A busca usa o operador do pgvector:

```sql
<=>
```

Esse operador calcula a distância cosseno entre dois vetores:

```text
embedding da consulta
vs.
embedding do chunk
```

A ordenação é feita por:

```sql
ORDER BY ce.chunk_embedding <=> %s::vector
```

Isso significa:

```text
menor distância = mais similar
maior distância = menos similar
```

A função também calcula:

```sql
1 - (ce.chunk_embedding <=> %s::vector) AS score_similaridade
```

Logo:

```text
score_similaridade = 1 - distancia_cosseno
```

Exemplo:

```text
distância cosseno:   0.4215
score similaridade:  0.5785
```

Interpretação:

```text
distância menor -> melhor
score maior     -> melhor
```

## 17. Interpretação dos Scores

Uma regra prática inicial:

```text
score >= 0.70       -> referência forte
0.55 até 0.70       -> referência aproveitável
0.45 até 0.55       -> referência fraca/moderada
score < 0.45        -> provável ruído
```

Essa regra ainda precisa ser calibrada com dados reais.

No protótipo atual, scores ao redor de 0.50 indicam que a fonte recuperada pode ser útil como inspiração estrutural, mas provavelmente não é uma referência temática forte.

## 18. Filtro por Origem: Interno, Externo ou Ambos

O campo do formulário `ragContextSource` controla quais projetos podem ser usados como referência.

A regra aplicada no SQL é:

```python
if rag_context_source == "internal":
    filtros.append("LOWER(TRIM(p.origin)) = LOWER(TRIM(%s))")
    params_filtros.append("Innovatis")

elif rag_context_source == "external":
    filtros.append("LOWER(TRIM(p.origin)) <> LOWER(TRIM(%s))")
    params_filtros.append("Innovatis")

elif rag_context_source == "both":
    pass
```

Isso significa:

```text
internal -> apenas projetos com origin = Innovatis
external -> apenas projetos com origin diferente de Innovatis
both     -> todos os projetos
```

O uso de `LOWER(TRIM(...))` torna o filtro mais robusto contra diferenças simples como:

```text
Innovatis
innovatis
 Innovatis
Innovatis 
```

## 19. Por Que Validar Apenas a Dimensão?

No script atual, foi decidido remover o filtro por `model_embedding`.

Antes, a função podia filtrar:

```sql
ce.model_embedding = 'BAAI/bge-m3'
```

Agora ela filtra apenas:

```sql
ce.dimensions = 1024
```

A decisão simplifica o MVP.

Porém, há uma nuance importante: embeddings de modelos diferentes não necessariamente vivem no mesmo espaço vetorial.

Mesmo que dois modelos gerem vetores de 1024 dimensões, isso não garante que eles sejam comparáveis.

Para o cenário atual, essa simplificação é aceitável se houver garantia operacional de que todos os embeddings de 1024 dimensões na tabela foram gerados pelo mesmo modelo.

Se no futuro a tabela tiver embeddings de diferentes modelos com a mesma dimensão, será recomendável voltar a filtrar por `model_embedding`.

## 20. Montagem do Contexto RAG

Depois que os chunks são recuperados, eles são transformados em um contexto textual estruturado.

Função atual:

```python
def montar_contexto_rag(
    resultados: List[dict],
) -> str:
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
```

Diferente de versões anteriores da documentação, a função atual não aplica `max_chars_por_chunk` nem trunca o texto do chunk. Ela insere o `texto_chunk` completo no contexto e apenas formata o score com quatro casas decimais quando o valor é numérico. Pois não precisa colocar limite de token por chunk dado que já no Pipeline de ingestão a estratégia de chunk utilizada é uma limitação por token.

Esse contexto fica em um formato parecido com:

```text
[FONTE 1]
projeto_id: ...
chunk_id: ...
projeto_titulo: ...
area: ...
origem: ...
paginas: 6 - 6
chunk_index: 15
score_similaridade: 0.4957

trecho:
Texto recuperado do projeto...
```

## 21. Por Que o Contexto RAG Precisa Ser Rastreável?

A rastreabilidade é essencial porque a LLM pode gerar texto fluente, mas nem sempre é possível saber de onde ela tirou determinada informação.

Ao incluir metadados no contexto, o sistema permite:

- auditar quais fontes foram usadas;
- exibir projetos de referência na interface;
- verificar scores de aderência;
- identificar páginas e chunks;
- reduzir risco de alucinação;
- explicar por que uma resposta foi gerada daquela forma.

No projeto atual, cada fonte traz:

- `projeto_id`;
- `chunk_id`;
- `projeto_titulo`;
- `area`;
- `origem`;
- `páginas`;
- `chunk_index`;
- `score_similaridade`;
- `trecho`.

## 22. Prompt LangChain

A geração final usa LangChain.

Componentes principais:

```python
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field, ValidationError
```

Modelo atual:

```python
llm_groq = ChatGroq(
    model=GROQ_GENERATION_MODEL,
    temperature=0,
    api_key=API_GRQ_LLM,
)
```

O pipeline atual passou a usar validação contratual forte com Pydantic.

Os modelos definidos no script são:

```python
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
```

O parser é configurado assim:

```python
parser = PydanticOutputParser(pydantic_object=ProjetoGerado)
```

O prompt é construído com:

```python
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
```

## 23. Chain LangChain

A chain atual é:

```python
parser = PydanticOutputParser(pydantic_object=ProjetoGerado)

chain = prompt | llm_groq | parser
```

O script também adiciona uma validação posterior para garantir que as referências citadas pelo modelo realmente vieram do retrieval:

```python
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
```

A execução é encapsulada em uma função que retorna `ok` ou `failed_validation`:

```python
resultado_geracao = gerar_projeto_com_validacao(
    chain=chain,
    consulta_rag=consulta_rag,
    contexto_rag=contexto_rag,
    modo_saida=brief_usuario["outputMode"],
    format_instructions=parser.get_format_instructions(),
    resultados=resultados,
)
```

O LangChain organiza o fluxo assim:

```text
prompt template
        |
        v
LLM Groq
        |
        v
parse estruturado com Pydantic
        |
        v
validação contratual do schema
        |
        v
validação contra resultados do retrieval
        |
        v
retorno ok | failed_validation
```

### Etapa Posterior: Download dos Documentos de Referência

Depois da geração, o script atual identifica os `projeto_id` presentes nos resultados do retrieval e busca os arquivos originais associados na tabela `rag.arquivos_documentos_rag`.

A função usada é:

```python
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
        caminho_local = pasta / f"{projeto_id}_{filename}"

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
```

Em seguida, o script monta a lista de projetos distintos retornados pelo RAG:

```python
projeto_ids = list({
    r["projeto_id"]
    for r in resultados
})
```

E baixa os documentos relacionados:

```python
arquivos_baixados = baixar_documentos_referencia(
    conn=conn,
    projeto_ids=projeto_ids,
)
```

Essa etapa não altera o prompt nem a geração do JSON. Ela serve para recuperar localmente os documentos originais que deram origem às referências usadas pelo RAG.

## 24. Resposta Final Esperada

A resposta final esperada não é mais apenas um JSON válido. Agora ela precisa obedecer ao schema contratual definido em `ProjetoGerado`.

Exemplo de estrutura esperada:

```json
{
  "titulo": "Restauração das fachadas da Faculdade de Medicina da UFRGS",
  "area": ["Cultura", "Patrimônio Histórico", "Educação"],
  "resumo": "Restauração das fachadas sul e noroeste do Antigo Prédio da Faculdade de Medicina da UFRGS...",
  "objetivos": [
    "Preservar o patrimônio histórico da UFRGS",
    "Recuperar elementos arquitetônicos das fachadas"
  ],
  "publico_alvo": "Comunidade acadêmica, escolas públicas e público geral",
  "metas_etapas_fases": [
    "Planejamento",
    "Licitação",
    "Execução do restauro",
    "Ações educativas",
    "Divulgação",
    "Prestação de contas"
  ],
  "entregaveis": [
    "Fachadas restauradas",
    "Visitas guiadas",
    "Palestra/seminário",
    "Vídeo institucional",
    "Relatório final"
  ],
  "resultado_esperado": "Patrimônio restaurado, valorização da memória da UFRGS e ampliação do acesso à educação patrimonial",
  "duracao_periodo": "12",
  "projetos_referencia_usados": [
    {
      "projeto_id": "...",
      "projeto_titulo": "...",
      "origem": "...",
      "chunk_ids": ["..."],
      "paginas": ["8 - 8"],
      "score_medio": 0.5046,
      "justificativa_uso": "A referência foi usada porque apresenta estrutura de execução e entregáveis compatíveis com o briefing."
    }
  ]
}
```

Exemplo de saída que agora deve ser rejeitada:

```json
{
  "projetos_referencia_usados": [
    "Projeto de Paz e Desenvolvimento"
  ]
}
```

Esse JSON pode até ser sintaticamente válido, mas falha contratualmente porque não traz campos obrigatórios, não respeita os tipos esperados e não oferece rastreabilidade verificável.

## 25. Retrieval Funcionando Não Significa Contexto Perfeito

O retrieval atual retorna os chunks com menor distância cosseno.

Isso significa que ele responde à pergunta:

```text
Quais chunks estão semanticamente mais próximos da consulta?
```

Mas isso não garante automaticamente que os chunks sejam os melhores para gerar um projeto completo.

Possíveis problemas:

- `top_k` pequeno demais;
- muitos chunks do mesmo projeto;
- chunks semanticamente próximos, mas pouco úteis;
- scores baixos;
- falta de diversidade temática;
- chunks que ajudam na estrutura, mas não no conteúdo;
- fontes recuperadas com aderência parcial.

Por isso, é importante avaliar os resultados antes da geração.

## 26. Diagnóstico de Qualidade do Retrieval

Recomenda-se adicionar uma etapa de diagnóstico antes da chamada à LLM:

```python
if not resultados:
    raise ValueError("Nenhum chunk recuperado pelo RAG.")

melhor_score = resultados[0]["score_similaridade"]
score_medio = sum(r["score_similaridade"] for r in resultados) / len(resultados)

print(f"Melhor score: {melhor_score:.4f}")
print(f"Score médio: {score_medio:.4f}")

if melhor_score < 0.55:
    print(
        "Atenção: o melhor score está baixo. "
        "As fontes podem ser apenas parcialmente aderentes ao briefing."
    )
```

Esse diagnóstico ajuda a evitar confiança excessiva no RAG quando o contexto recuperado é fraco.

## 27. Nuance Sobre top_k

No script atual, a função `buscar_chunks_similares()` tem o seguinte padrão:

```python
top_k: int = 12
```

Porém, a chamada efetiva no fluxo de teste usa:

```python
top_k=6
```

Isso significa que o script está configurado para recuperar até 6 chunks na execução atual, embora a função permita usar 12 como padrão quando `top_k` não é informado.

Para geração real de projetos, 6 chunks pode funcionar como teste controlado, mas pode ser pouco dependendo da complexidade do briefing. Uma faixa inicial razoável continua sendo de 8 a 12 chunks.

Motivo:

- projetos têm várias seções;
- um único chunk pode conter apenas uma parte da estrutura;
- a LLM precisa de exemplos de objetivos, metas, entregáveis e justificativa;
- mais chunks aumentam a chance de recuperar contexto útil.

Porém, `top_k` alto demais pode causar:

- contexto muito longo;
- mais ruído;
- mais custo;
- maior chance de a LLM se confundir.

Uma estratégia melhor para o futuro:

```text
buscar top_k=30
-> filtrar por score
-> limitar chunks por projeto
-> diversificar fontes
-> montar contexto final com 8 a 12 chunks
```

## 28. Nuance Sobre Projetos Internos e Externos

O filtro `ragContextSource` afeta diretamente o universo de busca.

Exemplo:

```text
internal
```

Só consulta projetos com `origin = Innovatis`.

Isso pode ser desejável quando a plataforma quer usar apenas referências internas.

Mas também pode reduzir muito a qualidade do retrieval se não houver projetos internos próximos ao briefing.

Exemplo:

```text
Projeto sobre restauro patrimonial
```

Se a base interna não tiver muitos projetos patrimoniais, o sistema pode retornar projetos fracos, mesmo que a base externa tenha referências melhores.

Por isso, o modo `both` tende a melhorar recall, mas pode misturar estilos e fontes diferentes.

## 29. Nuance Sobre Score Baixo

Um score baixo não significa necessariamente que o chunk é inútil.

Ele pode ser útil de formas diferentes:

```text
score alto  -> referência temática forte
score médio -> referência estrutural ou parcial
score baixo -> possível ruído
```

Por exemplo, um chunk com score 0.50 pode não ser sobre restauração de fachada, mas pode conter uma boa estrutura de etapas, entregáveis ou prestação de contas.

Nesse caso, a LLM deve usar a fonte como inspiração estrutural, não como evidência temática.

## 30. Risco de Alucinação

Mesmo com RAG, a LLM pode alucinar.

Possíveis causas:

- contexto fraco;
- briefing ambíguo;
- prompt permissivo demais;
- ausência de validação forte;
- chunks recuperados pouco aderentes;
- LLM tentando preencher lacunas com conhecimento geral.

Medidas atuais:

- contexto com fontes rastreáveis;
- JSON estruturado com schema Pydantic;
- `temperature=0`;
- prompt instruindo a não inventar projetos de referência;
- validação cruzada de `projeto_id` e `chunk_ids` contra os resultados do retrieval;
- retorno controlado de falha com status `failed_validation`.

Medidas recomendadas:

- adicionar diagnóstico RAG;
- enriquecer a validação semântica das justificativas de uso;
- aplicar threshold mínimo;
- implementar reranking.

## 31. Melhorias Recomendadas no Prompt

O prompt atual já foi fortalecido para impor um contrato de saída.

As regras incorporadas hoje são:

```text
- A saída deve seguir exatamente o schema fornecido.
- Não inclua texto fora do JSON.
- Não invente projeto_id, chunk_id, score, páginas ou títulos de referência.
- Só use referências presentes em FONTES RAG.
- Use as fontes como referência, mas não copie literalmente.
- Caso uma informação não esteja no briefing nem nas fontes, não trate como fato.
```

Uma melhoria futura plausível seria adicionar regras mais explícitas sobre score, por exemplo:

```text
Quando score_similaridade < 0.55, use a fonte apenas como inspiração estrutural.
Não trate score baixo como evidência temática forte.
```

## 32. Validação Contratual com Pydantic

O pipeline usa:

```python
PydanticOutputParser(pydantic_object=ProjetoGerado)
```

Isso significa que a saída do modelo precisa ser parseável e também aderente ao schema definido em código.

Garantias atuais:

- campos obrigatórios precisam estar presentes;
- tipos precisam ser compatíveis com o schema;
- `projetos_referencia_usados` precisa ser uma lista de objetos estruturados;
- cada referência precisa trazer `projeto_id`, `projeto_titulo`, `chunk_ids`, `score_medio` e `justificativa_uso`;
- o objeto gerado pode ser validado antes de seguir no pipeline.

Além disso, o pipeline aplica uma segunda validação:

```python
validar_referencias_contra_retrieval(projeto_gerado, resultados)
```

Essa etapa garante que:

- nenhum `projeto_id` seja aceito se não estiver nos resultados recuperados;
- nenhum `chunk_id` seja aceito se não estiver nos chunks retornados pelo retrieval.

## 33. Limitações Atuais do Pipeline

O pipeline atual ainda não implementa:

- reranking;
- busca híbrida lexical + vetorial;
- diversificação por projeto;
- limite máximo de chunks por projeto;
- threshold mínimo de score;
- avaliação automática de groundedness;
- cache de embeddings da consulta;
- logging estruturado;
- observabilidade em produção;
- versionamento de prompts;
- métricas de custo e latência.

Essas limitações são aceitáveis para protótipo, mas precisam ser tratadas antes de produção.

## 34. Próximas Melhorias Recomendadas

### 1. Aumentar top_k

Usar inicialmente:

```python
top_k = 10
```

### 2. Adicionar diagnóstico de score

Registrar:

- melhor score;
- score médio;
- quantidade de fontes;
- origens retornadas;
- projetos distintos.

### 3. Diversificar por projeto

Evitar que todos os chunks venham do mesmo projeto.

Estratégia:

```text
buscar top_k=30
-> agrupar por projeto_id
-> limitar 2 ou 3 chunks por projeto
-> selecionar os melhores
```

### 4. Adicionar chunk_id na resposta final

Esse ponto já foi parcialmente resolvido com `chunk_ids` por referência. Uma evolução futura seria mapear com mais precisão quais trechos sustentaram cada parte da resposta.

### 5. Usar PydanticOutputParser

Esse ponto já foi implementado no script atual.

### 6. Criar avaliação offline

Montar um pequeno conjunto de briefs de teste e avaliar:

- relevância dos chunks;
- qualidade da resposta;
- fidelidade às fontes;
- aderência ao briefing;
- completude do JSON;
- latência;
- custo.

## 35. Resumo Final do Pipeline Atual

O pipeline atual pode ser resumido assim:

1. O script carrega variáveis de ambiente com `load_dotenv()`.
2. Abre conexão com Aurora PostgreSQL e registra suporte a pgvector.
3. Cria sessão AWS e clientes S3/STS.
4. Instancia o cliente Groq, o modelo BGE-M3 e o `ChatGroq`.
5. O usuário é representado por um dicionário `brief_usuario`.
6. `brief_para_consulta_rag()` transforma o briefing em texto.
7. BGE-M3 gera embedding da consulta.
8. `buscar_chunks_similares()` consulta Aurora PostgreSQL com pgvector.
9. O banco retorna os chunks com menor distância cosseno, respeitando `ragContextSource`.
10. O script imprime uma visualização diagnóstica dos chunks retornados.
11. `montar_contexto_rag()` transforma os chunks em contexto rastreável.
12. LangChain monta o prompt com briefing, contexto, modo de saída e `format_instructions`.
13. ChatGroq gera a resposta.
14. `PydanticOutputParser` converte a resposta em objeto estruturado.
15. O pipeline valida se `projeto_id` e `chunk_ids` realmente vieram do retrieval.
16. O sistema retorna `ok` ou `failed_validation`.
17. Se a validação for bem-sucedida, o projeto gerado é aceito.
18. O script coleta os `projeto_id` retornados e baixa os documentos originais via S3.

## 36. Conclusão

O pipeline atual já implementa o núcleo de um sistema RAG funcional para geração de projetos.

A arquitetura está correta para um MVP:

```text
briefing estruturado
-> embedding único
-> busca vetorial
-> contexto rastreável
-> geração com LangChain
-> JSON contratual com Pydantic
-> validação contra retrieval
-> download opcional das fontes originais
```

As principais nuances do projeto estão em:

- transformar corretamente os inputs do formulário em uma consulta semântica;
- garantir que os embeddings tenham a mesma dimensão;
- usar o filtro de origem `internal`/`external`/`both` corretamente;
- interpretar scores de similaridade com cuidado;
- evitar que a LLM trate fontes fracas como referências fortes;
- preservar rastreabilidade por projeto, chunk, página e score;
- manter o contrato de saída alinhado ao backend e às validações de rastreabilidade.

A próxima etapa recomendada é transformar esse protótipo em uma função de serviço:

```python
def gerar_projeto_por_brief(brief_usuario: dict) -> dict:
    consulta_rag = brief_para_consulta_rag(brief_usuario)
    resultados = buscar_chunks_similares(
        consulta=consulta_rag,
        top_k=10,
        dimensions=1024,
        rag_context_source=brief_usuario["ragContextSource"],
    )
    contexto_rag = montar_contexto_rag(resultados)
    resultado_geracao = gerar_projeto_com_validacao(
        chain=chain,
        consulta_rag=consulta_rag,
        contexto_rag=contexto_rag,
        modo_saida=brief_usuario["outputMode"],
        format_instructions=parser.get_format_instructions(),
        resultados=resultados,
    )
    return resultado_geracao
```

Essa função será a base para expor o pipeline em uma API futura.