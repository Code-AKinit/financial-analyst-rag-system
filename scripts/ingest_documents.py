"""
Document ingestion script.

Processes all documents in data/raw/ and indexes them in the vector store.
"""

import sys
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.logging_config import configure_logging, get_logger
from src.config.settings import get_settings
from src.domain.models.document import Document, DocumentChunk
from src.infrastructure.document_processing.csv_processor import CSVProcessor
from src.infrastructure.document_processing.excel_processor import ExcelProcessor
from src.infrastructure.document_processing.pdf_processor import PDFProcessor
from src.infrastructure.vector_store.chroma_store import ChromaVectorStore

# Configure logging
configure_logging()
logger = get_logger(__name__)


class DocumentIngestionPipeline:
    """
    Pipeline for ingesting documents into the vector store.
    """

    def __init__(self):
        """Initialize ingestion pipeline."""
        settings = get_settings()

        # Initialize processors
        self.processors = [
            PDFProcessor(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            ),
            ExcelProcessor(),
            CSVProcessor(),
        ]

        # Initialize vector store
        self.vector_store = ChromaVectorStore()

        self.data_dir = Path("data/raw")

        logger.info("ingestion_pipeline_initialized")

    def ingest_all_documents(self) -> None:
        """
        Ingest all documents from data/raw directory.
        """
        logger.info("starting_document_ingestion", data_dir=str(self.data_dir))

        if not self.data_dir.exists():
            logger.error("data_directory_not_found", data_dir=str(self.data_dir))
            print(f"❌ Error: Directory {self.data_dir} does not exist")
            print(f"Please create it and add your financial documents.")
            return

        # Get all files
        files = list(self.data_dir.glob("*"))
        document_files = [f for f in files if f.is_file() and not f.name.startswith(".")]

        if not document_files:
            logger.warning("no_documents_found", data_dir=str(self.data_dir))
            print(f"⚠️  No documents found in {self.data_dir}")
            print(f"Please add your financial documents (PDF, Excel, CSV) to this directory.")
            return

        logger.info("found_documents", count=len(document_files))
        print(f"\n📁 Found {len(document_files)} document(s) to process\n")

        # Process each file
        all_chunks: List[DocumentChunk] = []

        for file_path in document_files:
            try:
                print(f"Processing: {file_path.name}...")
                chunks = self.process_document(file_path)

                if chunks:
                    all_chunks.extend(chunks)
                    print(f"  ✓ Created {len(chunks)} chunks")
                else:
                    print(f"  ⚠️  No chunks created")

            except Exception as e:
                logger.error("document_processing_failed", file=str(file_path), error=str(e))
                print(f"  ❌ Error: {e}")
                continue

        if not all_chunks:
            logger.warning("no_chunks_created")
            print("\n⚠️  No chunks were created. Check your documents.")
            return

        # Index in vector store
        print(f"\n📊 Indexing {len(all_chunks)} chunks in vector store...")

        try:
            self.vector_store.add_documents(all_chunks)
            print(f"✓ Successfully indexed all chunks")

            # Show stats
            stats = self.vector_store.get_collection_stats()
            print(f"\n📈 Vector Store Statistics:")
            print(f"  Collection: {stats['collection_name']}")
            print(f"  Total chunks: {stats['document_count']}")
            print(f"  Location: {stats['persist_directory']}")

            logger.info("ingestion_completed", total_chunks=len(all_chunks))
            print(f"\n✅ Document ingestion completed successfully!")

        except Exception as e:
            logger.error("indexing_failed", error=str(e))
            print(f"\n❌ Error indexing documents: {e}")

    def process_document(self, file_path: Path) -> List[DocumentChunk]:
        """
        Process a single document.

        Args:
            file_path: Path to document

        Returns:
            List[DocumentChunk]: Created chunks
        """
        # Find appropriate processor
        processor = None
        for proc in self.processors:
            if proc.can_process(file_path):
                processor = proc
                break

        if not processor:
            logger.warning("no_processor_found", file=str(file_path))
            raise ValueError(f"No processor found for file: {file_path.name}")

        # Process document
        document = processor.process_document(file_path)

        # Create chunks
        chunks = processor.create_chunks(document)

        return chunks

    def reset_vector_store(self) -> None:
        """
        Reset the vector store (delete all data).

        Use with caution!
        """
        logger.warning("resetting_vector_store")
        print("⚠️  Resetting vector store...")

        try:
            self.vector_store.delete_collection()
            print("✓ Vector store reset complete")

        except Exception as e:
            logger.error("reset_failed", error=str(e))
            print(f"❌ Error resetting vector store: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest financial documents")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset vector store before ingesting (deletes all existing data)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("📄 Financial Document Ingestion Pipeline")
    print("=" * 60)

    try:
        pipeline = DocumentIngestionPipeline()

        if args.reset:
            confirm = input("\n⚠️  This will delete all existing data. Continue? (yes/no): ")
            if confirm.lower() == "yes":
                pipeline.reset_vector_store()
            else:
                print("Reset cancelled.")
                return

        pipeline.ingest_all_documents()

    except KeyboardInterrupt:
        print("\n\n⚠️  Ingestion interrupted by user")
        logger.warning("ingestion_interrupted")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error("ingestion_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
