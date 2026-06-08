# schemas.py

Arquivo: `src/escreveai/schemas.py`

## Objetivo

Definir os contratos de dados (Pydantic) do pipeline: entrada do usuário, chunks
recuperados, referências usadas e a saída gerada validada.

## Papel no pipeline RAG

Fluxo anterior: [[briefing]] / [[retrieval]]
Fluxo atual: [[schemas]]
Fluxo seguinte: [[generation]], [[validators]]

## Responsabilidades

- Definir `BriefUsuario` (entrada do briefing).
- Definir `RetrievedChunk` (chunk recuperado no retrieval).
- Definir `ReferenciaUsada` (referência citada pela LLM).
- Definir `ProjetoGerado` (saída estruturada principal).
- Definir `GenerationResult` (resultado padronizado da geração).

## Principais funções/classes

- `BriefUsuario`: campos do briefing; `ragContextSource` (`internal`/`external`/`both`,
  default `both`) e `outputMode` (`draft`/`complete`, default `draft`).
- `RetrievedChunk`: metadados de rastreabilidade (`chunk_id`, `projeto_id`,
  `projeto_titulo`, `score_similaridade`, `distancia_cosseno`, etc.).
- `ReferenciaUsada`: `projeto_id`, `projeto_titulo`, `chunk_ids` (mín. 1),
  `paginas`, `score_medio` (entre -1 e 1), `justificativa_uso` (mín. 20 chars).
- `ProjetoGerado`: saída principal com `titulo`, `area`, `resumo`, `objetivos`,
  `publico_alvo`, `metas_etapas_fases`, `entregaveis`, `resultado_esperado`,
  `duracao_periodo` e `projetos_referencia_usados` (lista de `ReferenciaUsada`,
  mín. 1) — com validações de tamanho mínimo por campo.
- `GenerationResult`: `status` (`ok`/`failed_validation`), `projeto`, `erro`,
  `detalhes`.

## Entradas

- N/A — módulo de definição de modelos (sem lógica executável).

## Saídas

- Classes Pydantic reutilizadas pelos demais módulos.

## Dependências internas

- Usado por [[llm]] (parser), [[generation]] e [[validators]].

## Dependências externas

- `pydantic` (`BaseModel`, `Field`)
- `typing`

## Regras importantes

- É a base da validação contratual da geração; os mínimos (`min_length`, faixas de
  score) reprovam saídas incompletas.
- Diferenciar os três contratos: entrada (`BriefUsuario`), recuperação
  (`RetrievedChunk`) e saída (`ProjetoGerado`/`GenerationResult`).
- Sem side effects no import.

## Erros possíveis

- `ValidationError` quando a saída da LLM não respeita os contratos
  (tratado em [[generation]]).

## Exemplo de uso

```python
from escreveai.schemas import ProjetoGerado
from langchain_core.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=ProjetoGerado)
```

## Links relacionados

- [[PipelineRAG]]
- [[briefing]]
- [[retrieval]]
- [[generation]]
- [[validators]]
