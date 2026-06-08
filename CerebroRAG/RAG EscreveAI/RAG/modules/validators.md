# validators.py

Arquivo: `src/escreveai/validators.py`

## Objetivo

Validar a rastreabilidade da saída gerada: garantir que toda referência citada pela
LLM (`projeto_id` e `chunk_id`) realmente veio dos chunks recuperados no retrieval.

## Papel no pipeline RAG

Fluxo anterior: [[generation]]
Fluxo atual: [[validators]]
Fluxo seguinte: [[generation]] (retorna o controle)

## Responsabilidades

- Construir o mapa `projeto_id -> {chunk_ids}` a partir dos resultados.
- Verificar se cada `projeto_id` citado existe nos resultados.
- Verificar se cada `chunk_id` citado pertence ao `projeto_id` declarado.
- Lançar erro controlado (`ValueError`) quando uma referência não é rastreável.

## Principais funções/classes

- `validar_referencias_contra_retrieval(projeto: ProjetoGerado, resultados: list[dict]) -> None`
  - Monta `chunks_por_projeto` a partir de `resultados`.
  - Para cada `ReferenciaUsada` em `projeto.projetos_referencia_usados`:
    - `ValueError` se o `projeto_id` não estiver nos resultados;
    - `ValueError` se algum `chunk_id` não pertencer ao `projeto_id`.
  - Retorna `None` quando tudo é válido.

## Entradas

- `projeto` ([[schemas|ProjetoGerado]] gerado pela LLM).
- `resultados` (chunks de [[retrieval]]).

## Saídas

- Nenhuma (retorna `None`); a sinalização de erro é via exceção.

## Dependências internas

- [[schemas]] (`ProjetoGerado`, `ReferenciaUsada`).
- [[retrieval]] (origem dos `resultados`).
- Chamado por [[generation]].

## Dependências externas

- `typing` (stdlib).

## Regras importantes

- É a barreira anti-alucinação: impede a LLM de citar referências inexistentes.
- Compara IDs como string (`str(...)`) para evitar divergência de tipos.
- Não altera o `projeto`; apenas valida.

## Erros possíveis

- `ValueError: projeto_id inválido: ... não está nos resultados recuperados.`
- `ValueError: chunk_id inválido: ... não pertence ao projeto_id ...`

Ambos são capturados por [[generation]] e viram `failed_validation`.

## Exemplo de uso

```python
from escreveai.validators import validar_referencias_contra_retrieval

# levanta ValueError se a LLM citar referência fora do retrieval
validar_referencias_contra_retrieval(projeto_gerado, resultados)
```

## Links relacionados

- [[PipelineRAG]]
- [[schemas]]
- [[generation]]
- [[retrieval]]
