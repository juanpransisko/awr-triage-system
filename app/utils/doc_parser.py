from docx import Document
import re
from collections import defaultdict


def normalize(text: str) -> str:
    ''' for easier parsing, convert all to lowercase '''
    return re.sub(r'\s+', ' ', text.strip().lower())

# these are the document sections I believe will contain important data
# can be updated as deemed necessary
TARGET_PATHS = {
    ("customer requirements details", "functional requirements"),
    ("customer requirements details", "technical requirements"),
    ("customer requirements details", "required delivery date"),
    ("champ proposed solution", "business solution"),
    ("champ proposed solution", "technical solution"),
    ("champ proposed solution", "limitations"),
    ("pricing and payment terms", "price", "one-time charges"),
    ("pricing and payment terms", "price", "annual maintenance charges"),
    ("pricing and payment terms", "payment terms", "one-time charges"),
    ("pricing and payment terms", "payment terms", "annual maintenance charges"),
}

def nested_dict():
    ''' for structuring the parsed document contens '''
    return defaultdict(nested_dict)

def set_nested(d, keys, value):
    ''' for storing the values in the nested dictionary '''
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
            current_path = current_path[:level-1]  # Trim to current level
            current_path.append(text)
        else:
            section_buffer.append(text)

    flush_buffer() # last section
    return result

