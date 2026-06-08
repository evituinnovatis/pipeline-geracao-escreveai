# briefing.py

Arquivo: `src/escreveai/briefing.py`

## Objetivo

Transformar o briefing estruturado do usuário em uma consulta textual consolidada,
usada como entrada da busca semântica do retrieval.

## Papel no pipeline RAG

Fluxo anterior: [[run_generation_test]]
Fluxo atual: [[briefing]]
Fluxo seguinte: [[retrieval]]

## Responsabilidades

- Receber o dicionário de briefing.
- Concatenar título, áreas, resumo, objetivos, público-alvo, metas/etapas,
  entregáveis, resultado esperado e duração em texto.
- Anexar `areasRelacionadasOutro` quando "Outro" estiver entre as áreas.
- Remover do texto final os campos vazios.

## Principais funções/classes

- `brief_para_consulta_rag(brief: dict) -> str`
  - Monta as áreas a partir de `areasRelacionadas` (e do campo "Outro" se aplicável).
  - Monta linhas rotuladas (`Título do projeto: ...`, `Objetivos: ...`, etc.).
  - Retorna somente as linhas cujo valor após `:` não está vazio.

## Entradas

- `brief` (`dict`) — tipicamente o `BRIEF_USUARIO` do [[run_generation_test|runner]]
  (formato de [[schemas|BriefUsuario]]).

## Saídas

- `str` — consulta textual pronta para gerar embedding em [[retrieval]].

## Dependências internas

- Estrutura de entrada definida em [[schemas]] (`BriefUsuario`).
- Consumido por [[retrieval]] e [[generation]] (como `briefing`).

## Dependências externas

- `typing` (stdlib).

## Regras importantes

- Não gera embedding, não acessa banco e não chama LLM.
- Função pura: mesma entrada produz a mesma saída.

## Erros possíveis

- Praticamente nenhum: usa `brief.get(...)` com defaults, tolerando chaves ausentes.

## Exemplo de uso

```python
from escreveai.briefing import brief_para_consulta_rag

consulta = brief_para_consulta_rag(BRIEF_USUARIO)
# consulta é uma string com os campos preenchidos do briefing
```

## Links relacionados

- [[PipelineRAG]]
- [[schemas]]
- [[retrieval]]
