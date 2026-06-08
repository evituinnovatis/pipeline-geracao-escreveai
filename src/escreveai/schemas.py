from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class BriefUsuario(BaseModel):
    titulo: str
    areasRelacionadas: List[str]
    areasRelacionadasOutro: Optional[str] = ""
    resumo: str
    objetivos: str
    publicoAlvo: str
    metasEtapasFases: str
    entregaveis: str
    resultadoEsperado: str
    duracaoPeriodo: str
    ragContextSource: Literal["internal", "external", "both"] = "both"
    outputMode: Literal["draft", "complete"] = "draft"


class RetrievedChunk(BaseModel):
    chunk_id: str
    projeto_id: str
    projeto_titulo: Optional[str] = None
    projeto_area: Optional[object] = None
    projeto_origem: Optional[str] = None
    projeto_status: Optional[str] = None
    texto_chunk: Optional[str] = None
    page_start: Optional[object] = None
    page_end: Optional[object] = None
    chunk_index: Optional[int] = None
    token_count: Optional[int] = None
    char_count: Optional[int] = None
    source_origin: Optional[str] = None
    model_embedding: Optional[str] = None
    dimensions: Optional[int] = None
    score_similaridade: Optional[float] = None
    distancia_cosseno: Optional[float] = None


class ReferenciaUsada(BaseModel):
    projeto_id: str = Field(..., description="ID do projeto recuperado no RAG.")
    projeto_titulo: str = Field(..., description="Título do projeto recuperado.")
    origem: Optional[str] = Field(None, description="Origem da referência.")
    chunk_ids: List[str] = Field(
        ..., min_length=1, description="Chunks usados como referência."
    )
    paginas: List[str] = Field(
        default_factory=list, description="Páginas associadas aos chunks."
    )
    score_medio: float = Field(
        ..., ge=-1.0, le=1.0, description="Score médio de similaridade."
    )
    justificativa_uso: str = Field(
        ..., min_length=20, description="Justificativa do uso da referência."
    )


class ProjetoGerado(BaseModel):
    titulo: str = Field(..., min_length=5)
    area: List[str] = Field(..., min_length=1)
    resumo: str = Field(..., min_length=50)
    objetivos: List[str] = Field(..., min_length=1)
    publico_alvo: str = Field(..., min_length=10)
    metas_etapas_fases: List[str] = Field(..., min_length=1)
    entregaveis: List[str] = Field(..., min_length=1)
    resultado_esperado: str = Field(..., min_length=30)
    duracao_periodo: str = Field(..., min_length=1)
    projetos_referencia_usados: List[ReferenciaUsada] = Field(..., min_length=1)


class GenerationResult(BaseModel):
    status: Literal["ok", "failed_validation"]
    projeto: Optional[ProjetoGerado | dict] = None
    erro: Optional[str] = None
    detalhes: Optional[str] = None

