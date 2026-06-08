from contextlib import contextmanager
from collections.abc import Iterator

import psycopg
from pgvector.psycopg import register_vector


def abrir_conexao_pg(database_url: str) -> psycopg.Connection:
    conn = psycopg.connect(
        database_url,
        autocommit=False,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )
    register_vector(conn)
    return conn


@contextmanager
def conexao_pg(database_url: str) -> Iterator[psycopg.Connection]:
    conn = abrir_conexao_pg(database_url)
    try:
        yield conn
    finally:
        conn.close()

