"""
Knowledge Base Ingestion Script

Reads curated knowledge documents, generates embeddings, and stores them in ChromaDB.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings
from modules.rag_engine import RAGEngine

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def read_knowledge_documents(knowledge_base_dir: Path) -> List[Dict[str, Any]]:
    """Read all knowledge documents from the knowledge base directory.
    
    Args:
        knowledge_base_dir: Path to knowledge_base directory
        
    Returns:
        List of document dictionaries with text and metadata
    """
    documents = []
    
    # Categories to process
    categories = ['emotions', 'genres', 'instruments', 'contexts']
    
    for category in categories:
        category_dir = knowledge_base_dir / category
        
        if not category_dir.exists():
            logger.warning(f"Category directory not found: {category_dir}")
            continue
        
        # Read all .txt files in the category
        for file_path in category_dir.glob('*.txt'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract topic from filename
                topic = file_path.stem.replace('_', ' ').title()
                
                # Create document
                doc = {
                    'id': str(uuid.uuid4()),
                    'text': content,
                    'metadata': {
                        'category': category.rstrip('s'),  # Remove plural
                        'topic': topic,
                        'source': str(file_path.name)
                    }
                }
                
                documents.append(doc)
                logger.info(f"Loaded: {category}/{file_path.name} - {topic}")
                
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {e}")
    
    return documents


def chunk_document(doc: Dict[str, Any], max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
    """Split large documents into smaller chunks if needed.
    
    Args:
        doc: Document dictionary
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of chunked documents
    """
    text = doc['text']
    
    # If document is small enough, return as-is
    if len(text) <= max_chunk_size:
        return [doc]
    
    # Split by paragraphs (double newline)
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        if current_size + para_size > max_chunk_size and current_chunk:
            # Save current chunk
            chunk_text = '\n\n'.join(current_chunk)
            chunk_doc = {
                'id': f"{doc['id']}_chunk_{len(chunks)}",
                'text': chunk_text,
                'metadata': doc['metadata'].copy()
            }
            chunks.append(chunk_doc)
            
            # Start new chunk
            current_chunk = [para]
            current_size = para_size
        else:
            current_chunk.append(para)
            current_size += para_size
    
    # Add final chunk
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        chunk_doc = {
            'id': f"{doc['id']}_chunk_{len(chunks)}",
            'text': chunk_text,
            'metadata': doc['metadata'].copy()
        }
        chunks.append(chunk_doc)
    
    return chunks


def ingest_knowledge_base(force_rebuild: bool = False):
    """Ingest knowledge documents into ChromaDB.
    
    Args:
        force_rebuild: If True, delete existing collection and rebuild
    """
    logger.info("="*70)
    logger.info("KNOWLEDGE BASE INGESTION")
    logger.info("="*70)
    
    settings = get_settings()
    
    # Find knowledge base directory
    workspace_root = Path(__file__).parent.parent
    knowledge_base_dir = workspace_root / 'data' / 'knowledge_base'
    
    if not knowledge_base_dir.exists():
        logger.error(f"Knowledge base directory not found: {knowledge_base_dir}")
        return False
    
    logger.info(f"Knowledge base directory: {knowledge_base_dir}")
    
    # Read documents
    logger.info("\nReading knowledge documents...")
    documents = read_knowledge_documents(knowledge_base_dir)
    
    if not documents:
        logger.error("No documents found!")
        return False
    
    logger.info(f"Loaded {len(documents)} documents")
    
    # Chunk large documents
    logger.info("\nChunking documents...")
    chunked_docs = []
    for doc in documents:
        chunks = chunk_document(doc, max_chunk_size=1000)
        chunked_docs.extend(chunks)
    
    logger.info(f"Created {len(chunked_docs)} chunks from {len(documents)} documents")
    
    # Initialize RAG engine
    logger.info("\nInitializing RAG engine...")
    try:
        rag_engine = RAGEngine()
    except Exception as e:
        logger.error(f"Failed to initialize RAG engine: {e}")
        return False
    
    # Handle force rebuild
    if force_rebuild:
        logger.warning("Force rebuild enabled - deleting existing collection")
        try:
            rag_engine.chroma_client.delete_collection(name=settings.collection_name)
            logger.info("Existing collection deleted")
        except Exception as e:
            logger.info(f"No existing collection to delete: {e}")
    
    # Create or get collection
    logger.info(f"\nCreating collection: {settings.collection_name}")
    try:
        collection = rag_engine.chroma_client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"description": "Music knowledge for emotion-based recommendations"}
        )
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        return False
    
    # Generate embeddings and add to collection
    logger.info("\nGenerating embeddings and adding to ChromaDB...")
    
    batch_size = 10
    total_chunks = len(chunked_docs)
    
    for i in range(0, total_chunks, batch_size):
        batch = chunked_docs[i:i+batch_size]
        
        try:
            # Prepare batch data
            ids = [doc['id'] for doc in batch]
            texts = [doc['text'] for doc in batch]
            metadatas = [doc['metadata'] for doc in batch]
            
            # Generate embeddings
            embeddings = [rag_engine.embed_text(text) for text in texts]
            
            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            logger.info(f"Progress: {min(i+batch_size, total_chunks)}/{total_chunks} chunks processed")
            
        except Exception as e:
            logger.error(f"Failed to process batch {i//batch_size + 1}: {e}")
            return False
    
    # Verify ingestion
    logger.info("\nVerifying ingestion...")
    try:
        count = collection.count()
        logger.info(f"Collection contains {count} documents")
        
        if count != total_chunks:
            logger.warning(f"Expected {total_chunks} but found {count}")
        
    except Exception as e:
        logger.error(f"Failed to verify ingestion: {e}")
        return False
    
    logger.info("\n" + "="*70)
    logger.info("[SUCCESS] Knowledge base ingestion complete!")
    logger.info("="*70)
    logger.info(f"Vector store: {settings.vector_db_dir}")
    logger.info(f"Collection: {settings.collection_name}")
    logger.info(f"Documents: {count}")
    logger.info(f"Embedding model: {settings.embedding_model}")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build knowledge base for RAG")
    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Force rebuild - delete existing collection'
    )
    
    args = parser.parse_args()
    
    success = ingest_knowledge_base(force_rebuild=args.rebuild)
    
    if success:
        sys.exit(0)
    else:
        logger.error("\n[FAILED] Knowledge base ingestion failed")
        sys.exit(1)
