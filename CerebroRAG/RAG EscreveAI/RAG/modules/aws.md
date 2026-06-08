# aws.py

Arquivo: `src/escreveai/aws.py`

## Objetivo

Centralizar a criação de sessão AWS (boto3) e do cliente S3 usado para baixar os
documentos de referência.

## Papel no pipeline RAG

Fluxo anterior: [[generation]]
Fluxo atual: [[aws]]
Fluxo seguinte: [[reference_files]]

## Responsabilidades

- Criar uma sessão boto3 (`Session`).
- Aceitar `profile_name` opcional para uso local.
- Funcionar com credenciais/IAM Role do ambiente quando não há profile.
- Criar e retornar o cliente S3.

## Principais funções/classes

- `criar_sessao_aws(region_name, profile_name=None) -> Session`
  - Se `profile_name` for informado, cria a sessão com esse profile.
  - Caso contrário, cria a sessão apenas com `region_name`.
- `criar_s3_client(region_name, profile_name=None) -> BaseClient`
  - Cria a sessão e retorna `session.client("s3")`.

## Entradas

- `region_name` (ex.: `us-east-1`, de [[config]]).
- `profile_name` opcional (`AWS_PROFILE`, de [[config]]).

## Saídas

- `Session` do boto3 ou cliente S3 (`BaseClient`).

## Dependências internas

- Recebe `region_name`/`profile_name` de [[config]].

## Dependências externas

- `boto3`
- `botocore`

## Regras importantes

- Não faz download nem consulta o S3 (isso é responsabilidade de [[reference_files]]).
- Sem side effects no import.
- Em produção (IAM Role), `profile_name` deve ser `None`.

## Erros possíveis

- `ProfileNotFound` quando o profile local não existe.
- `NoCredentialsError` quando não há credenciais disponíveis no ambiente.
- Região inválida.

## Exemplo de uso

```python
from escreveai.aws import criar_s3_client

s3_client = criar_s3_client(
    region_name=settings.aws_region,
    profile_name=settings.aws_profile,
)
```

## Links relacionados

- [[PipelineRAG]]
- [[reference_files]]
- [[config]]
