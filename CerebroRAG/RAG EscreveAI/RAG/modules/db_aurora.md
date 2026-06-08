# db_aurora.py

Arquivo: `src/escreveai/db_aurora.py`

## Objetivo

Centralizar a conexão com o Aurora PostgreSQL e registrar o suporte ao tipo
`vector` (pgvector), expondo um context manager para uso seguro.

## Papel no pipeline RAG

Fluxo anterior: [[briefing]]
Fluxo atual: [[db_aurora]]
Fluxo seguinte: [[retrieval]], [[reference_files]]

## Responsabilidades

- Abrir conexão PostgreSQL com `psycopg`.
- Registrar o tipo `vector` do pgvector na conexão.
- Expor `conexao_pg()` como context manager.
- Garantir o fechamento da conexão ao final do uso.

## Principais funções/classes

- `abrir_conexao_pg(database_url) -> psycopg.Connection`
  - Abre conexão com `autocommit=False` e keepalives configurados.
  - Chama `register_vector(conn)` para habilitar o tipo vetorial.
  - Retorna a conexão pronta para uso.
- `conexao_pg(database_url) -> Iterator[Connection]`
  - Context manager (`@contextmanager`) que abre a conexão e a fecha no `finally`.

## Entradas

- `database_url` (string de conexão, vinda de [[config]]).

## Saídas

- Objeto `psycopg.Connection` (via `abrir_conexao_pg`) ou cedido no `with`
  (via `conexao_pg`).

## Dependências internas

- Recebe `database_url` de [[config]] (passado pelo [[run_generation_test|runner]]).

## Dependências externas

- `psycopg`
- `pgvector` (`pgvector.psycopg.register_vector`)

## Regras importantes

- Não cria conexão automaticamente no import.
- Deve ser usado preferencialmente via `with conexao_pg(...) as conn:`.
- `autocommit=False`: operações de escrita exigiriam commit explícito (o fluxo
  atual é de leitura).

## Erros possíveis

- Falha de conexão com Aurora (host/credenciais/rede inválidos).
- Extensão pgvector ausente no banco ao registrar o tipo `vector`.
- Timeout de conexão.

## Exemplo de uso

```python
from escreveai.db_aurora import conexao_pg

with conexao_pg(settings.database_url) as conn:
    # conn já tem o tipo vector registrado
    resultados = buscar_chunks_similares(conn=conn, ...)
```

## Links relacionados

- [[PipelineRAG]]
- [[retrieval]]
- [[reference_files]]
- [[config]]
