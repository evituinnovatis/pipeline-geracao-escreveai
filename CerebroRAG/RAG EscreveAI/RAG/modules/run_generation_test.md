# run_generation_test.py

Arquivo: `scripts/run_generation_test.py`

## Objetivo

Runner local do pipeline RAG. É o único arquivo responsável por executar o fluxo
completo ponta a ponta em ambiente local, orquestrando todos os módulos de
`src/escreveai/`.

## Papel no pipeline RAG

Fluxo anterior: — (ponto de entrada)
Fluxo atual: [[run_generation_test]]
Fluxo seguinte: [[config]] -> [[embeddings]] -> [[llm]] -> [[briefing]] -> [[db_aurora]] -> [[retrieval]] -> [[context_builder]] -> [[generation]] -> [[aws]] -> [[reference_files]]

## Responsabilidades

- Adicionar `src/` ao `sys.path` para permitir imports do pacote `escreveai`.
- Definir o briefing de teste `BRIEF_USUARIO` (dicionário).
- Carregar `Settings` a partir do `.env`.
- Instanciar embeddings, LLM, parser, prompt e chain.
- Converter o briefing em consulta RAG.
- Abrir conexão com Aurora via context manager.
- Executar retrieval, montar contexto e gerar o projeto com validação.
- Criar cliente S3 e baixar os documentos de referência.
- Imprimir resultados no console.

## Principais funções/classes

- `PROJECT_ROOT` / `SRC_DIR`: resolvem a raiz do projeto e inserem `src/` no `sys.path`.
- `BRIEF_USUARIO` (`dict`): briefing de teste com campos como `titulo`,
  `areasRelacionadas`, `resumo`, `ragContextSource` e `outputMode`.
- `imprimir_resultados(resultados)`: imprime metadados de cada chunk recuperado.
- `main()`: orquestra o fluxo completo dentro de um bloco `with conexao_pg(...)`.

## Entradas

- Variáveis de ambiente do `.env` (via [[config]]).
- `BRIEF_USUARIO` definido no próprio arquivo.

## Saídas

- Saída no console: número de chunks, metadados, contexto RAG, resultado da
  geração (`status`) e lista de arquivos baixados.

## Dependências internas

- [[config]]
- [[embeddings]]
- [[llm]]
- [[briefing]]
- [[db_aurora]]
- [[retrieval]]
- [[context_builder]]
- [[generation]]
- [[aws]]
- [[reference_files]]

## Dependências externas

- `pathlib`, `sys`, `typing` (stdlib)

## Regras importantes

- É o único ponto que executa o pipeline completo localmente.
- Não deve conter lógica de negócio dos módulos; apenas orquestra.
- A conexão é sempre usada via context manager `conexao_pg(...)`.

## Erros possíveis

- Variáveis de ambiente ausentes (erro lançado por [[config]]).
- Falha de conexão com Aurora ([[db_aurora]]).
- Nenhum chunk recuperado ([[retrieval]]).
- `failed_validation` na geração ([[generation]] / [[validators]]).
- Erro de download S3 ([[reference_files]]).

## Exemplo de uso

```bash
python scripts/run_generation_test.py
```

Para alterar o caso de teste, edite o dicionário `BRIEF_USUARIO` (ex.: trocar
`ragContextSource` entre `internal`, `external` e `both`).

## Links relacionados

- [[PipelineRAG]]
- [[config]]
- [[retrieval]]
- [[generation]]
- [[reference_files]]
