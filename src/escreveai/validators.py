from typing import Any

from escreveai.schemas import ProjetoGerado


def validar_referencias_contra_retrieval(
    projeto: ProjetoGerado,
    resultados: list[dict[str, Any]],
) -> None:
    chunks_por_projeto: dict[str, set[str]] = {}

    for resultado in resultados:
        projeto_id = str(resultado["projeto_id"])
        chunk_id = str(resultado["chunk_id"])
        chunks_por_projeto.setdefault(projeto_id, set()).add(chunk_id)

    for ref in projeto.projetos_referencia_usados:
        projeto_id = str(ref.projeto_id)

        if projeto_id not in chunks_por_projeto:
            raise ValueError(
                f"projeto_id inválido: {ref.projeto_id} não está nos resultados recuperados."
            )

        chunks_validos = chunks_por_projeto[projeto_id]
        for chunk_id in ref.chunk_ids:
            if str(chunk_id) not in chunks_validos:
                raise ValueError(
                    f"chunk_id inválido: {chunk_id} não pertence ao projeto_id "
                    f"{ref.projeto_id} nos resultados recuperados."
                )

