# CLAUDE.md

## Objetivo desta tarefa

Criar uma documentação técnica modular em Markdown para o pipeline RAG do projeto EscreveAI/EasyPlanner.

O objetivo é construir uma "memória técnica" do pipeline, compatível com Obsidian, para que desenvolvedores e agentes de IA consigam entender rapidamente:

* como o pipeline funciona;
* qual é a responsabilidade de cada módulo;
* quais módulos se conectam entre si;
* quais são as entradas e saídas de cada parte;
* quais cuidados operacionais devem ser mantidos;
* quais erros são esperados em cada etapa.

Esta tarefa é exclusivamente de documentação e organização do conhecimento. Não alterar o comportamento funcional do pipeline.

---

## Regra principal

Não modificar a lógica dos scripts Python, exceto se for estritamente necessário para corrigir links, nomes ou referências de documentação.

Não apagar, sobrescrever ou deletar o script original `script_geracao_teste.py`.

Não fazer refatoração adicional nesta tarefa.

Não melhorar prompt, resposta da LLM, estratégia de retrieval, schema de saída ou lógica de geração nesta etapa.

O foco é criar documentação Markdown conectada ao código existente.

---

## Contexto do projeto

O projeto possui um pipeline RAG modularizado a partir do antigo `script_geracao_teste.py`.

O fluxo principal é executado por:

```text
scripts/run_generation_test.py
```

A estrutura modular esperada é:

```text
src/
  escreveai/
    __init__.py
    config.py
    db_aurora.py
    aws.py
    embeddings.py
    schemas.py
    briefing.py
    retrieval.py
    context_builder.py
    llm.py
    generation.py
    validators.py
    reference_files.py

scripts/
  run_generation_test.py
```

O fluxo lógico é:

```text
run_generation_test.py
-> config.py
-> embeddings.py
-> llm.py
-> briefing.py
-> db_aurora.py
-> retrieval.py
-> context_builder.py
-> generation.py
   -> validators.py
-> aws.py
-> reference_files.py
```

Observação: `validators.py` é chamado pelo fluxo de geração, não precisa necessariamente ser chamado diretamente pelo runner.

---

## Estrutura de documentação esperada

Criar a documentação em uma pasta própria:

```text
docs/
  PipelineRAG.md
  modules/
    run_generation_test.md
    config.md
    db_aurora.md
    aws.md
    embeddings.md
    schemas.md
    briefing.md
    retrieval.md
    context_builder.md
    llm.md
    generation.md
    validators.md
    reference_files.md
```

Não colocar os arquivos Markdown dentro de `src/escreveai/`, salvo se já houver uma decisão explícita do projeto para isso.

A pasta `docs/` deve funcionar como base de conhecimento compatível com Obsidian.

---

## Padrão Obsidian

Usar links internos no formato:

```markdown
[[PipelineRAG]]
[[config]]
[[retrieval]]
[[generation]]
[[validators]]
```

Não usar links Markdown tradicionais para arquivos internos, exceto quando necessário.

Preferir links curtos com o nome lógico do módulo.

Exemplo:

```markdown
Fluxo anterior: [[briefing]]
Fluxo seguinte: [[context_builder]]
Depende de: [[schemas]], [[db_aurora]], [[embeddings]]
```

---

## Arquivo índice principal

Criar o arquivo:

```text
docs/PipelineRAG.md
```

Esse arquivo deve ser o mapa central do pipeline.

Ele deve conter:

1. visão geral do pipeline;
2. fluxo ponta a ponta;
3. lista de módulos com links Obsidian;
4. responsabilidades principais;
5. princípios de arquitetura;
6. cuidados operacionais;
7. o que não deve acontecer no import dos módulos;
8. como executar o runner local;
9. relação entre código e documentação.

Estrutura sugerida:

```markdown
# Pipeline RAG

## Objetivo

## Fluxo principal

## Mapa dos módulos

## Princípios da modularização

## Regras operacionais

## Execução local

## Links dos módulos
```

---

## Template obrigatório para cada módulo

Cada arquivo em `docs/modules/` deve seguir este padrão:

```markdown
# nome_do_modulo.py

## Objetivo

Explique de forma objetiva a responsabilidade principal do módulo.

## Papel no pipeline RAG

Explique onde este módulo entra no fluxo.

Exemplo:

Fluxo anterior: [[briefing]]
Fluxo atual: [[retrieval]]
Fluxo seguinte: [[context_builder]]

## Responsabilidades

Liste as responsabilidades do módulo em bullets.

## Principais funções/classes

Para cada função ou classe relevante, documentar:

- nome;
- o que faz;
- parâmetros principais;
- retorno esperado;
- observações importantes.

## Entradas

Liste os dados recebidos pelo módulo.

## Saídas

Liste os dados retornados pelo módulo.

## Dependências internas

Liste outros módulos do projeto usados por este módulo.

Exemplo:

- [[schemas]]
- [[validators]]
- [[config]]

## Dependências externas

Liste bibliotecas externas relevantes.

Exemplo:

- `psycopg`
- `boto3`
- `langchain`
- `FlagEmbedding`
- `pgvector`
- `pydantic`

## Regras importantes

Liste cuidados operacionais.

Exemplo:

- este módulo não deve abrir conexão automaticamente no import;
- este módulo não deve carregar modelo pesado no import;
- este módulo não deve chamar LLM no import;
- dependências externas devem ser recebidas explicitamente quando possível.

## Erros possíveis

Liste falhas esperadas.

Exemplo:

- variável de ambiente ausente;
- falha de conexão com Aurora;
- dimensão inválida do embedding;
- erro SQL;
- nenhum chunk recuperado;
- falha de validação Pydantic;
- referência citada que não veio do retrieval;
- erro de download S3.

## Exemplo de uso

Adicionar um exemplo curto e realista de uso do módulo.

Não copiar o arquivo Python inteiro.

## Links relacionados

Adicionar links Obsidian para módulos conectados.

Exemplo:

- [[PipelineRAG]]
- [[schemas]]
- [[retrieval]]
- [[generation]]
```

---

## Módulos a documentar

### `scripts/run_generation_test.py`

Documentar como runner local do pipeline.

Deve explicar que ele:

* adiciona `src/` ao path, se necessário;
* carrega settings;
* instancia dependências;
* define ou carrega briefing de teste;
* executa o fluxo ponta a ponta;
* deve ser o único arquivo responsável por executar o pipeline completo localmente.

Links relacionados:

* [[PipelineRAG]]
* [[config]]
* [[embeddings]]
* [[llm]]
* [[briefing]]
* [[db_aurora]]
* [[retrieval]]
* [[context_builder]]
* [[generation]]
* [[aws]]
* [[reference_files]]

---

### `src/escreveai/config.py`

Documentar configuração central.

Deve explicar:

* leitura de variáveis de ambiente;
* dataclass ou modelo `Settings`;
* variáveis obrigatórias;
* variáveis opcionais;
* defaults;
* cuidados com `AWS_PROFILE`;
* cuidados com valores booleanos;
* ausência de side effects no import.

Links relacionados:

* [[PipelineRAG]]
* [[run_generation_test]]

---

### `src/escreveai/db_aurora.py`

Documentar conexão com Aurora PostgreSQL.

Deve explicar:

* abertura de conexão com `psycopg`;
* registro do pgvector;
* uso como context manager;
* fechamento correto da conexão;
* ausência de conexão automática no import.

Links relacionados:

* [[PipelineRAG]]
* [[retrieval]]
* [[reference_files]]

---

### `src/escreveai/aws.py`

Documentar criação de sessão AWS e cliente S3.

Deve explicar:

* uso opcional de profile local;
* funcionamento com IAM Role;
* criação do cliente S3;
* ausência de download no módulo.

Links relacionados:

* [[PipelineRAG]]
* [[reference_files]]
* [[config]]

---

### `src/escreveai/embeddings.py`

Documentar modelo BGE-M3.

Deve explicar:

* classe de embeddings;
* `embed_query`;
* `embed_documents`;
* criação do modelo apenas quando solicitado;
* custo operacional de carregar modelo;
* dimensão esperada do vetor.

Links relacionados:

* [[PipelineRAG]]
* [[retrieval]]
* [[config]]

---

### `src/escreveai/schemas.py`

Documentar contratos Pydantic.

Deve explicar:

* `BriefUsuario`;
* `RetrievedChunk`;
* `ReferenciaUsada`;
* `ProjetoGerado`;
* `GenerationResult`;
* papel dos schemas na validação contratual;
* diferença entre dados de entrada, chunks recuperados e saída gerada.

Links relacionados:

* [[PipelineRAG]]
* [[briefing]]
* [[retrieval]]
* [[generation]]
* [[validators]]

---

### `src/escreveai/briefing.py`

Documentar transformação do briefing em consulta RAG.

Deve explicar:

* entrada;
* campos considerados;
* remoção de campos vazios;
* saída textual usada pelo retrieval;
* ausência de chamada a banco, embedding ou LLM.

Links relacionados:

* [[PipelineRAG]]
* [[schemas]]
* [[retrieval]]

---

### `src/escreveai/retrieval.py`

Documentar busca vetorial.

Deve explicar:

* recebimento explícito de conexão e embeddings;
* geração do embedding da consulta;
* validação da dimensão;
* filtro `internal`, `external` ou `both`;
* consulta ao pgvector;
* retorno de chunks com metadados de rastreabilidade.

Links relacionados:

* [[PipelineRAG]]
* [[db_aurora]]
* [[embeddings]]
* [[schemas]]
* [[context_builder]]

---

### `src/escreveai/context_builder.py`

Documentar montagem de contexto.

Deve explicar:

* recebimento dos chunks;
* formatação em fontes rastreáveis;
* metadados incluídos;
* saída como string de contexto RAG;
* ausência de chamada à LLM.

Links relacionados:

* [[PipelineRAG]]
* [[retrieval]]
* [[generation]]

---

### `src/escreveai/llm.py`

Documentar criação dos componentes LangChain.

Deve explicar:

* criação do `ChatGroq`;
* criação do parser Pydantic;
* criação do prompt;
* criação da chain;
* ausência de execução de geração no import.

Links relacionados:

* [[PipelineRAG]]
* [[schemas]]
* [[generation]]
* [[config]]

---

### `src/escreveai/generation.py`

Documentar geração com validação.

Deve explicar:

* chamada da chain;
* recebimento de briefing, contexto e format instructions;
* retorno padronizado com `status`;
* chamada a `validators.py`;
* diferença entre `ok` e `failed_validation`.

Links relacionados:

* [[PipelineRAG]]
* [[llm]]
* [[schemas]]
* [[validators]]
* [[context_builder]]

---

### `src/escreveai/validators.py`

Documentar validações de rastreabilidade.

Deve explicar:

* validação de `projeto_id`;
* validação de `chunk_id`;
* validação de relação `chunk_id -> projeto_id`;
* objetivo de impedir referências inventadas;
* erros esperados.

Links relacionados:

* [[PipelineRAG]]
* [[schemas]]
* [[generation]]
* [[retrieval]]

---

### `src/escreveai/reference_files.py`

Documentar download de documentos de referência.

Deve explicar:

* consulta à tabela de arquivos;
* recebimento de `conn` e `s3_client`;
* download de arquivos S3;
* status por arquivo;
* por que essa etapa é posterior à geração;
* cuidados com autorização e confidencialidade.

Links relacionados:

* [[PipelineRAG]]
* [[aws]]
* [[db_aurora]]
* [[generation]]

---

## Regras de qualidade da documentação

A documentação deve ser:

* objetiva;
* técnica;
* específica do projeto;
* curta o suficiente para ser útil;
* completa o suficiente para orientar outro desenvolvedor ou IA;
* conectada via links Obsidian;
* versionada junto com o código.

Evitar:

* documentação genérica;
* repetir o código inteiro no Markdown;
* textos longos demais;
* abstrações desnecessárias;
* alterar comportamento do código durante esta tarefa;
* fazer refatoração junto com documentação.

---

## Critérios de aceite

A tarefa será considerada concluída quando:

1. Existir `docs/PipelineRAG.md`.
2. Existir um `.md` para cada módulo Python relevante.
3. Todos os `.md` seguirem o template mínimo.
4. Os arquivos usarem links Obsidian `[[...]]`.
5. O fluxo completo estiver descrito no índice central.
6. As responsabilidades de cada módulo estiverem claras.
7. As entradas e saídas de cada módulo estiverem documentadas.
8. As dependências internas e externas estiverem listadas.
9. Os erros possíveis estiverem documentados.
10. O script original `script_geracao_teste.py` permanecer intacto.
11. Nenhuma lógica funcional do pipeline for alterada.
12. A documentação deixar claro que módulos não devem executar lógica pesada no import.
13. A documentação permitir que uma IA ou novo desenvolvedor entenda o pipeline sem precisar reler todo o código.

---

## Resultado esperado

Ao final, o projeto deve possuir uma documentação conectada em Markdown que funcione como uma memória técnica do pipeline RAG.

Essa documentação será usada posteriormente no Obsidian como um cérebro navegável do projeto.
