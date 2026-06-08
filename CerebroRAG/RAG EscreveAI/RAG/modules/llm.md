# llm.py

Arquivo: `src/escreveai/llm.py`

## Objetivo

Criar os componentes LangChain do pipeline: o modelo `ChatGroq`, o parser Pydantic,
o prompt de geração e a chain que os combina.

## Papel no pipeline RAG

Fluxo anterior: [[config]]
Fluxo atual: [[llm]]
Fluxo seguinte: [[generation]]

## Responsabilidades

- Criar o `ChatGroq` com modelo, temperatura e API key.
- Criar o `PydanticOutputParser` baseado em [[schemas|ProjetoGerado]].
- Criar o `ChatPromptTemplate` (system + human) com regras de não-invenção.
- Compor a chain `prompt | llm | parser`.

## Principais funções/classes

- `criar_llm_groq(api_key, model, temperature=0) -> ChatGroq`.
- `criar_parser_projeto() -> PydanticOutputParser` (sobre `ProjetoGerado`).
- `criar_prompt_geracao() -> ChatPromptTemplate`
  - System: regras obrigatórias (seguir o schema, não inventar `projeto_id`,
    `chunk_id`, score, páginas ou títulos; usar apenas fontes do RAG);
    inclui `{format_instructions}`.
  - Human: recebe `{briefing}`, `{contexto_rag}` e `{modo_saida}`.
- `criar_chain_geracao(llm, prompt, parser)` -> chain `prompt | llm | parser`.

## Entradas

- `api_key`, `model` (de [[config]]), `temperature`.

## Saídas

- `ChatGroq`, `PydanticOutputParser`, `ChatPromptTemplate` e a chain.

## Dependências internas

- [[schemas]] (`ProjetoGerado`).
- Consumido por [[generation]] e pelo [[run_generation_test|runner]].

## Dependências externas

- `langchain_groq` (`ChatGroq`)
- `langchain_core` (`PydanticOutputParser`, `ChatPromptTemplate`)

## Regras importantes

- Não executa a geração no import nem nas funções de criação (apenas monta os
  objetos); a invocação ocorre em [[generation]].
- A temperatura padrão é 0 (saída mais determinística).
- As variáveis do prompt (`briefing`, `contexto_rag`, `modo_saida`,
  `format_instructions`) devem ser fornecidas no `invoke`.

## Erros possíveis

- API key inválida / ausente (erro no momento do `invoke`, não na criação).
- Modelo inexistente na Groq.
- `KeyError` de variável de prompt faltante no `invoke` (ver [[generation]]).

## Exemplo de uso

```python
from escreveai.llm import (
    criar_llm_groq, criar_parser_projeto, criar_prompt_geracao, criar_chain_geracao,
)

llm = criar_llm_groq(api_key=settings.groq_api_key, model=settings.groq_generation_model)
parser = criar_parser_projeto()
prompt = criar_prompt_geracao()
chain = criar_chain_geracao(llm=llm, prompt=prompt, parser=parser)
```

## Links relacionados

- [[PipelineRAG]]
- [[schemas]]
- [[generation]]
- [[config]]
