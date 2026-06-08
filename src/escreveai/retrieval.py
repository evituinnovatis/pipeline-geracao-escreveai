from typing import Any

from langchain_core.embeddings import Embeddings
from psycopg import Connection


def buscar_chunks_similares(
    conn: Connection,
    embeddings: Embeddings,
    consulta: str,
    top_k: int = 12,
    dimensions: int = 1024,
    rag_context_source: str = "both",
) -> list[dict[str, Any]]:
    vetor = embeddings.embed_query(consulta)

    if len(vetor) != dimensions:
        raise ValueError(
            f"Dimensão inválida do vetor da query: {len(vetor)}. "
            f"Esperado: {dimensions}."
        )

    filtros = [
        "ce.chunk_embedding IS NOT NULL",
        "ce.dimensions = %s",
    ]

    params_filtros: list[Any] = [dimensions]

    if rag_context_source == "internal":
        filtros.append("LOWER(TRIM(p.origin)) = LOWER(TRIM(%s))")
        params_filtros.append("Innovatis")

    elif rag_context_source == "external":
        filtros.append("LOWER(TRIM(p.origin)) <> LOWER(TRIM(%s))")
        params_filtros.append("Innovatis")

    elif rag_context_source == "both":
        pass

    else:
        raise ValueError(
            "rag_context_source inválido. Use: 'internal', 'external' ou 'both'."
        )

    where_clause = " AND ".join(filtros)

    sql = f"""
        SELECT
            c.id AS chunk_id,
            c.projetos_referencia_rag_id AS projeto_id,
            p.title_project AS projeto_titulo,
            p.area AS projeto_area,
            p.origin AS projeto_origem,
            p.status AS projeto_status,

            c.raw_text AS texto_chunk,
            c.page_start,
            c.page_end,
            c.chunk_index,
            c.token_count,
            c.char_count,
            c.source_origin,

            ce.model_embedding,
            ce.dimensions,

            1 - (ce.chunk_embedding <=> %s::vector) AS score_similaridade,
            ce.chunk_embedding <=> %s::vector AS distancia_cosseno

        FROM rag.chunks_embeddings ce

        JOIN rag.chunks c
            ON c.id = ce.chunk_id

        JOIN rag.projetos_referencia_rag p
            ON p.id = c.projetos_referencia_rag_id

        WHERE {where_clause}

        ORDER BY ce.chunk_embedding <=> %s::vector

        LIMIT %s;
    """

    params = [vetor, vetor] + params_filtros + [vetor, top_k]

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

    return [dict(zip(columns, row)) for row in rows]

