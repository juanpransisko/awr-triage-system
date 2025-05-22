from docx import Document
import re
import json
from collections import defaultdict


def normalize(text: str) -> str:
    """for easier parsing, convert all to lowercase"""
    return re.sub(r"\s+", " ", text.strip().lower())


# these are the document sections I believe will contain important data
# can be updated as deemed necessary
TARGET_PATHS = {
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


def nested_dict():
    """for structuring the parsed document contens"""
    return defaultdict(nested_dict)


def set_nested(d, keys, value):
    """for storing the values in the nested dictionary"""
    for key in keys[:-1]:
        d = d[key]
    d[keys[-1]] = value.strip()


def extract_structured_sections(file_path):
    doc = Document(file_path)
    result = nested_dict()
    current_path = []
    section_buffer = []

    def flush_buffer():
        if not current_path:
            return
        norm_path = tuple(normalize(p) for p in current_path)
        if norm_path in TARGET_PATHS:
            set_nested(result, current_path, "\n".join(section_buffer).strip())

    for para in doc.paragraphs:
        style = para.style.name
        text = para.text.strip()
        if not text:
            continue

        if style.startswith("Heading"):
            # flush existing buffer before updating path
            flush_buffer()
            section_buffer = []

            # Determine heading level
            level = int(re.search(r"\d+", style).group())
            current_path = current_path[: level - 1]  # Trim to current level
            current_path.append(text)
        else:
            section_buffer.append(text)

    flush_buffer()  # last section
    return result


def clean_whitespace(s):
    return re.sub(r"\s+", " ", s).strip()


def dict_to_json(nested_dict):
    """since we use defaultdict here, we need to convert it to json"""

    def to_dict(nested_dict):
        """recursive covnersion here"""
        if isinstance(nested_dict, defaultdict):
            return {k: to_dict(v) for k, v in nested_dict.items()}
        return nested_dict

    # to regular dictionary now then to json str then deserialize
    converted = to_dict(nested_dict)
    json_value = json.loads(json.dumps(converted, indent=2))
    return json_value


def flatten_json(nested_json, parent_key="", sep=" > "):
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
            flat_dict.update(flatten_json(value, new_key, sep=sep))

        else:
            # Normalize whitespace in value
            cleaned_value = " ".join(value.split())
            flat_dict[new_key] = cleaned_value

    return flat_dict


def extract_awr_sections(document_path: str):
    """
    returns the extracted document sections in a flattened json format
    """

    sections = extract_structured_sections(document_path)
    json_value = dict_to_json(sections)
    return flatten_json(json_value)
