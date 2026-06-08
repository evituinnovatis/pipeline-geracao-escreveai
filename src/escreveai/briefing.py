from typing import Any


def brief_para_consulta_rag(brief: dict[str, Any]) -> str:
    areas = ", ".join(brief.get("areasRelacionadas", []))

    if "Outro" in brief.get("areasRelacionadas", []):
        outro = brief.get("areasRelacionadasOutro", "").strip()
        if outro:
            areas += f", {outro}"

    partes_projetos = [
        f"Título do projeto: {brief.get('titulo', '')}",
        f"Áreas relacionadas: {areas}",
        f"Resumo do projeto: {brief.get('resumo', '')}",
        f"Objetivos: {brief.get('objetivos', '')}",
        f"Público-alvo: {brief.get('publicoAlvo', '')}",
        f"Metas, etapas e fases: {brief.get('metasEtapasFases', '')}",
        f"Entregáveis: {brief.get('entregaveis', '')}",
        f"Resultado esperado: {brief.get('resultadoEsperado', '')}",
        f"Duração/período: {brief.get('duracaoPeriodo', '')}",
    ]

    return "\n".join(
        parte for parte in partes_projetos
        if parte.split(":", 1)[1].strip()
    )

