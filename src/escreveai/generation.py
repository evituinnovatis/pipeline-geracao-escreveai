from typing import Any

from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from escreveai.validators import validar_referencias_contra_retrieval


def gerar_projeto_com_validacao(
    chain,
    consulta_rag: str,
    contexto_rag: str,
    modo_saida: str,
    format_instructions: str,
    resultados: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Fluxo: LLM -> parse JSON -> validação Pydantic -> validação contra retrieval.
    Retorna dict com status 'ok' ou 'failed_validation'.
    """
    try:
        projeto_gerado = chain.invoke({
            "briefing": consulta_rag,
            "contexto_rag": contexto_rag,
            "modo_saida": modo_saida,
            "format_instructions": format_instructions,
        })
        validar_referencias_contra_retrieval(projeto_gerado, resultados)
        return {
            "status": "ok",
            "projeto": projeto_gerado.model_dump(),
        }
    except (ValidationError, OutputParserException) as e:
        return {
            "status": "failed_validation",
            "erro": "Falha na validação do schema Pydantic.",
            "detalhes": str(e),
        }
    except ValueError as e:
        return {
            "status": "failed_validation",
            "erro": str(e),
        }
    except Exception as e:
        return {
            "status": "failed_validation",
            "erro": f"Erro inesperado na geração: {e}",
        }

