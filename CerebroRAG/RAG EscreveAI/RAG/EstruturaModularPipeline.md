# Estrutura Modular do Pipeline RAG

Este documento explica a ordem lógica de execução dos módulos criados a partir do `script_geracao_teste.py` e a responsabilidade de cada arquivo dentro da nova estrutura.

## Ordem Lógica do Fluxo

O ponto de entrada do fluxo modular é:

```text
scripts/run_generation_test.py
```

A ordem lógica de execução é:

```text
1. scripts/run_generation_test.py
   |
   v
2. src/escreveai/config.py
   |
   v
3. src/escreveai/embeddings.py
   |
   v
4. src/escreveai/llm.py
   |
   v
5. src/escreveai/briefing.py
   |
   v
6. src/escreveai/db_aurora.py
   |
   v
7. src/escreveai/retrieval.py
   |
   v
8. src/escreveai/context_builder.py
   |
   v
9. src/escreveai/generation.py
   |
   v
10. src/escreveai/validators.py
   |
   v
11. src/escreveai/aws.py
   |
   v
12. src/escreveai/reference_files.py
```

Em termos funcionais, o fluxo é:

```text
Carregar configurações
-> instanciar embeddings
-> instanciar LLM, parser, prompt e chain
-> transformar briefing em consulta RAG
-> abrir conexão com Aurora PostgreSQL
-> buscar chunks similares
-> montar contexto RAG
-> gerar projeto com validação
-> validar referências contra o retrieval
-> criar cliente S3
-> baixar documentos de referência
```

## Responsabilidade de Cada Arquivo

### `scripts/run_generation_test.py`

É o runner local do pipeline modular.

Responsabilidades:

- adicionar `src/` ao `sys.path` para permitir imports locais;
- definir o briefing de teste `BRIEF_USUARIO`;
- carregar configurações;
- instanciar embeddings, LLM, parser, prompt e chain;
- abrir conexão com Aurora;
- executar retrieval;
- montar contexto RAG;
- chamar a geração com validação;
- criar cliente S3;
- baixar documentos de referência;
- concentrar a execução ponta a ponta dentro de `main()`.

Esse arquivo é o único que deve executar o fluxo completo.

### `src/escreveai/config.py`

Centraliza as configurações do pipeline.

Responsabilidades:

- carregar variáveis de ambiente com `load_dotenv`;
- definir o dataclass `Settings`;
- ler chave da Groq;
- ler `DATABASE_URL`;
- configurar modelo de geração;
- configurar região e profile AWS;
- configurar modelo de embedding;
- configurar dimensão esperada do embedding;
- configurar `top_k`;
- configurar pasta de documentos de referência.

Esse módulo não abre conexões nem instancia clientes externos.

### `src/escreveai/db_aurora.py`

Centraliza a conexão com Aurora PostgreSQL.

Responsabilidades:

- abrir conexão PostgreSQL com `psycopg`;
- registrar suporte ao tipo `vector` do pgvector;
- expor `conexao_pg()` como context manager;
- garantir fechamento da conexão após o uso.

Esse módulo não cria conexão automaticamente no import.

### `src/escreveai/aws.py`

Centraliza a criação de sessão AWS e cliente S3.

Responsabilidades:

- criar sessão boto3;
- aceitar `profile_name` opcional;
- funcionar tanto com profile local quanto com credenciais/IAM Role do ambiente;
- criar cliente S3.

Esse módulo não faz download nem consulta S3 diretamente.

### `src/escreveai/embeddings.py`

Contém a integração com o modelo BGE-M3.

Responsabilidades:

- definir a classe `BGE_M3_Embeddings`;
- implementar `embed_documents`;
- implementar `embed_query`;
- expor `criar_embeddings_bge_m3()` para instanciar o modelo.

O carregamento do modelo acontece apenas quando a função de criação é chamada pelo runner.

### `src/escreveai/schemas.py`

Contém os contratos de dados do pipeline.

Responsabilidades:

- definir `BriefUsuario`;
- definir `RetrievedChunk`;
- definir `ReferenciaUsada`;
- definir `ProjetoGerado`;
- definir `GenerationResult`;
- concentrar o contrato Pydantic da resposta final.

Esse módulo é a base da validação contratual da geração.

### `src/escreveai/briefing.py`

Transforma o briefing estruturado em texto para busca semântica.

Responsabilidades:

- receber um dicionário de briefing;
- montar uma consulta textual consolidada;
- incluir título, áreas, resumo, objetivos, público-alvo, etapas, entregáveis, resultado esperado e duração;
- remover campos vazios da consulta final.

Esse módulo não gera embedding nem acessa banco.

### `src/escreveai/retrieval.py`

Executa a busca semântica no Aurora PostgreSQL com pgvector.

Responsabilidades:

- receber explicitamente `conn` e `embeddings`;
- gerar embedding da consulta;
- validar dimensão do vetor;
- aplicar filtro de origem `internal`, `external` ou `both`;
- executar SQL de similaridade com pgvector;
- retornar os chunks mais próximos com metadados de rastreabilidade.

Esse módulo não abre conexão e não instancia embedding.

### `src/escreveai/context_builder.py`

Monta o contexto textual usado no prompt da LLM.

Responsabilidades:

- receber os resultados do retrieval;
- formatar cada chunk como uma fonte rastreável;
- incluir `projeto_id`, `chunk_id`, título, área, origem, páginas, índice e score;
- concatenar os blocos em uma string única de contexto RAG.

Esse módulo não chama LLM nem altera os chunks recuperados.

### `src/escreveai/llm.py`

Centraliza a criação dos componentes LangChain.

Responsabilidades:

- criar `ChatGroq`;
- criar `PydanticOutputParser` com `ProjetoGerado`;
- criar o prompt de geração;
- criar a chain `prompt | llm | parser`.

Esse módulo não executa geração no import.

### `src/escreveai/generation.py`

Executa a geração do projeto com validação.

Responsabilidades:

- chamar a chain com briefing, contexto RAG, modo de saída e instruções de formato;
- receber o objeto validado pelo parser Pydantic;
- chamar a validação de referências contra o retrieval;
- retornar `status: ok` quando a geração passa nas validações;
- retornar `status: failed_validation` quando há erro de schema, parser ou referência inválida.

Esse módulo coordena a geração, mas não conhece detalhes de banco, S3 ou embedding.

### `src/escreveai/validators.py`

Valida a rastreabilidade da saída gerada.

Responsabilidades:

- verificar se cada `projeto_id` citado existe nos resultados recuperados;
- verificar se cada `chunk_id` citado existe nos resultados recuperados;
- verificar se cada `chunk_id` pertence ao `projeto_id` declarado;
- lançar erro controlado quando uma referência não é rastreável.

Esse módulo impede que a LLM cite referências que não vieram do retrieval.

### `src/escreveai/reference_files.py`

Baixa os documentos originais associados aos projetos de referência.

Responsabilidades:

- receber conexão com banco;
- receber `s3_client` explicitamente;
- consultar `rag.arquivos_documentos_rag`;
- baixar arquivos do S3;
- registrar status de sucesso ou erro por arquivo.

Esse módulo é uma etapa posterior ao RAG e não interfere na geração da resposta.

### `src/escreveai/__init__.py`

Marca `src/escreveai` como pacote Python.

Responsabilidades:

- permitir imports como `from escreveai.config import load_settings`;
- não executar lógica de pipeline.

## Separação de Responsabilidades

A modularização segue uma regra simples:

```text
Runner executa.
Módulos fornecem funções.
Dependências são passadas explicitamente.
Nada pesado acontece no import.
```

Isso mantém o pipeline mais fácil de testar, reutilizar e integrar futuramente em uma API, sem transformar o protótipo em uma arquitetura grande demais.

