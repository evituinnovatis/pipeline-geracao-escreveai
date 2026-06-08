# context_builder.py

Arquivo: `src/escreveai/context_builder.py`

## Objetivo

Montar o contexto textual rastreável (string única) a partir dos chunks
recuperados, para ser injetado no prompt da LLM.

## Papel no pipeline RAG

Fluxo anterior: [[retrieval]]
Fluxo atual: [[context_builder]]
Fluxo seguinte: [[generation]]

## Responsabilidades

- Receber a lista de resultados do retrieval.
- Formatar cada chunk como um bloco `[FONTE i]` rastreável.
- Incluir `projeto_id`, `chunk_id`, `projeto_titulo`, `area`, `origem`, páginas,
  `chunk_index`, `score_similaridade` e o trecho de texto.
- Concatenar os blocos com separadores em uma única string.

## Principais funções/classes

- `montar_contexto_rag(resultados: list[dict]) -> str`
  - Itera os resultados, formatando o score com 4 casas (ou `N/A`).
  - Gera blocos `[FONTE 1]`, `[FONTE 2]`, ... separados por uma linha de hífens.

## Entradas

- `resultados` (`list[dict]`) — saída de [[retrieval]].

## Saídas

- `str` — contexto RAG formatado, usado como `contexto_rag` em [[generation]].

## Dependências internas

- [[retrieval]] (entrada), [[generation]] (consumidor).

## Dependências externas

- `typing` (stdlib).

## Regras importantes

- Não chama LLM e não altera os chunks recuperados.
- Preserva os IDs (`projeto_id`, `chunk_id`) para garantir rastreabilidade — eles
  são checados depois por [[validators]].
- Função pura.

## Erros possíveis

- Praticamente nenhum: usa `.get(...)` com defaults; chunk sem texto vira string vazia.

## Exemplo de uso

```python
from escreveai.context_builder import montar_contexto_rag

contexto_rag = montar_contexto_rag(resultados)
# string com blocos [FONTE i] incluindo projeto_id e chunk_id
```

## Links relacionados

- [[PipelineRAG]]
- [[retrieval]]
- [[generation]]
