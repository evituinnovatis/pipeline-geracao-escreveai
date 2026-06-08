# generation.py

Arquivo: `src/escreveai/generation.py`

## Objetivo

Executar a geração do projeto: invocar a chain LangChain, validar a saída contra o
schema e contra o retrieval, retornando um resultado padronizado com `status`.

## Papel no pipeline RAG

Fluxo anterior: [[context_builder]] (+ [[llm]])
Fluxo atual: [[generation]] -> [[validators]]
Fluxo seguinte: [[aws]] / [[reference_files]]

## Responsabilidades

- Invocar a chain com `briefing`, `contexto_rag`, `modo_saida` e `format_instructions`.
- Receber o objeto já validado pelo parser Pydantic.
- Chamar [[validators]] para checar rastreabilidade das referências.
- Padronizar a saída com `status: "ok"` ou `status: "failed_validation"`.

## Principais funções/classes

- `gerar_projeto_com_validacao(chain, consulta_rag, contexto_rag, modo_saida, format_instructions, resultados) -> dict`
  - Fluxo: LLM -> parse JSON -> validação Pydantic -> validação contra retrieval.
  - Sucesso: `{"status": "ok", "projeto": <dict>}`.
  - `ValidationError`/`OutputParserException`: `failed_validation` com detalhes.
  - `ValueError` (referência inválida de [[validators]]): `failed_validation` com `erro`.
  - Qualquer outra exceção: `failed_validation` com mensagem genérica.

## Entradas

- `chain` ([[llm]]), `consulta_rag` ([[briefing]]), `contexto_rag` ([[context_builder]]).
- `modo_saida` (`draft`/`complete`), `format_instructions` (do parser).
- `resultados` (chunks de [[retrieval]], usados na validação).

## Saídas

- `dict` padronizado com `status` (`ok` | `failed_validation`), e `projeto` ou
  `erro`/`detalhes` (ver [[schemas|GenerationResult]]).

## Dependências internas

- [[llm]] (chain), [[validators]] (rastreabilidade), [[schemas]] (contratos),
  [[context_builder]] (contexto).

## Dependências externas

- `langchain_core` (`OutputParserException`)
- `pydantic` (`ValidationError`)

## Regras importantes

- Não conhece detalhes de banco, S3 ou embeddings — apenas coordena a geração.
- Nunca lança exceção para o chamador: encapsula falhas no `status`.
- Diferença entre `ok` (gerou e passou em todas as validações) e
  `failed_validation` (schema, parser ou referência inválida).

## Erros possíveis

- `failed_validation` por schema/parser (saída não-JSON ou incompleta).
- `failed_validation` por referência não rastreável (de [[validators]]).
- `failed_validation` por erro inesperado (ex.: falha de rede com a Groq).

## Exemplo de uso

```python
from escreveai.generation import gerar_projeto_com_validacao

resultado = gerar_projeto_com_validacao(
    chain=chain,
    consulta_rag=consulta_rag,
    contexto_rag=contexto_rag,
    modo_saida="draft",
    format_instructions=parser.get_format_instructions(),
    resultados=resultados,
)
if resultado["status"] == "ok":
    projeto = resultado["projeto"]
```

## Links relacionados

- [[PipelineRAG]]
- [[llm]]
- [[schemas]]
- [[validators]]
- [[context_builder]]
