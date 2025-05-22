import openai
import numpy as np
from config.settings import Settings
from utils.logger import logger

class EmbeddingGenerator:
    def __init__(self):
        self.model = Settings.AZURE_OPENAI_DEPLOYMENT
        self.dimensions = 3072  # Can reduce to 256 for smaller vectors

    def generate(self, text: str) -> np.ndarray:
        try:
            response = openai.embeddings.create(
                input=text,
                model=self.model,
                dimensions=self.dimensions
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            logger.error(f"Embedding failed: {str(e)}")
            raise
