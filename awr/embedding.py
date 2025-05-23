import openai
import numpy as np
from config.settings import settings
from awr.logger import logger


class EmbeddingGenerator:
    def __init__(self):
        self.model = settings.AZURE_OPENAI_DEPLOYMENT
        self.dimensions = (
            settings.AZURE_OPENAI_MODEL_DIMENSIONS
        )  # can be reduced to 256 for performance

    def generate(self, text: str) -> np.ndarray:
        if not text.strip():
            logger.warning("Empty text input for embedding generation")
            return np.zeros(self.dimensions, dtype=float)

        try:
            response = openai.embeddings.create(
                model=self.model,
                input=text,
            )
            embedding = response.data[0].embedding
            if len(embedding) != self.dimensions:
                logger.warning(
                    f"Embedding dimension mismatch: exp {self.dimensions}," \ 
                    " got {len(embedding)}"
                )
            return np.array(embedding, dtype=float)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}", exc_info=True)
            raise
