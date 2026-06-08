# config.py

Arquivo: `src/escreveai/config.py`

## Objetivo

Centralizar a configuração do pipeline. Lê variáveis de ambiente e expõe um
objeto imutável `Settings` consumido pelo [[run_generation_test|runner]].

## Papel no pipeline RAG

Fluxo anterior: [[run_generation_test]]
Fluxo atual: [[config]]
Fluxo seguinte: [[embeddings]], [[llm]], [[db_aurora]], [[aws]], [[retrieval]]

## Responsabilidades

- Carregar variáveis de ambiente com `load_dotenv`.
- Definir o dataclass imutável `Settings`.
- Validar a presença das variáveis obrigatórias.
- Aplicar defaults e conversões de tipo (bool/int).

## Principais funções/classes

- `Settings` (`@dataclass(frozen=True)`): contrato de configuração. Campos:
  - obrigatórios: `groq_api_key`, `database_url`;
  - opcionais com default: `groq_generation_model` (`openai/gpt-oss-120b`),
    `aws_region` (`us-east-1`), `aws_profile` (`None`),
    `embedding_model_name` (`BAAI/bge-m3`), `embedding_use_fp16` (`True`),
    `embedding_batch_size` (`12`), `embedding_max_length` (`8192`),
    `embedding_dimensions` (`1024`), `retrieval_top_k` (`6`),
    `references_dir` (`referencias_projeto_doc`).
- `_get_bool(name)`: interpreta `1/true/yes/y/sim` como `True`.
- `_get_int(name)`: converte a env em `int`.
- `load_settings(env_path=None)`: carrega o `.env`, valida e retorna `Settings`.

## Entradas

- Caminho opcional para o `.env` (`env_path`).
- Variáveis de ambiente, principalmente:
  - `API_KEY_GROQ_ESCREVEAI_VICTOR` (obrigatória);
  - `DATABASE_URL` (obrigatória);
  - `GROQ_GENERATION_MODEL`, `AWS_REGION`, `AWS_PROFILE`,
    `EMBEDDING_MODEL_NAME`, `EMBEDDING_USE_FP16`, `EMBEDDING_BATCH_SIZE`,
    `EMBEDDING_MAX_LENGTH`, `EMBEDDING_DIMENSIONS`, `RAG_TOP_K`, `REFERENCES_DIR`.

## Saídas

- Instância de `Settings` (imutável).

## Dependências internas

- Nenhuma (módulo base).

## Dependências externas

- `python-dotenv`
- `dataclasses`, `os`, `pathlib`, `typing` (stdlib)

## Regras importantes

- Não abre conexões nem instancia clientes externos.
- Sem side effects no import (a leitura ocorre só em `load_settings`).
- `AWS_PROFILE` é opcional: se ausente, o boto3 usa credenciais/IAM Role do
  ambiente (ver [[aws]]).
- Valores booleanos vêm de strings; use os formatos aceitos por `_get_bool`.

## Erros possíveis

- `ValueError: Variaveis de ambiente ausentes: [...]` quando faltam as obrigatórias.
- `ValueError` de conversão em `_get_int` se a env não for numérica.
- Atenção: `_get_bool`/`_get_int` referenciam um nome `default` que não é parâmetro
  da função; se a variável correspondente não estiver definida no ambiente, a
  execução cai nesse caminho e pode levantar `NameError`. As envs esperadas devem
  estar presentes (este comportamento é do código atual e não deve ser alterado
  nesta tarefa de documentação).

## Exemplo de uso

```python
from escreveai.config import load_settings

settings = load_settings(".env")
print(settings.retrieval_top_k, settings.embedding_dimensions)
```

## Links relacionados

- [[PipelineRAG]]
- [[run_generation_test]]
- [[aws]]
- [[embeddings]]
