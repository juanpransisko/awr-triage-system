from typing import Dict
import numpy as np
from utils.document_parser import DocumentParser
from awr.embedding_generator import EmbeddingGenerator


class DocumentEmbeddingPipeline:
    """extracts structured sections from DOCX files and
    generate embeddings per section."""

    def __init__(self, parser: DocumentParser, embedder: EmbeddingGenerator):
        self.parser = parser
        self.embedder = embedder

    def process_document(self, docx_path: str) -> Dict[str, np.ndarray]:
        """extract flattened sections and generate vector embeddings."""
        logger.info(f"Processing document: {docx_path}")

        sections = self.parser.extract_awr_sections(docx_path)
        logger.debug(f"Extracted {len(sections)} sections from document")

        embeddings = {}
        for section_title, section_text in sections.items():
            try:
                embedding_vector = self.embedder.generate(section_text)
                embeddings[section_title] = embedding_vector
                logger.debug(f"Generated embedding for section: {section_title}")
            except Exception as e:
                logger.error(
                    f"Embedding generation failed for section '{section_title}': {e}"
                )

        logger.info(f"Completed embeddings for document: {docx_path}")
        return embeddings


# Example usage:

# parser = DocumentParser()
# embedder = EmbeddingGenerator()
# pipeline = DocumentEmbeddingPipeline(parser, embedder)

# embeddings = pipeline.process_document("path/to/your/awr_document.docx")

# Now embeddings is a dict: {section_path: np.ndarray(embedding_vector)}
