"""
RAG (Retrieval-Augmented Generation) Engine

Uses sentence transformers and ChromaDB for semantic retrieval of music knowledge.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from config.settings import get_settings

logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieval-Augmented Generation engine for music knowledge retrieval."""

    def __init__(self):
        """Initialize RAG engine with embedding model and vector store."""
        self.settings = get_settings()
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self._initialize()

    def _initialize(self):
        """Initialize embedding model and ChromaDB connection."""
        try:
            logger.info(f"Initializing embedding model: {self.settings.embedding_model}")
            self.embedding_model = SentenceTransformer(
                self.settings.embedding_model,
                device=self.settings.embedding_device
            )
            logger.info(f"Embedding model loaded on {self.settings.embedding_device}")

            # Initialize ChromaDB with persistent storage
            logger.info(f"Initializing ChromaDB at: {self.settings.vector_db_dir}")
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.settings.vector_db_dir),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(
                    name=self.settings.collection_name
                )
                logger.info(f"Loaded existing collection: {self.settings.collection_name}")
            except Exception:
                logger.warning(f"Collection {self.settings.collection_name} not found, will be created during ingestion")
                self.collection = None

        except Exception as e:
            logger.error(f"RAG engine initialization failed: {e}")
            raise

    def is_knowledge_base_ready(self) -> bool:
        """Check if knowledge base has been ingested.
        
        Returns:
            True if collection exists and has documents
        """
        if not self.collection:
            try:
                self.collection = self.chroma_client.get_collection(
                    name=self.settings.collection_name
                )
            except Exception:
                return False
        
        try:
            count = self.collection.count()
            return count > 0
        except Exception:
            return False

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    @staticmethod
    def normalize_distance(distance: Optional[float], metric: str = "cosine") -> float:
        """Convert supported Chroma distances into a bounded relevance score."""
        if distance is None:
            return 0.0
        value = max(float(distance), 0.0)
        metric = (metric or "cosine").lower()
        if metric in {"cosine", "cosine_distance"}:
            return min(max(1.0 - value, 0.0), 1.0)
        if metric in {"l2", "euclidean"}:
            return 1.0 / (1.0 + value)
        return 1.0 / (1.0 + value)

    def _collection_metric(self) -> str:
        """Read the collection metric when Chroma exposes it; default to cosine."""
        metadata = getattr(self.collection, "metadata", {}) or {}
        return str(metadata.get("hnsw:space", "cosine"))

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant knowledge chunks using semantic search.
        
        Args:
            query: Search query
            top_k: Number of results to return (default from config)
            filter_metadata: Optional metadata filters
            
        Returns:
            List of retrieved documents with metadata
        """
        if not self.is_knowledge_base_ready():
            logger.error("Knowledge base not ready - run build_knowledge_base.py first")
            return []

        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []

        top_k = top_k or self.settings.retrieval_top_k

        try:
            logger.info(f"Retrieving top-{top_k} documents for query: {query[:100]}...")
            
            # Generate query embedding
            query_embedding = self.embed_text(query)

            # Perform semantic search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata,
                include=['documents', 'metadatas', 'distances']
            )

            # Format results
            retrieved_docs = []
            if results and results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    doc = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'relevance_score': self.normalize_distance(
                            results['distances'][0][i] if results['distances'] else None,
                            self._collection_metric(),
                        )
                    }
                    retrieved_docs.append(doc)

            logger.info(f"Retrieved {len(retrieved_docs)} documents")
            return retrieved_docs

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []

    def retrieve_multi(
        self,
        queries: List[str],
        top_k: Optional[int] = None,
        per_query_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve and fuse a small set of targeted semantic queries."""
        unique_queries = list(dict.fromkeys(query.strip() for query in queries if query and query.strip()))
        if not unique_queries:
            return []
        per_query_k = per_query_k or self.settings.retrieval_top_k
        fused: Dict[str, Dict[str, Any]] = {}
        for query in unique_queries:
            for rank, document in enumerate(self.retrieve(query, top_k=per_query_k)):
                key = str(document.get("id"))
                contribution = float(document.get("relevance_score") or 0.0) + 0.5 / (rank + 1)
                if key not in fused:
                    fused[key] = dict(document)
                    fused[key]["relevance_score"] = contribution
                else:
                    fused[key]["relevance_score"] = max(float(fused[key]["relevance_score"]), contribution)
        results = sorted(fused.values(), key=lambda item: item["relevance_score"], reverse=True)
        return results[: (top_k or self.settings.retrieval_top_k)]

    def retrieve_by_category(
        self,
        query: str,
        category: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve documents filtered by category.
        
        Args:
            query: Search query
            category: Category to filter (emotion, genre, instrument, context)
            top_k: Number of results
            
        Returns:
            Retrieved documents from specified category
        """
        return self.retrieve(
            query=query,
            top_k=top_k,
            filter_metadata={'category': category}
        )

    def format_retrieved_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context string for LLM.
        
        Args:
            retrieved_docs: List of retrieved document dictionaries
            
        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return "No relevant knowledge found."

        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            metadata = doc.get('metadata', {})
            category = metadata.get('category', 'unknown')
            topic = metadata.get('topic', 'unknown')
            text = doc.get('text', '')
            relevance = doc.get('relevance_score', 0.0)

            context_parts.append(
                f"[{i}] {category.upper()}: {topic}\n"
                f"Relevance: {relevance:.2f}\n"
                f"{text}\n"
            )

        return "\n".join(context_parts)

    def get_retrieval_summary(self, retrieved_docs: List[Dict[str, Any]]) -> List[str]:
        """Create human-readable summary of retrieved knowledge.
        
        Args:
            retrieved_docs: Retrieved documents
            
        Returns:
            List of summary strings
        """
        if not retrieved_docs:
            return ["No knowledge retrieved"]

        summaries = []
        for doc in retrieved_docs:
            metadata = doc.get('metadata', {})
            category = metadata.get('category', 'unknown')
            topic = metadata.get('topic', 'unknown')
            relevance = doc.get('relevance_score', 0.0)
            
            summaries.append(
                f"{category.capitalize()}: {topic} (relevance: {relevance:.1%})"
            )

        return summaries
