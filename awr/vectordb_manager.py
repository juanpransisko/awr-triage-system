import chromadb
from chromadb.utils import embedding_functions
from config.settings import Settings
from core.logger import logger

class VectorDBManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(Settings.CHROMA_PATH))
        self.ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=Settings.OPENAI_KEY,
            model_name="text-embedding-3-small"
        )
        self.collection = self.client.get_or_create_collection(
            name="awr_tickets",
            embedding_function=self.ef
        )
        logger.info("Vector DB [ChromaDB] initialized")

    def find_similar_tickets(self, text: str, n_results: int = 3):
        """Find similar tickets using vector search"""
        results = self.collection.query(
            query_texts=[text],
            n_results=n_results,
            include=['distances', 'metadatas']
        )
        logger.debug(f"Found {len(results['ids'][0])} similar tickets")
        return results
