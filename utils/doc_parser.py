from docx import Document
import re
import json
from collections import defaultdict
from typing import Dict, Any, Tuple, Optional


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


class DocumentParser:

    DEFAULT_TARGET_PATHS = {
        ("customer requirements details", "functional requirements"),
        ("customer requirements details", "technical requirements"),
        ("customer requirements details", "required delivery date"),
        ("champ proposed solution", "business solution"),
        ("champ proposed solution", "technical solution"),
        ("champ proposed solution", "limitations"),
        ("timescales and notifications", "delivery date"),
        ("timescales and notifications", "notifications"),
        ("pricing and payment terms", "price", "one-time charges"),
        ("pricing and payment terms", "price", "annual maintenance charges"),
        ("pricing and payment terms", "payment terms", "one-time charges"),
        ("pricing and payment terms", "payment terms", "annual maintenance charges"),
    }

    def __init__(self, target_paths: Optional[set[Tuple[str, ...]]] = None):
        self.target_paths = target_paths or self.DEFAULT_TARGET_PATHS

    @staticmethod
    def nested_dict() -> defaultdict:
        """to capture nested values"""
        return defaultdict(DocumentParser.nested_dict)

    @staticmethod
    def set_nested(d: dict, keys: Tuple[str, ...], value: str) -> None:
        """for saving the values that comes nested"""
        for key in keys[:-1]:
            d = d[key]
        d[keys[-1]] = value.strip()

    def extract_structured_sections(self, file_path: str) -> dict:
        """extracts document sections matching target paths into nested dict."""
        try:
            doc = Document(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load DOCX file '{file_path}': {e}")

        result = self.nested_dict()
        current_path = []
        section_buffer = []

        def flush_buffer():
            if not current_path:
                return
            norm_path = tuple(normalize(p) for p in current_path)
            if norm_path in self.target_paths:
                self.set_nested(result, current_path, "\n".join(section_buffer).strip())

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            style = para.style.name if para.style else ""
            if style.lower().startswith("heading"):
                flush_buffer()
                section_buffer = []

                match = re.search(r"\d+", style)
                if match:
                    level = int(match.group())
                    # trim or extend current_path for heading level
                    current_path = current_path[: level - 1]
                else:
                    current_path = []
                current_path.append(text)
            else:
                section_buffer.append(text)
        flush_buffer()
        return result

    @staticmethod
    def dict_to_json(nested_dict: dict) -> dict:
        """convert nested defaultdict to normal dict recursively."""
        if isinstance(nested_dict, defaultdict):
            return {k: DocumentParser.dict_to_json(v) for k, v in nested_dict.items()}
        return nested_dict

    @staticmethod
    def flatten_json(nested_json: dict, parent_key: str = "", sep: str = " > ") -> dict:
        """after reading, if we are going to feed json to the embedding model,
        then it is more advisable to have the data in flattened format particularly
        because of the nested sections. we do this to ensure that one section
        pertains to a semantic unit, one topic at a time for easier retrieval.

        Example:
        {
            "Pricing and Payment Terms": {
                "Payment Terms": {
                    "Annual Maintenance Charges": "Customer shall pay..."
                }
            }
        }

        will be converted to
        {
        "Pricing and Payment Terms > Payment Terms > Annual Maintenance Charges":
            "Customer shall pay..."
        }
        """
        flat_dict = {}
        for key, value in nested_json.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                flat_dict.update(DocumentParser.flatten_json(value, new_key, sep=sep))
            else:
                flat_dict[new_key] = " ".join(value.split())  # normalize whitespace
        return flat_dict

    def extract_awr_sections(self, document_path: str) -> dict:
        """extracts and flattens important AWR sections from a DOCX file."""
        nested_sections = self.extract_structured_sections(document_path)
        normalized = self.dict_to_json(nested_sections)
        return self.flatten_json(normalized)


# parser = DocumentParser()
# flattened_sections = parser.extract_awr_sections("sample_awr.docx")
# print(flattened_sections)
