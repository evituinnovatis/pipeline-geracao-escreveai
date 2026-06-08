from typing import List

from FlagEmbedding import BGEM3FlagModel
from langchain_core.embeddings import Embeddings


class BGE_M3_Embeddings(Embeddings):
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        use_fp16: bool = True,
        batch_size: int = 12,
        max_length: int = 8192,
    ):
        self.model = BGEM3FlagModel(
            model_name,
            use_fp16=use_fp16,
        )
        self.batch_size = batch_size
        self.max_length = max_length

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            max_length=self.max_length,
        )["dense_vecs"]

        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(
            [text],
            batch_size=1,
            max_length=self.max_length,
        )["dense_vecs"][0]

        return embedding.tolist()


def criar_embeddings_bge_m3(
    model_name: str = "BAAI/bge-m3",
    use_fp16: bool = True,
    batch_size: int = 12,
    max_length: int = 8192,
) -> BGE_M3_Embeddings:
    return BGE_M3_Embeddings(
        model_name=model_name,
        use_fp16=use_fp16,
        batch_size=batch_size,
        max_length=max_length,
    )

