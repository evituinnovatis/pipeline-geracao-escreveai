from pathlib import Path

from botocore.client import BaseClient
from psycopg import Connection


def baixar_documentos_referencia(
    conn: Connection,
    s3_client: BaseClient,
    projeto_ids: list[str],
    pasta_destino: str = "referencias_projeto_doc1",
) -> list[dict[str, str]]:
    pasta = Path.cwd() / pasta_destino
    pasta.mkdir(parents=True, exist_ok=True)

    sql = """
        SELECT
            projetos_referencia_rag_id,
            s3_bucket,
            s3_key,
            filename
        FROM rag.arquivos_documentos_rag
        WHERE projetos_referencia_rag_id = ANY(%s)
    """

    with conn.cursor() as cur:
        cur.execute(sql, (projeto_ids,))
        arquivos = cur.fetchall()

    arquivos_baixados = []

    for projeto_id, bucket, key, filename in arquivos:
        caminho_local = pasta / f"{projeto_id}_{filename}"

        try:
            s3_client.download_file(
                Bucket=bucket,
                Key=key,
                Filename=str(caminho_local),
            )

            arquivos_baixados.append({
                "projeto_id": str(projeto_id),
                "filename": filename,
                "bucket": bucket,
                "key": key,
                "caminho_local": str(caminho_local),
                "status": "baixado",
            })

        except Exception as e:
            arquivos_baixados.append({
                "projeto_id": str(projeto_id),
                "filename": filename,
                "bucket": bucket,
                "key": key,
                "erro": str(e),
                "status": "erro",
            })

    return arquivos_baixados

