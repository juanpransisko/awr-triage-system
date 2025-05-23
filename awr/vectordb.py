from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from config import settings
import chromadb

class ChromaManager:
    def __init__(self):
        self.embed_fn = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            device="cpu",
            normalize_embeddings=True
        )
        self.client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIR))
        self.collection = self.client.get_or_create_collection(
            name="awr_tickets",
            embedding_function=self.embed_fn
        )

    def query_tickets(self, text: str, n_results: int = 3):
        """Query similar tickets with distance scores"""
        return self.collection.query(
            query_texts=[text],
            n_results=n_results,
            include=['distances', 'metadatas']
        )
