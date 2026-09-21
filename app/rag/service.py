from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from app.config import settings


class BusKnowledgeService:

    def __init__(self):

        self.embeddings = OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )

        self.vector_store = Chroma(
            persist_directory=settings.chroma_dir,
            embedding_function=self.embeddings,
        )

        self.retriever = (
            self.vector_store.as_retriever(
                search_kwargs={
                    "k": 3
                }
            )
        )

    def search(
        self,
        question: str
    ) -> list[dict]:

        docs = self.retriever.invoke(
            question
        )

        results = []

        for doc in docs:
            results.append(
                {
                    "content":
                        doc.page_content,

                    "source":
                        doc.metadata,
                }
            )

        return results