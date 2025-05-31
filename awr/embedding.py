import openai
import numpy as np
from config.settings import settings
from awr.logger import logger
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_VERSION,
)
import numpy as np
from config.settings import settings
from awr.logger import logger

# Azure OpenAI configuration


class EmbeddingGenerator:
    def __init__(self):
        self.model = settings.AZURE_OPENAI_DEPLOYMENT
        self.dimensions = settings.AZURE_OPENAI_MODEL_DIMENSIONS

    def generate(self, text: str) -> np.ndarray:
        if not text.strip():
            logger.warning("Empty text input for embedding generation")
            return np.zeros(self.dimensions, dtype=float)

        try:
            response = client.embeddings.create(
                model=self.model, input=text  # Azure Engine
            )
            embedding = response.data[0].embedding
            if len(embedding) != self.dimensions:
                logger.warning(
                    f"Embedding dimension mismatch: expected {self.dimensions}, got {len(embedding)}"
                )
            return np.array(embedding, dtype=float)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}", exc_info=True)
            raise
