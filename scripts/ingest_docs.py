"""
Document Ingestion Script for GAMP 5 and CSA Regulatory Documents.

This script chunks PDF documents and prepares them for vector storage in Pinecone.

:requirement: URS-5.1 - System shall ingest regulatory documents for RAG.
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# PDF processing with LangChain
try:
    from langchain_community.document_loaders import PyPDFLoader
except ImportError:
    PyPDFLoader = None

# Text chunking
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None

# Pinecone
try:
    from pinecone import Pinecone, ServerlessSpec
except ImportError:
    Pinecone = None
    ServerlessSpec = None

# Embeddings
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# Configuration
DOCS_RAW_DIR = Path(__file__).parent.parent / "docs" / "raw"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
PINECONE_INDEX_NAME = "csv-knowledge-base"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"


def _derive_reg_version(filename: str) -> str:
    """
    Derive a regulatory version identifier from a PDF filename.

    Strips the file extension and returns the stem as the version
    string (e.g. ``"GAMP5_Rev2.pdf"`` becomes ``"GAMP5_Rev2"``).

    :param filename: The PDF filename (not a full path).
    :return: Version string derived from the filename stem.
    :requirement: URS-14.1 - System shall derive reg version from
                  PDF filename at ingestion.
    """
    return Path(filename).stem


class DocumentChunk:
    """
    Represents a chunk of a document with metadata.

    :requirement: URS-5.2 - System shall maintain document traceability.
    """

    def __init__(
        self,
        text: str,
        source_document: str,
        page_number: int,
        chunk_index: int,
        timestamp: str,
        reg_version: str = ""
    ):
        self.text = text
        self.source_document = source_document
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.timestamp = timestamp
        self.reg_version = reg_version
        self.chunk_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique ID for the chunk."""
        content = f"{self.source_document}:{self.page_number}:{self.chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()

    def to_metadata(self) -> Dict[str, Any]:
        """
        Convert chunk to metadata dictionary for Pinecone.

        :return: Dictionary with source_document, page_number, and timestamp.
        :requirement: URS-5.3 - System shall attach metadata to each chunk.
        """
        return {
            "source_document": self.source_document,
            "page_number": self.page_number,
            "timestamp": self.timestamp,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "reg_version": self.reg_version
        }


def check_dependencies() -> bool:
    """
    Verify all required dependencies are installed.

    :return: True if all dependencies available, False otherwise.
    :requirement: URS-5.4 - System shall validate environment before processing.
    """
    missing = []
    if PyPDFLoader is None:
        missing.append("langchain-community (pip install langchain-community)")
    if RecursiveCharacterTextSplitter is None:
        missing.append("langchain-text-splitters (pip install langchain-text-splitters)")
    if Pinecone is None:
        missing.append("pinecone (pip install pinecone)")
    if OpenAI is None:
        missing.append("openai (pip install openai)")

    if missing:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        return False
    return True


def load_pdfs_from_directory(docs_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all PDF files from a directory using PyPDFLoader.

    :param docs_dir: Path to directory containing PDF files.
    :return: List of documents with page content and metadata.
    :requirement: URS-5.5 - System shall read PDF files from docs/raw.
    """
    if PyPDFLoader is None:
        raise ImportError("langchain-community is required for PDF loading")

    all_documents = []
    pdf_files = list(docs_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {docs_dir}")
        return all_documents

    print(f"Found {len(pdf_files)} PDF files to process")

    for pdf_path in pdf_files:
        print(f"Loading: {pdf_path.name}")
        try:
            loader = PyPDFLoader(str(pdf_path))
            documents = loader.load()
            for doc in documents:
                all_documents.append({
                    "content": doc.page_content,
                    "source_document": pdf_path.name,
                    "page_number": doc.metadata.get("page", 0) + 1
                })
            print(f"  Loaded {len(documents)} pages")
        except Exception as e:
            print(f"  Error loading {pdf_path.name}: {e}")

    return all_documents


def chunk_documents(
    documents: List[Dict[str, Any]],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[DocumentChunk]:
    """
    Split documents into overlapping chunks using RecursiveCharacterTextSplitter.

    :param documents: List of documents with content and metadata.
    :param chunk_size: Maximum size of each chunk (default 1000).
    :param chunk_overlap: Overlap between chunks (default 200).
    :return: List of DocumentChunk objects with metadata.
    :requirement: URS-5.6 - System shall chunk text with 1000-char size and 200-char overlap.
    """
    if RecursiveCharacterTextSplitter is None:
        raise ImportError("langchain is required for text chunking")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = []
    timestamp = datetime.now(timezone.utc).isoformat()
    chunk_index = 0

    for doc in documents:
        text_chunks = splitter.split_text(doc["content"])
        reg_version = _derive_reg_version(doc["source_document"])
        for text in text_chunks:
            chunk = DocumentChunk(
                text=text,
                source_document=doc["source_document"],
                page_number=doc["page_number"],
                chunk_index=chunk_index,
                timestamp=timestamp,
                reg_version=reg_version
            )
            chunks.append(chunk)
            chunk_index += 1

    return chunks


def get_embeddings(texts: List[str], openai_client: "OpenAI") -> List[List[float]]:
    """
    Generate embeddings for a list of texts using OpenAI.

    :param texts: List of texts to embed.
    :param openai_client: OpenAI client instance.
    :return: List of embedding vectors.
    :requirement: URS-5.7 - System shall generate embeddings for chunks.
    """
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]


def ensure_pinecone_index_exists(
    pc: "Pinecone",
    index_name: str = PINECONE_INDEX_NAME,
    dimension: int = EMBEDDING_DIMENSION
) -> None:
    """
    Check if Pinecone index exists and create it if not.

    :param pc: Pinecone client instance.
    :param index_name: Name of the index to check/create.
    :param dimension: Embedding dimension for the index.
    :requirement: URS-5.8 - System shall verify index exists before upserting.
    """
    existing_indexes = [idx.name for idx in pc.list_indexes()]

    if index_name in existing_indexes:
        print(f"Index '{index_name}' already exists")
        return

    print(f"Creating index '{index_name}'...")
    pc.create_index(
        name=index_name,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(
            cloud=PINECONE_CLOUD,
            region=PINECONE_REGION
        )
    )
    print(f"Index '{index_name}' created successfully")


def upsert_to_pinecone(
    chunks: List[DocumentChunk],
    embeddings: List[List[float]],
    pinecone_client: "Pinecone",
    index_name: str = PINECONE_INDEX_NAME
) -> int:
    """
    Upsert document chunks with embeddings to Pinecone index 'csv-knowledge-base'.

    This function checks if the index exists before upserting. Each chunk is
    stored with metadata including source_document, page_number, and timestamp.

    :param chunks: List of DocumentChunk objects with metadata.
    :param embeddings: Corresponding embedding vectors.
    :param pinecone_client: Pinecone client instance.
    :param index_name: Name of the Pinecone index (default: csv-knowledge-base).
    :return: Number of vectors upserted.
    :requirement: URS-5.9 - System shall upsert chunks to Pinecone index.
    """
    # Ensure index exists before upserting
    ensure_pinecone_index_exists(pinecone_client, index_name)

    # Get index reference
    index = pinecone_client.Index(index_name)

    # Prepare vectors with metadata
    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        vectors.append({
            "id": chunk.chunk_id,
            "values": embedding,
            "metadata": chunk.to_metadata()
        })

    # Upsert in batches of 100 to avoid rate limits
    batch_size = 100
    total_upserted = 0

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
        total_upserted += len(batch)
        print(f"  Upserted {total_upserted}/{len(vectors)} vectors")

    return total_upserted


def ingest_documents(
    docs_dir: Path = DOCS_RAW_DIR,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Ingest all PDF documents from docs/raw into Pinecone.

    Pipeline:
    1. Load PDFs using PyPDFLoader
    2. Chunk text using RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
    3. Add metadata (source_document, page_number, timestamp)
    4. Generate embeddings via OpenAI
    5. Upsert to Pinecone index 'csv-knowledge-base'

    :param docs_dir: Directory containing PDF files.
    :param dry_run: If True, process but don't upload to Pinecone.
    :return: Summary statistics of the ingestion.
    :requirement: URS-5.1 - System shall ingest regulatory documents for RAG.
    """
    if not check_dependencies():
        return {"status": "error", "message": "Missing dependencies"}

    if not docs_dir.exists():
        print(f"Creating docs/raw directory: {docs_dir}")
        docs_dir.mkdir(parents=True, exist_ok=True)
        return {
            "status": "error",
            "message": f"No documents found. Add PDFs to {docs_dir}"
        }

    # Step 1: Load PDFs using PyPDFLoader
    print("\n[Step 1/4] Loading PDFs with PyPDFLoader...")
    print("-" * 50)
    documents = load_pdfs_from_directory(docs_dir)

    if not documents:
        return {"status": "error", "message": "No documents loaded"}

    # Step 2: Chunk documents with RecursiveCharacterTextSplitter
    print("\n[Step 2/4] Chunking documents...")
    print(f"  Chunk size: {CHUNK_SIZE}, Overlap: {CHUNK_OVERLAP}")
    print("-" * 50)
    chunks = chunk_documents(documents)
    print(f"Total chunks created: {len(chunks)}")

    # Show sample metadata
    if chunks:
        sample = chunks[0]
        print("\nSample chunk metadata:")
        print(f"  source_document: {sample.source_document}")
        print(f"  page_number: {sample.page_number}")
        print(f"  timestamp: {sample.timestamp}")
        print(f"  reg_version: {sample.reg_version}")

    if dry_run:
        print("\n[DRY RUN] Skipping embedding and Pinecone upload")
        return {
            "status": "success",
            "mode": "dry_run",
            "documents_loaded": len(documents),
            "total_chunks": len(chunks)
        }

    # Validate API keys
    openai_api_key = os.getenv("OPENAI_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")

    if not openai_api_key:
        return {"status": "error", "message": "Missing OPENAI_API_KEY"}
    if not pinecone_api_key:
        return {"status": "error", "message": "Missing PINECONE_API_KEY"}

    # Step 3: Generate embeddings
    print("\n[Step 3/4] Generating embeddings...")
    print("-" * 50)
    openai_client = OpenAI(api_key=openai_api_key)
    texts = [chunk.text for chunk in chunks]

    # Process embeddings in batches
    batch_size = 100
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = get_embeddings(batch, openai_client)
        all_embeddings.extend(batch_embeddings)
        print(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)} chunks")

    # Step 4: Upsert to Pinecone
    print("\n[Step 4/4] Upserting to Pinecone...")
    print(f"  Index: {PINECONE_INDEX_NAME}")
    print("-" * 50)
    pc = Pinecone(api_key=pinecone_api_key)
    upserted = upsert_to_pinecone(chunks, all_embeddings, pc)

    # Detect new regulatory versions in this batch
    batch_versions = {
        c.reg_version for c in chunks if c.reg_version
    }
    if batch_versions:
        print(f"\n  Regulatory versions in batch: "
              f"{', '.join(sorted(batch_versions))}")
        try:
            index = pc.Index(PINECONE_INDEX_NAME)
            stats = index.describe_index_stats()
            existing_versions: set = set()
            # Sample a few vectors to discover existing versions
            sample_ids = [
                c.chunk_id for c in chunks[:5]
            ]
            if sample_ids:
                fetched = index.fetch(ids=sample_ids)
                for vec in fetched.vectors.values():
                    ver = vec.metadata.get("reg_version", "")
                    if ver:
                        existing_versions.add(ver)
            new_versions = batch_versions - existing_versions
            if new_versions:
                for ver in sorted(new_versions):
                    print(
                        f"\n  New regulatory version detected: "
                        f"{ver}. Do you wish to re-evaluate "
                        f"existing logic? (y/n)"
                    )
                    try:
                        answer = input("  > ").strip().lower()
                    except EOFError:
                        answer = "n"
                    if answer == "y":
                        print(
                            f"  Flagged {ver} for "
                            f"re-evaluation."
                        )
        except Exception:
            pass  # Non-critical; proceed with ingestion

    print("\n" + "=" * 50)
    print("INGESTION COMPLETE")
    print("=" * 50)
    print(f"  Documents processed: {len(documents)}")
    print(f"  Chunks created: {len(chunks)}")
    print(f"  Vectors upserted: {upserted}")

    return {
        "status": "success",
        "documents_loaded": len(documents),
        "total_chunks": len(chunks),
        "vectors_upserted": upserted,
        "index_name": PINECONE_INDEX_NAME,
        "reg_versions": sorted(batch_versions)
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest GAMP 5 and CSA documents into Pinecone"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process documents without uploading to Pinecone"
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=DOCS_RAW_DIR,
        help="Directory containing PDF files"
    )
    args = parser.parse_args()

    result = ingest_documents(
        docs_dir=args.docs_dir,
        dry_run=args.dry_run
    )
    print("\nResult:", result)
