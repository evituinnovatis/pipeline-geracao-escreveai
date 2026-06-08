from typing import Any


def montar_contexto_rag(resultados: list[dict[str, Any]]) -> str:
    blocos = []

    for i, r in enumerate(resultados, start=1):
        texto = (r.get("texto_chunk") or "").strip()

        score = r.get("score_similaridade")
        score_fmt = f"{score:.4f}" if isinstance(score, (int, float)) else "N/A"

        bloco = f"""
[FONTE {i}]
projeto_id: {r.get("projeto_id")}
chunk_id: {r.get("chunk_id")}
projeto_titulo: {r.get("projeto_titulo")}
area: {r.get("projeto_area")}
origem: {r.get("projeto_origem")}
paginas: {r.get("page_start")} - {r.get("page_end")}
chunk_index: {r.get("chunk_index")}
score_similaridade: {score_fmt}

trecho:
{texto}
""".strip()

        blocos.append(bloco)

    return "\n\n" + ("\n\n" + "-" * 100 + "\n\n").join(blocos)

