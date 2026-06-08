# Pipeline RAG

Memória técnica do pipeline RAG de geração de projetos do EscreveAI/EasyPlanner.
Este é o mapa central: comece por aqui e navegue pelos módulos via links Obsidian.

## Objetivo

O pipeline recebe um briefing estruturado do usuário, recupera trechos (chunks) de
projetos de referência via busca vetorial no Aurora PostgreSQL (pgvector) e usa uma
LLM (Groq) para gerar um documento de projeto estruturado e validado, com
rastreabilidade obrigatória das referências usadas. Ao final, baixa do S3 os
documentos originais dos projetos citados.

A estrutura modular foi extraída do antigo `script_geracao_teste.py`, que permanece
intacto como referência histórica.

## Fluxo principal

```text
run_generation_test.py        (runner / orquestrador)
-> config.py                  carrega Settings (env)
-> embeddings.py              instancia modelo BGE-M3
-> llm.py                     cria ChatGroq + parser + prompt + chain
-> briefing.py                converte briefing em consulta textual
-> db_aurora.py               abre conexão PostgreSQL (context manager)
-> retrieval.py               busca vetorial (pgvector) -> chunks
-> context_builder.py         monta string de contexto RAG rastreável
-> generation.py              chama a chain e valida a saída
   -> validators.py           valida referências contra o retrieval
-> aws.py                     cria sessão/cliente S3
-> reference_files.py         baixa documentos de referência do S3
```

Em termos funcionais:

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

## Mapa dos módulos

- [[run_generation_test]] — runner local, orquestra o fluxo ponta a ponta.
- [[config]] — `Settings` e leitura de variáveis de ambiente.
- [[embeddings]] — modelo de embeddings BGE-M3.
- [[schemas]] — contratos Pydantic do pipeline.
- [[briefing]] — converte o briefing em consulta textual para o RAG.
- [[db_aurora]] — conexão com Aurora PostgreSQL + pgvector.
- [[retrieval]] — busca vetorial dos chunks similares.
- [[context_builder]] — monta o contexto textual rastreável para o prompt.
- [[llm]] — componentes LangChain (ChatGroq, parser, prompt, chain).
- [[generation]] — geração com validação e status padronizado.
- [[validators]] — validação de rastreabilidade das referências.
- [[aws]] — sessão AWS e cliente S3.
- [[reference_files]] — download dos documentos de referência do S3.

## Responsabilidades principais

| Módulo | Responsabilidade |
| --- | --- |
| [[config]] | Centralizar configuração via env, expor `Settings`. |
| [[embeddings]] | Gerar vetores densos com BGE-M3. |
| [[schemas]] | Definir contratos de entrada, chunks e saída. |
| [[briefing]] | Transformar briefing em texto de consulta. |
| [[db_aurora]] | Abrir/fechar conexão PostgreSQL com pgvector. |
| [[retrieval]] | Buscar chunks por similaridade de cosseno. |
| [[context_builder]] | Formatar fontes rastreáveis para o prompt. |
| [[llm]] | Montar a chain `prompt \| llm \| parser`. |
| [[generation]] | Invocar a chain e padronizar o resultado. |
| [[validators]] | Impedir referências inventadas pela LLM. |
| [[aws]] | Criar sessão/cliente S3. |
| [[reference_files]] | Baixar arquivos originais do S3. |

## Princípios da modularização

```text
Runner executa.
Módulos fornecem funções.
Dependências são passadas explicitamente.
Nada pesado acontece no import.
```

- Injeção explícita de dependências: `conn`, `embeddings`, `s3_client`, `chain`
  são criados no runner e passados como argumentos.
- Cada módulo tem responsabilidade única e não conhece detalhes dos outros além
  do contrato (ver [[schemas]]).
- Rastreabilidade obrigatória: toda referência citada pela LLM precisa existir no
  retrieval (ver [[validators]]).

## Regras operacionais

- O import de qualquer módulo não deve ter side effects.
- Nenhum módulo abre conexão com banco no import (ver [[db_aurora]]).
- Nenhum módulo carrega o modelo de embeddings no import (ver [[embeddings]]).
- Nenhum módulo chama a LLM no import (ver [[llm]]).
- A conexão PostgreSQL deve ser usada via context manager `conexao_pg(...)`.
- O download de S3 acontece apenas no final, após a geração (ver [[reference_files]]).

## O que NÃO deve acontecer no import dos módulos

- Não conectar ao Aurora.
- Não carregar `BGEM3FlagModel`.
- Não instanciar `ChatGroq` nem invocar a chain.
- Não criar sessão/cliente AWS.
- Não baixar arquivos do S3.

Tudo isso ocorre apenas quando o [[run_generation_test|runner]] chama as funções.

## Execução local

1. Garantir as variáveis de ambiente em um arquivo `.env` na raiz do projeto
   (ver [[config]] para a lista completa).
2. Executar o runner:

```bash
python scripts/run_generation_test.py
```

O runner adiciona `src/` ao `sys.path`, carrega `Settings`, instancia as
dependências, executa retrieval + geração e baixa os documentos de referência.

## Relação entre código e documentação

- Código-fonte: `src/escreveai/*.py` e `scripts/run_generation_test.py`.
- Documentação: esta pasta (vault Obsidian), com um `.md` por módulo.
- Cada `.md` espelha um arquivo Python e deve ser atualizado junto com o código.
- O script `script_geracao_teste.py` é a versão monolítica original e não deve ser
  alterado nem apagado.

## Links dos módulos

- [[run_generation_test]]
- [[config]]
- [[db_aurora]]
- [[aws]]
- [[embeddings]]
- [[schemas]]
- [[briefing]]
- [[retrieval]]
- [[context_builder]]
- [[llm]]
- [[generation]]
- [[validators]]
- [[reference_files]]
