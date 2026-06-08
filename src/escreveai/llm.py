from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from escreveai.schemas import ProjetoGerado


def criar_llm_groq(
    api_key: str,
    model: str,
    temperature: float = 0,
) -> ChatGroq:
    return ChatGroq(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )


def criar_parser_projeto() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=ProjetoGerado)


def criar_prompt_geracao() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        (
            "system",
            """
Você é um especialista em escrita de projetos institucionais.

Use o briefing do usuário e as fontes RAG recuperadas para gerar um documento estruturado.

Regras obrigatórias:
- A saída deve seguir exatamente o schema fornecido.
- Não inclua texto fora do JSON.
- Não invente projeto_id, chunk_id, score, páginas ou títulos de referência.
- Só use referências presentes em FONTES RAG.
- Use as fontes como referência, mas não copie literalmente.
- Caso uma informação não esteja no briefing nem nas fontes, não trate como fato.

{format_instructions}
"""
        ),
        (
            "human",
            """
BRIEFING DO USUÁRIO:
{briefing}

FONTES RAG:
{contexto_rag}

MODO DE SAÍDA:
{modo_saida}
"""
        ),
    ])


def criar_chain_geracao(
    llm: ChatGroq,
    prompt: ChatPromptTemplate,
    parser: PydanticOutputParser,
):
    return prompt | llm | parser

