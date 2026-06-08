# reference_files.py

Arquivo: `src/escreveai/reference_files.py`

## Objetivo

Baixar do S3 os documentos originais associados aos projetos de referência citados,
após a geração, registrando o status por arquivo.

## Papel no pipeline RAG

Fluxo anterior: [[generation]] (+ [[aws]], [[db_aurora]])
Fluxo atual: [[reference_files]]
Fluxo seguinte: — (etapa final)

## Responsabilidades

- Receber `conn` e `s3_client` explicitamente.
- Criar a pasta de destino local se necessário.
- Consultar `rag.arquivos_documentos_rag` pelos `projeto_ids`.
- Baixar cada arquivo do S3.
- Registrar status (`baixado` ou `erro`) por arquivo.

## Principais funções/classes

- `baixar_documentos_referencia(conn, s3_client, projeto_ids, pasta_destino="referencias_projeto_doc1") -> list[dict]`
  - Cria `pasta_destino` (relativa a `Path.cwd()`).
  - SQL: seleciona `s3_bucket`, `s3_key`, `filename` onde
    `projetos_referencia_rag_id = ANY(projeto_ids)`.
  - Para cada arquivo, chama `s3_client.download_file(...)`.
  - Sucesso => dict com `status: "baixado"` e `caminho_local`;
    falha => dict com `status: "erro"` e `erro`.

## Entradas

- `conn` ([[db_aurora]]), `s3_client` ([[aws]]).
- `projeto_ids` (`list[str]`) — extraídos dos resultados de [[retrieval]].
- `pasta_destino` (de [[config]] `references_dir`, montada pelo runner).

## Saídas

- `list[dict]` — um registro por arquivo, com metadados e `status`.

## Dependências internas

- [[db_aurora]] (conexão), [[aws]] (cliente S3).
- Acionado pelo [[run_generation_test|runner]] após [[generation]].

## Dependências externas

- `psycopg` (`Connection`)
- `botocore` (`BaseClient`)
- `pathlib` (stdlib)

## Regras importantes

- Etapa posterior ao RAG: não interfere na geração da resposta.
- Não cria a conexão nem o cliente S3 (recebe ambos prontos).
- Falha de um arquivo não interrompe os demais (erro capturado por arquivo).
- Cuidados de autorização/confidencialidade: só baixa arquivos dos projetos
  efetivamente recuperados; o acesso ao bucket depende das credenciais de [[aws]].

## Erros possíveis

- Erro SQL (tabela `rag.arquivos_documentos_rag` ausente).
- Erro de download S3 (chave inexistente, permissão negada) — registrado como
  `status: "erro"`, sem parar o loop.
- Falha de escrita no disco local.

## Exemplo de uso

```python
from escreveai.reference_files import baixar_documentos_referencia

projeto_ids = list({str(r["projeto_id"]) for r in resultados})
arquivos = baixar_documentos_referencia(
    conn=conn,
    s3_client=s3_client,
    projeto_ids=projeto_ids,
    pasta_destino=str(PROJECT_ROOT / settings.references_dir),
)
```

## Links relacionados

- [[PipelineRAG]]
- [[aws]]
- [[db_aurora]]
- [[generation]]
