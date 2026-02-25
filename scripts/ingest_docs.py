"""
Document Ingestion Script for GAMP 5 and CSA Regulatory Documents.

This script chunks PDF documents and prepares them for vector storage
in Pinecone. Supports manifest-based deduplication, tqdm progress bars,
and non-blocking new-version detection.

:requirement: URS-5.1 - System shall ingest regulatory documents for RAG.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Optional progress bars ─────────────────────────────────────────────
try:
    from tqdm import tqdm as _tqdm
except ImportError:
    _tqdm = None


def _progress_wrap(
    iterable,
    desc: str = "",
    total: Optional[int] = None,
):
    """
    Wrap an iterable with tqdm if available, otherwise return as-is.

    :param iterable: The iterable to wrap.
    :param desc: Description label for the progress bar.
    :param total: Total count (used when iterable has no len).
    :return: Wrapped (or original) iterable.
    """
    if _tqdm is not None:
        return _tqdm(iterable, desc=desc, total=total)
    return iterable


# ── PDF / text-split / Pinecone / OpenAI imports ─────────────────────
try:
    from langchain_community.document_loaders import PyPDFLoader
except ImportError:
    PyPDFLoader = None

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None

try:
    from pinecone import Pinecone, ServerlessSpec
except ImportError:
    Pinecone = None
    ServerlessSpec = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ── Configuration ──────────────────────────────────────────────────────
DOCS_RAW_DIR = Path(__file__).parent.parent / "docs" / "raw"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
PINECONE_INDEX_NAME = "csv-knowledge-base"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"

# Manifest lives in docs/ alongside the raw PDFs
REG_MANIFEST_PATH = (
    Path(__file__).parent.parent / "docs" / "reg_manifest.json"
)


# ── Manifest helpers ──────────────────────────────────────────────────
def _load_reg_manifest() -> Dict[str, Any]:
    """
    Load the regulatory document manifest from disk.

    :return: Manifest dict (empty structure if file absent).
    :requirement: URS-14.8 - System shall detect new reg versions.
    """
    if REG_MANIFEST_PATH.exists():
        try:
            return json.loads(
                REG_MANIFEST_PATH.read_text(encoding="utf-8")
            )
        except Exception:
            pass
    return {"reg_versions": {}, "new_versions_pending_review": []}


def _save_reg_manifest(manifest: Dict[str, Any]) -> None:
    """
    Write the regulatory manifest to disk.

    :param manifest: Manifest dict to serialise.
    :requirement: URS-14.8 - System shall detect new reg versions.
    """
    REG_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    REG_MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


def _update_manifest_for_version(
    manifest: Dict[str, Any],
    ver: str,
    fname: str,
    fhash: str,
    chunk_count: int,
    is_new: bool,
) -> None:
    """
    Insert or update a version entry in the manifest dict (in-place).

    :param manifest: The manifest dict to mutate.
    :param ver: Regulatory version string (e.g. "GAMP5_Rev2").
    :param fname: PDF file name.
    :param fhash: SHA-256 hash of the PDF file.
    :param chunk_count: Number of chunks produced.
    :param is_new: True if this version was not in the manifest before.
    :requirement: URS-14.8 - System shall detect new reg versions.
    """
    now = datetime.now(timezone.utc).isoformat()
    existing = manifest["reg_versions"].get(ver)

    if existing is None:
        manifest["reg_versions"][ver] = {
            "file_name": fname,
            "file_hash": fhash,
            "first_ingested": now,
            "last_updated": now,
            "chunk_count": chunk_count,
            "status": "ingested",
        }
    else:
        existing["file_name"] = fname
        existing["file_hash"] = fhash
        existing["last_updated"] = now
        existing["chunk_count"] = chunk_count
        existing["status"] = "ingested"

    if is_new:
        pending = manifest.setdefault(
            "new_versions_pending_review", []
        )
        if ver not in pending:
            pending.append(ver)


def _compute_file_hash(path: Path) -> str:
    """
    Compute SHA-256 hex digest of a file.

    :param path: Path to the file.
    :return: Hex SHA-256 string.
    """
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Core helpers ───────────────────────────────────────────────────────
def _derive_reg_version(filename: str) -> str:
    """
    Derive a regulatory version identifier from a PDF filename.

    Strips the file extension and returns the stem as the version
    string (e.g. ``"GAMP5_Rev2.pdf"`` → ``"GAMP5_Rev2"``).

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
        reg_version: str = "",
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
        content = (
            f"{self.source_document}:"
            f"{self.page_number}:{self.chunk_index}"
        )
        return hashlib.md5(content.encode()).hexdigest()

    def to_metadata(self) -> Dict[str, Any]:
        """
        Convert chunk to metadata dictionary for Pinecone.

        :return: Dictionary with source_document, page_number,
                 timestamp, text, chunk_index, and reg_version.
        :requirement: URS-5.3 - System shall attach metadata to chunks.
        """
        return {
            "source_document": self.source_document,
            "page_number": self.page_number,
            "timestamp": self.timestamp,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "reg_version": self.reg_version,
        }


def check_dependencies() -> bool:
    """
    Verify all required dependencies are installed.

    :return: True if all dependencies available, False otherwise.
    :requirement: URS-5.4 - System shall validate environment.
    """
    missing = []
    if PyPDFLoader is None:
        missing.append(
            "langchain-community (pip install langchain-community)"
        )
    if RecursiveCharacterTextSplitter is None:
        missing.append(
            "langchain-text-splitters "
            "(pip install langchain-text-splitters)"
        )
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


def load_pdfs_from_directory(
    docs_dir: Path,
    manifest: Optional[Dict[str, Any]] = None,
    skip_existing: bool = False,
) -> List[Dict[str, Any]]:
    """
    Load all PDF files from a directory using PyPDFLoader.

    When ``skip_existing=True`` and a manifest is provided, PDFs whose
    reg_version already has a matching ``file_hash`` in the manifest
    are skipped without re-processing.

    :param docs_dir: Path to directory containing PDF files.
    :param manifest: Optional reg_manifest dict for skip logic.
    :param skip_existing: Skip PDFs already in the manifest.
    :return: List of documents with page content and metadata.
    :requirement: URS-5.5 - System shall read PDF files from docs/raw.
    """
    if PyPDFLoader is None:
        raise ImportError(
            "langchain-community is required for PDF loading"
        )

    all_documents: List[Dict[str, Any]] = []
    pdf_files = list(docs_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {docs_dir}")
        return all_documents

    print(f"Found {len(pdf_files)} PDF files to process")

    reg_versions = (
        (manifest or {}).get("reg_versions", {})
    )

    for pdf_path in _progress_wrap(
        pdf_files, desc="Loading PDFs", total=len(pdf_files)
    ):
        ver = _derive_reg_version(pdf_path.name)

        # Skip if hash unchanged in manifest
        if skip_existing and manifest is not None:
            entry = reg_versions.get(ver)
            if entry is not None:
                existing_hash = entry.get("file_hash", "")
                if existing_hash:
                    current_hash = _compute_file_hash(pdf_path)
                    if current_hash == existing_hash:
                        print(
                            f"  Skipping {pdf_path.name} "
                            f"(unchanged, hash match)"
                        )
                        continue

        if _tqdm is None:
            print(f"Loading: {pdf_path.name}")
        try:
            loader = PyPDFLoader(str(pdf_path))
            documents = loader.load()
            for doc in documents:
                all_documents.append({
                    "content": doc.page_content,
                    "source_document": pdf_path.name,
                    "page_number": doc.metadata.get("page", 0) + 1,
                })
            if _tqdm is None:
                print(f"  Loaded {len(documents)} pages")
        except Exception as exc:
            print(f"  Error loading {pdf_path.name}: {exc}")

    return all_documents


def chunk_documents(
    documents: List[Dict[str, Any]],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    """
    Split documents into overlapping chunks.

    :param documents: List of documents with content and metadata.
    :param chunk_size: Maximum size of each chunk (default 1000).
    :param chunk_overlap: Overlap between chunks (default 200).
    :return: List of DocumentChunk objects with metadata.
    :requirement: URS-5.6 - System shall chunk text.
    """
    if RecursiveCharacterTextSplitter is None:
        raise ImportError("langchain is required for text chunking")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: List[DocumentChunk] = []
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
                reg_version=reg_version,
            )
            chunks.append(chunk)
            chunk_index += 1

    return chunks


def get_embeddings(
    texts: List[str],
    openai_client: "OpenAI",
) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using OpenAI.

    :param texts: List of texts to embed.
    :param openai_client: OpenAI client instance.
    :return: List of embedding vectors.
    :requirement: URS-5.7 - System shall generate embeddings for chunks.
    """
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def ensure_pinecone_index_exists(
    pc: "Pinecone",
    index_name: str = PINECONE_INDEX_NAME,
    dimension: int = EMBEDDING_DIMENSION,
) -> None:
    """
    Check if Pinecone index exists and create it if not.

    :param pc: Pinecone client instance.
    :param index_name: Name of the index to check/create.
    :param dimension: Embedding dimension for the index.
    :requirement: URS-5.8 - System shall verify index exists.
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
            region=PINECONE_REGION,
        ),
    )
    print(f"Index '{index_name}' created successfully")


def upsert_to_pinecone(
    chunks: List[DocumentChunk],
    embeddings: List[List[float]],
    pinecone_client: "Pinecone",
    index_name: str = PINECONE_INDEX_NAME,
) -> int:
    """
    Upsert document chunks with embeddings to Pinecone.

    :param chunks: List of DocumentChunk objects with metadata.
    :param embeddings: Corresponding embedding vectors.
    :param pinecone_client: Pinecone client instance.
    :param index_name: Name of the Pinecone index.
    :return: Number of vectors upserted.
    :requirement: URS-5.9 - System shall upsert chunks to Pinecone.
    """
    ensure_pinecone_index_exists(pinecone_client, index_name)
    index = pinecone_client.Index(index_name)

    vectors = [
        {
            "id": chunk.chunk_id,
            "values": embedding,
            "metadata": chunk.to_metadata(),
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]

    batch_size = 100
    total_upserted = 0

    for i in _progress_wrap(
        range(0, len(vectors), batch_size),
        desc="Upserting to Pinecone",
        total=(len(vectors) + batch_size - 1) // batch_size,
    ):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
        total_upserted += len(batch)
        if _tqdm is None:
            print(
                f"  Upserted {total_upserted}/{len(vectors)} vectors"
            )

    return total_upserted


def ingest_documents(
    docs_dir: Path = DOCS_RAW_DIR,
    dry_run: bool = False,
    skip_existing: bool = False,
) -> Dict[str, Any]:
    """
    Ingest all PDF documents from docs/raw into Pinecone.

    Pipeline:
    1. Load PDFs using PyPDFLoader (with optional skip-existing logic)
    2. Chunk text using RecursiveCharacterTextSplitter
    3. Generate embeddings via OpenAI
    4. Upsert to Pinecone index 'csv-knowledge-base'
    5. Update reg_manifest.json for version tracking

    New regulatory versions are flagged non-interactively in the
    manifest under ``new_versions_pending_review``.

    :param docs_dir: Directory containing PDF files.
    :param dry_run: If True, process but do not upload to Pinecone.
    :param skip_existing: Skip PDFs already in manifest (hash match).
    :return: Summary statistics of the ingestion.
    :requirement: URS-5.1 - System shall ingest regulatory documents.
    """
    if not check_dependencies():
        return {"status": "error", "message": "Missing dependencies"}

    if not docs_dir.exists():
        print(f"Creating docs/raw directory: {docs_dir}")
        docs_dir.mkdir(parents=True, exist_ok=True)
        return {
            "status": "error",
            "message": f"No documents found. Add PDFs to {docs_dir}",
        }

    # Load manifest
    manifest = _load_reg_manifest()

    # Step 1: Load PDFs
    print("\n[Step 1/4] Loading PDFs with PyPDFLoader...")
    print("-" * 50)
    documents = load_pdfs_from_directory(
        docs_dir,
        manifest=manifest,
        skip_existing=skip_existing,
    )

    if not documents:
        return {"status": "error", "message": "No documents loaded"}

    # Step 2: Chunk
    print("\n[Step 2/4] Chunking documents...")
    print(
        f"  Chunk size: {CHUNK_SIZE}, Overlap: {CHUNK_OVERLAP}"
    )
    print("-" * 50)
    chunks = chunk_documents(documents)
    print(f"Total chunks created: {len(chunks)}")

    if chunks:
        sample = chunks[0]
        print("\nSample chunk metadata:")
        print(f"  source_document: {sample.source_document}")
        print(f"  page_number: {sample.page_number}")
        print(f"  timestamp: {sample.timestamp}")
        print(f"  reg_version: {sample.reg_version}")

    if dry_run:
        # Still detect new versions and update manifest
        batch_versions = {
            c.reg_version for c in chunks if c.reg_version
        }
        existing_versions = set(manifest["reg_versions"].keys())
        new_versions = batch_versions - existing_versions

        for ver in sorted(new_versions):
            # Find the pdf path for hash computation
            pdf_path = docs_dir / f"{ver}.pdf"
            fhash = (
                _compute_file_hash(pdf_path)
                if pdf_path.exists() else ""
            )
            _update_manifest_for_version(
                manifest, ver, f"{ver}.pdf", fhash, 0, is_new=True
            )
            print(
                f"\n  New regulatory version detected: {ver}. "
                f"Flagged for review in reg_manifest.json."
            )

        if new_versions:
            _save_reg_manifest(manifest)

        print("\n[DRY RUN] Skipping embedding and Pinecone upload")
        return {
            "status": "success",
            "mode": "dry_run",
            "documents_loaded": len(documents),
            "total_chunks": len(chunks),
            "reg_versions": sorted(batch_versions),
            "new_versions_flagged": sorted(new_versions),
        }

    # Validate API keys
    openai_api_key = os.getenv("OPENAI_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")

    if not openai_api_key:
        return {
            "status": "error",
            "message": "Missing OPENAI_API_KEY",
        }
    if not pinecone_api_key:
        return {
            "status": "error",
            "message": "Missing PINECONE_API_KEY",
        }

    # Step 3: Embeddings
    print("\n[Step 3/4] Generating embeddings...")
    print("-" * 50)
    openai_client = OpenAI(api_key=openai_api_key)
    texts = [chunk.text for chunk in chunks]

    batch_size = 100
    all_embeddings: List[List[float]] = []

    for i in _progress_wrap(
        range(0, len(texts), batch_size),
        desc="Embedding chunks",
        total=(len(texts) + batch_size - 1) // batch_size,
    ):
        batch = texts[i:i + batch_size]
        batch_embeddings = get_embeddings(batch, openai_client)
        all_embeddings.extend(batch_embeddings)
        if _tqdm is None:
            print(
                f"  Embedded "
                f"{min(i + batch_size, len(texts))}/{len(texts)}"
                f" chunks"
            )

    # Step 4: Upsert
    print("\n[Step 4/4] Upserting to Pinecone...")
    print(f"  Index: {PINECONE_INDEX_NAME}")
    print("-" * 50)
    pc = Pinecone(api_key=pinecone_api_key)
    upserted = upsert_to_pinecone(chunks, all_embeddings, pc)

    # Detect and record regulatory versions (no blocking input())
    batch_versions = {
        c.reg_version for c in chunks if c.reg_version
    }
    existing_versions = set(manifest["reg_versions"].keys())
    new_versions = batch_versions - existing_versions

    if batch_versions:
        print(
            f"\n  Regulatory versions in batch: "
            f"{', '.join(sorted(batch_versions))}"
        )

    for ver in sorted(batch_versions):
        pdf_path = docs_dir / f"{ver}.pdf"
        fhash = (
            _compute_file_hash(pdf_path)
            if pdf_path.exists() else ""
        )
        chunk_count = sum(
            1 for c in chunks if c.reg_version == ver
        )
        is_new = ver in new_versions
        _update_manifest_for_version(
            manifest, ver, f"{ver}.pdf", fhash,
            chunk_count, is_new,
        )
        if is_new:
            print(
                f"\n  New regulatory version detected: {ver}. "
                f"Flagged for review in reg_manifest.json."
            )

    if batch_versions:
        _save_reg_manifest(manifest)

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
        "reg_versions": sorted(batch_versions),
        "new_versions_flagged": sorted(new_versions),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest GAMP 5 and CSA documents into Pinecone"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Process documents without uploading to Pinecone; "
            "manifest is still updated."
        ),
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=DOCS_RAW_DIR,
        help="Directory containing PDF files",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help=(
            "Skip PDFs whose reg_version hash already matches "
            "the manifest (avoids re-ingesting unchanged files)."
        ),
    )
    args = parser.parse_args()

    result = ingest_documents(
        docs_dir=args.docs_dir,
        dry_run=args.dry_run,
        skip_existing=args.skip_existing,
    )
    print("\nResult:", result)
