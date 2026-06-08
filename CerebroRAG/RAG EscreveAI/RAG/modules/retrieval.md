# retrieval.py

Arquivo: `src/escreveai/retrieval.py`

## Objetivo

Executar a busca semântica (vetorial) no Aurora PostgreSQL com pgvector,
retornando os chunks mais similares à consulta, com metadados de rastreabilidade.

## Papel no pipeline RAG

Fluxo anterior: [[briefing]] (+ [[embeddings]], [[db_aurora]])
Fluxo atual: [[retrieval]]
Fluxo seguinte: [[context_builder]]

## Responsabilidades

- Receber explicitamente `conn` e `embeddings`.
- Gerar o embedding da consulta.
- Validar a dimensão do vetor contra `dimensions`.
- Aplicar filtro de origem: `internal`, `external` ou `both`.
- Executar SQL de similaridade de cosseno com pgvector.
- Retornar os chunks com metadados (score, distância, páginas, etc.).

## Principais funções/classes

- `buscar_chunks_similares(conn, embeddings, consulta, top_k=12, dimensions=1024, rag_context_source="both") -> list[dict]`
  - `embeddings.embed_query(consulta)` gera o vetor.
  - Levanta `ValueError` se `len(vetor) != dimensions`.
  - Filtro por `p.origin`: `internal` => igual a `Innovatis`;
    `external` => diferente de `Innovatis`; `both` => sem filtro.
  - Ordena por `chunk_embedding <=> vetor` (distância de cosseno) e limita por `top_k`.
  - Calcula `score_similaridade = 1 - distancia_cosseno`.
  - Faz join entre `rag.chunks_embeddings`, `rag.chunks` e
    `rag.projetos_referencia_rag`.

## Entradas

- `conn` ([[db_aurora]]), `embeddings` ([[embeddings]]).
- `consulta` (texto de [[briefing]]).
- `top_k`, `dimensions`, `rag_context_source` (de [[config]]/briefing).

## Saídas

- `list[dict]` — cada dict é um chunk com `chunk_id`, `projeto_id`,
  `projeto_titulo`, `projeto_area`, `projeto_origem`, `texto_chunk`,
  `page_start`, `page_end`, `chunk_index`, `score_similaridade`,
  `distancia_cosseno`, entre outros.

## Dependências internas

- [[db_aurora]] (conexão), [[embeddings]] (vetor), [[schemas]] (`RetrievedChunk`).
- Consumido por [[context_builder]] e [[validators]].

## Dependências externas

- `psycopg` (`Connection`, cursor)
- `pgvector` (tipo `vector`, registrado em [[db_aurora]])
- `langchain_core` (`Embeddings`)

## Regras importantes

- Não abre conexão nem instancia embedding (recebe ambos prontos).
- A dimensão do vetor deve bater com `dimensions` (1024 por padrão).
- `rag_context_source` aceita apenas `internal`, `external` ou `both`.

## Erros possíveis

- `ValueError` por dimensão inválida do vetor.
- `ValueError` por `rag_context_source` inválido.
- Erro SQL (tabela/coluna ausente, pgvector não registrado).
- Nenhum chunk recuperado (lista vazia) — não é erro, mas impacta a geração.

## Exemplo de uso

```python
from escreveai.retrieval import buscar_chunks_similares

resultados = buscar_chunks_similares(
    conn=conn,
    embeddings=embeddings,
    consulta=consulta_rag,
    top_k=settings.retrieval_top_k,
    dimensions=settings.embedding_dimensions,
    rag_context_source="external",
)
```

## Links relacionados

- [[PipelineRAG]]
- [[db_aurora]]
- [[embeddings]]
- [[schemas]]
- [[context_builder]]
