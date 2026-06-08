# embeddings.py

Arquivo: `src/escreveai/embeddings.py`

## Objetivo

Integrar o modelo de embeddings BGE-M3 ao pipeline, gerando vetores densos para a
consulta do retrieval. Implementa a interface `Embeddings` do LangChain.

## Papel no pipeline RAG

Fluxo anterior: [[config]]
Fluxo atual: [[embeddings]]
Fluxo seguinte: [[retrieval]]

## Responsabilidades

- Definir a classe `BGE_M3_Embeddings` (subclasse de `Embeddings`).
- Implementar `embed_query` (vetor de um texto).
- Implementar `embed_documents` (vetores de vários textos).
- Carregar o modelo `BGEM3FlagModel` apenas quando instanciado.

## Principais funções/classes

- `BGE_M3_Embeddings`
  - `__init__(model_name="BAAI/bge-m3", use_fp16=True, batch_size=12, max_length=8192)`:
    carrega o `BGEM3FlagModel` (operação pesada).
  - `embed_documents(texts) -> List[List[float]]`: retorna os `dense_vecs`.
  - `embed_query(text) -> List[float]`: retorna o vetor denso do texto.
- `criar_embeddings_bge_m3(...) -> BGE_M3_Embeddings`: fábrica que instancia a classe.

## Entradas

- Parâmetros de modelo de [[config]]: `model_name`, `use_fp16`, `batch_size`,
  `max_length`.
- Texto(s) a serem vetorizados.

## Saídas

- Vetores densos (`List[float]` / `List[List[float]]`). Dimensão esperada: 1024
  (validada em [[retrieval]] via `embedding_dimensions`).

## Dependências internas

- Parâmetros vêm de [[config]].
- Consumido por [[retrieval]].

## Dependências externas

- `FlagEmbedding` (`BGEM3FlagModel`)
- `langchain_core` (`Embeddings`)

## Regras importantes

- Não carrega o modelo no import; só ao chamar `criar_embeddings_bge_m3` / instanciar.
- O carregamento do modelo tem custo operacional alto (memória/tempo) — instanciar
  uma única vez no [[run_generation_test|runner]] e reutilizar.

## Erros possíveis

- Falha ao baixar/carregar o modelo (rede, espaço em disco, memória).
- Dimensão do vetor diferente da esperada (detectada em [[retrieval]]).
- Incompatibilidade de hardware com `use_fp16=True`.

## Exemplo de uso

```python
from escreveai.embeddings import criar_embeddings_bge_m3

embeddings = criar_embeddings_bge_m3(model_name="BAAI/bge-m3", use_fp16=True)
vetor = embeddings.embed_query("consulta de exemplo")  # len(vetor) == 1024
```

## Links relacionados

- [[PipelineRAG]]
- [[retrieval]]
- [[config]]
