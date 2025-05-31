import chromadb
from chromadb.errors import DuplicateIDError
import shutil
import chromadb.utils.embedding_functions as embedding_functions
from config.settings import settings
from awr.logger import logger
import xml.etree.ElementTree as ET
from hashlib import sha256


def check_existing_db():
    try:
        shutil.rmtree(settings.CHROMA_PATH)
    except FileNotFoundError:
        pass


class ChromaDB:
    chunks = []
    documents = []
    metadatas = []
    uids = []

    def __init__(self):
        check_existing_db()
        self.ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_base=settings.AZURE_OPENAI_ENDPOINT,
            api_type="azure",
            api_version="2023-05-15",
            deployment_id=settings.AZURE_OPENAI_DEPLOYMENT,
        )
        self.client = chromadb.PersistentClient(path=str(settings.CHROMA_PATH))
        self.collection = self.client.get_or_create_collection(
            name="awr", embedding_function=self.ef
        )
        logger.info("AWR Vector ChromaDB initialized")

    def _get_element_text(self, parent, tag_names):
        """
        Try to find an element with any of the given tag names and return its text.
        Returns empty string if none found.
        """
        for tag_name in tag_names:
            # Try direct child first
            elem = parent.find(tag_name)
            if elem is not None:
                return elem.text.strip() if elem.text else ""

            # Try case-insensitive search
            for child in parent:
                if child.tag.lower() == tag_name.lower():
                    return child.text.strip() if child.text else ""

        return ""

    # Parse the XML file
    def parse_xml_file(self, file_path):
        records = []

        try:
            # Parse the XML file
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Look for record elements - adjust these based on your XML structure
            # Common patterns: 'record', 'item', 'entry', or the root elements directly
            record_elements = (
                root.findall(".//record")
                or root.findall(".//item")
                or root.findall(".//entry")
            )

            # If no nested records found, treat direct children as records
            if not record_elements:
                record_elements = list(root)

            for record_elem in record_elements:
                record = {}

                # Extract fields - adjust field names based on your XML structure
                record["ID"] = self._get_element_text(record_elem, ["ID", "id", "Id"])
                record["JIRA_AWR_Title"] = self._get_element_text(
                    record_elem, ["JIRA_AWR_Title", "title", "Title"]
                )
                record["JIRA_AWR_Description"] = self._get_element_text(
                    record_elem, ["JIRA_AWR_Description", "description", "Description"]
                )
                record["JIRA_AWR_URL"] = self._get_element_text(
                    record_elem, ["JIRA_AWR_URL", "url", "URL", "link"]
                )
                record["AWR_Document_Version"] = self._get_element_text(
                    record_elem, ["AWR_Document_Version", "version", "Version"]
                )
                record["AWR_Document_Reference"] = self._get_element_text(
                    record_elem,
                    ["AWR_Document_Reference", "refer", "reference", "Reference"],
                )
                record["AWR_DOC_JIRA_REF"] = self._get_element_text(
                    record_elem, ["AWR_DOC_JIRA_REF", "jira_ref", "jiraRef"]
                )
                record["AWR_DOC_Short_Work_Desc"] = self._get_element_text(
                    record_elem, ["AWR_DOC_Short_Work_Desc", "short_work", "shortWork"]
                )
                record["AWR_DOC_CUST_REQ_Summary"] = self._get_element_text(
                    record_elem, ["AWR_DOC_CUST_REQ_Summary", "cust_req", "summary"]
                )
                record["AWR_DOC_CUST_REQ_Details"] = self._get_element_text(
                    record_elem, ["AWR_DOC_CUST_REQ_Details", "req_details", "details"]
                )
                record["AWR_DOC_Business_Solution"] = self._get_element_text(
                    record_elem,
                    ["AWR_DOC_Business_Solution", "business_solution", "solution"],
                )
                record["WIKI_PAGE_URL"] = self._get_element_text(
                    record_elem, ["WIKI_PAGE_URL", "page_url", "url"]
                )
                record["WIKI_PAGE_Heading"] = self._get_element_text(
                    record_elem, ["WIKI_PAGE_Heading", "page_heading", "heading"]
                )
                record["WIKI_PAGE_Details"] = self._get_element_text(
                    record_elem, ["WIKI_PAGE_Details", "page_details", "details"]
                )

                # Only add records that have at least an ID or title
                if record["ID"] or record["JIRA_AWR_Title"]:
                    records.append(record)

        except ET.ParseError as e:
            logger.error("Error parsing XML file", extra={"file_path": file_path})
            return []
        except FileNotFoundError:
            logger.error(f"XML file not found: {file_path}")
            return []

        return records

    # Alternative parsing function for attribute-based XML
    def parse_xml_file_attributes(self, file_path):
        """
        Alternative parser for XML files where data is stored in
        attributes rather than text content.
        """
        records = []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            record_elements = (
                root.findall(".//record")
                or root.findall(".//item")
                or root.findall(".//entry")
            )
            if not record_elements:
                record_elements = list(root)

            for record_elem in record_elements:
                record = {}

                # Extract from attributes
                attrs = record_elem.attrib
                record["ID"] = attrs.get("ID", attrs.get("id", ""))
                record["JIRA_AWR_Title"] = attrs.get(
                    "JIRA_AWR_Title", attrs.get("title", "")
                )
                record["JIRA_AWR_Description"] = attrs.get(
                    "JIRA_AWR_Description", attrs.get("description", "")
                )
                record["JIRA_AWR_URL"] = attrs.get("JIRA_AWR_URL", attrs.get("url", ""))
                record["AWR_Document_Version"] = attrs.get(
                    "AWR_Document_Version", attrs.get("version", "")
                )
                record["AWR_Document_Reference"] = attrs.get(
                    "AWR_Document_Reference", attrs.get("refer", "")
                )
                record["AWR_DOC_JIRA_REF"] = attrs.get(
                    "AWR_DOC_JIRA_REF", attrs.get("jira_ref", "")
                )
                record["AWR_DOC_Short_Work_Desc"] = attrs.get(
                    "AWR_DOC_Short_Work_Desc", attrs.get("short_work", "")
                )
                record["AWR_DOC_CUST_REQ_Summary"] = attrs.get(
                    "AWR_DOC_CUST_REQ_Summary", attrs.get("cust_req", "")
                )
                record["AWR_DOC_CUST_REQ_Details"] = attrs.get(
                    "AWR_DOC_CUST_REQ_Details", attrs.get("req_details", "")
                )
                record["AWR_DOC_Business_Solution"] = attrs.get(
                    "AWR_DOC_Business_Solution", attrs.get("business_solution", "")
                )
                record["WIKI_PAGE_URL"] = attrs.get(
                    "WIKI_PAGE_URL", attrs.get("page_url", "")
                )
                record["WIKI_PAGE_Heading"] = attrs.get(
                    "WIKI_PAGE_Heading", attrs.get("page_heading", "")
                )
                record["WIKI_PAGE_Details"] = attrs.get(
                    "WIKI_PAGE_Details", attrs.get("page_details", "")
                )

                # Also check child elements for any missing data
                for field_name in record:
                    if not record[field_name]:
                        record[field_name] = self._get_element_text(
                            record_elem, [field_name]
                        )

                if record["ID"] or record["JIRA_AWR_Title"]:
                    records.append(record)

        except ET.ParseError as e:
            logger.error(f"Error parsing XML file: {e}")
            return []
        except FileNotFoundError:
            logger.error(f"XML file not found: {file_path}")
            return []

        return records

    def populate(self, documents, metadatas, uids):
        try:
            if not (documents and metadatas and uids):
                logger.warning("No valid documents found to add to ChromaDB.")
                return False

            assert (
                len(documents) == len(metadatas) == len(uids)
            ), "Input lists must match in length"

            documents = [doc for doc in documents if doc]

            self.collection.upsert(documents=documents, metadatas=metadatas, ids=uids)
            logger.info(f"Added {len(documents)} documents to ChromaDB")
            logger.info(f"Collection now contains {self.collection.count()} entries.")
            return True

        except DuplicateIDError:
            logger.warning("Duplicate records found.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in populate method: {e}", exc_info=True)
            return False

    def init_populate(self, xml_file_path=None):
        """we initialize chromadb using the contents of xml file,"""
        if not xml_file_path:
            xml_file_path = settings.XML_SOURCE

        # Try element-based parsing first, then attribute-based if needed
        records = self.parse_xml_file(xml_file_path)

        # If no records found, try attribute-based parsing
        if not records:
            logger.warning(
                "No records found with element-based parsing, "
                "trying attribute-based parsing..."
            )
            records = self.parse_xml_file_attributes(xml_file_path)

        logger.info(f"Found {len(records)} records in XML file")

        for record in records:
            # Create document content by combining title and description
            title = record.get("JIRA_AWR_Title", "").strip()
            description = record.get("JIRA_AWR_Description", "").strip()

            if title and description:
                document_content = f"{title} - {description}"
            elif title:
                document_content = title
            elif description:
                document_content = description
            else:
                continue
            self.documents.append(document_content)

            # Create a metadata dictionary with all fields
            self.metadatas.append(
                {
                    "ID": record.get("ID", ""),
                    "JIRA_AWR_Title": record.get("JIRA_AWR_Title", ""),
                    "JIRA_AWR_Description": record.get("JIRA_AWR_Description", ""),
                    "JIRA_AWR_URL": record.get("JIRA_AWR_URL", ""),
                    "AWR_Document_Version": record.get("AWR_Document_Version", ""),
                    "AWR_Document_Reference": record.get("AWR_Document_Reference", ""),
                    "AWR_DOC_JIRA_REF": record.get("AWR_DOC_JIRA_REF", ""),
                    "AWR_DOC_Short_Work_Desc": record.get(
                        "AWR_DOC_Short_Work_Desc", ""
                    ),
                    "AWR_DOC_CUST_REQ_Summary": record.get(
                        "AWR_DOC_CUST_REQ_Summary", ""
                    ),
                    "AWR_DOC_CUST_REQ_Details": record.get(
                        "AWR_DOC_CUST_REQ_Details", ""
                    ),
                    "AWR_DOC_Business_Solution": record.get(
                        "AWR_DOC_Business_Solution", ""
                    ),
                    "WIKI_PAGE_URL": record.get("WIKI_PAGE_URL", ""),
                    "WIKI_PAGE_Heading": record.get("WIKI_PAGE_Heading", ""),
                    "WIKI_PAGE_Details": record.get("WIKI_PAGE_Details", ""),
                }
            )

            # Generate a unique ID based on content and record ID to avoid duplicates
            record_id = record.get("ID", "unknown")
            uid = sha256(f"{record_id}_{document_content}".encode("utf-8")).hexdigest()
            self.uids.append(uid)

        # load the processed xml data to chromadb
        self.populate(self.documents, self.metadatas, self.uids)
        return 0

    def query(self, query_text: str, n_results: int = 3):
        awr_docs = self.client.get_collection(name="awr", embedding_function=self.ef)
        results = awr_docs.query(query_texts=[query_text], n_results=n_results)

        v_awr = []
        for i in range(len(results["documents"][0])):
            metadata = results["metadatas"][0][i]
            v_awr.append(
                {
                    "id": metadata.get("AWR_DOC_JIRA_REF"),
                    "url": metadata.get("JIRA_AWR_URL"),
                    "distance": results["distances"][0][i],
                }
            )
        return v_awr
