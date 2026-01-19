"""
Retriever Tool - Hybrid RAG retriever with reranking support

Two-stage retrieval:
1. Recall stage: FAISS (vector) + BM25 (keyword) hybrid search
2. Rerank stage: Cross-encoder reranking for improved precision
"""

import hashlib
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.tools import Tool
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from src.ingest.indexer import BM25Index

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import reranker
try:
    from src.tools.reranker import CrossEncoderReranker, create_reranker
    RERANKER_AVAILABLE = True
except ImportError as e:
    RERANKER_AVAILABLE = False
    logger.warning(f"Reranker module not available: {e}. Reranking disabled.")


def _get_stable_doc_key(doc: Document) -> str:
    """
    Generate a stable document key for deduplication.
    
    Uses metadata fields (source_file, page, chunk_id) if available,
    otherwise falls back to hash of (source_file + page + content_prefix).
    
    Args:
        doc: Document object
        
    Returns:
        Stable string key
    """
    metadata = doc.metadata
    
    # Try to use chunk_id if available
    if 'chunk_id' in metadata:
        return f"{metadata.get('source_file', 'unknown')}:{metadata.get('page', 0)}:{metadata['chunk_id']}"
    
    # Use source_file + page
    source_file = metadata.get('source_file', 'unknown')
    page = metadata.get('page', 0)
    
    # Add content hash for uniqueness (first 120 chars)
    content_prefix = doc.page_content[:120] if doc.page_content else ""
    content_hash = hashlib.md5(content_prefix.encode()).hexdigest()[:8]
    
    return f"{source_file}:{page}:{content_hash}"


class HybridRetriever:
    """
    Hybrid retriever with two-stage retrieval:
    1. Recall: FAISS (vector) + BM25 (keyword) hybrid search
    2. Rerank: Cross-encoder reranking (optional)
    """
    
    def __init__(
        self,
        vectorstore: FAISS,
        bm25_index: BM25Index,
        vector_weight: float = 0.65,
        bm25_weight: float = 0.35,
        top_k: int = 4,
        reranker: Optional[CrossEncoderReranker] = None,
        top_n_candidates: Optional[int] = None
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            vectorstore: FAISS vector store
            bm25_index: BM25 keyword index
            vector_weight: Weight for vector search scores
            bm25_weight: Weight for BM25 scores
            top_k: Final number of documents to return
            reranker: Optional reranker instance
            top_n_candidates: Number of candidates for reranking (default: top_k * 8)
        """
        self.vectorstore = vectorstore
        self.bm25_index = bm25_index
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.top_k = top_k
        self.reranker = reranker
        self.top_n_candidates = top_n_candidates or (top_k * 8)
        
        # Timing statistics
        self.last_recall_time = 0.0
        self.last_rerank_time = 0.0
    
    def search(
        self,
        query: str,
        return_timing: bool = False
    ) -> List[Document] | Tuple[List[Document], Dict[str, float]]:
        """
        Execute two-stage hybrid retrieval with optional reranking.
        
        Stage 1 (Recall): Hybrid search (FAISS + BM25) with fusion
        Stage 2 (Rerank): Cross-encoder reranking on top candidates
        
        Args:
            query: Query text
            return_timing: If True, return timing information
            
        Returns:
            List of top-k documents, optionally with timing dict
        """
        recall_start = time.time()
        
        # Stage 1: Recall - Hybrid search
        # Get more candidates than final top_k for reranking
        recall_k = max(self.top_n_candidates, self.top_k * 4)
        
        # 1. Vector search (FAISS)
        vector_results = self.vectorstore.similarity_search_with_score(
            query,
            k=recall_k
        )
        
        # 2. BM25 keyword search
        bm25_results = self.bm25_index.search(query, top_k=recall_k)
        
        # 3. Fusion: Normalize and combine scores
        doc_scores: Dict[str, Tuple[Document, float]] = {}
        
        # Normalize vector scores
        if vector_results:
            max_vector_score = max(score for _, score in vector_results)
            min_vector_score = min(score for _, score in vector_results)
            vector_range = max_vector_score - min_vector_score
            
            for doc, score in vector_results:
                # FAISS distance: lower is better, invert for normalization
                normalized_score = 1 - (score - min_vector_score) / (vector_range + 1e-10)
                doc_key = _get_stable_doc_key(doc)
                
                if doc_key not in doc_scores:
                    doc_scores[doc_key] = (doc, 0.0)
                
                current_doc, current_score = doc_scores[doc_key]
                doc_scores[doc_key] = (
                    current_doc,
                    current_score + normalized_score * self.vector_weight
                )
        
        # Normalize BM25 scores
        if bm25_results:
            max_bm25_score = max(score for _, score in bm25_results) if bm25_results else 1.0
            
            for doc, score in bm25_results:
                normalized_score = score / (max_bm25_score + 1e-10)
                doc_key = _get_stable_doc_key(doc)
                
                if doc_key not in doc_scores:
                    doc_scores[doc_key] = (doc, 0.0)
                
                current_doc, current_score = doc_scores[doc_key]
                doc_scores[doc_key] = (
                    current_doc,
                    current_score + normalized_score * self.bm25_weight
                )
        
        # Sort by fused score
        sorted_candidates = sorted(
            doc_scores.values(),
            key=lambda x: x[1],
            reverse=True
        )
        
        recall_time = time.time() - recall_start
        self.last_recall_time = recall_time
        
        # Extract documents from candidates
        candidate_docs = [doc for doc, _ in sorted_candidates]
        
        # Stage 2: Reranking (if enabled)
        rerank_start = time.time()
        
        if self.reranker is not None and len(candidate_docs) > self.top_k:
            # Take top_n_candidates for reranking
            rerank_candidates = candidate_docs[:self.top_n_candidates]
            
            try:
                # Rerank and get top_k
                reranked_docs = self.reranker.rerank(
                    query=query,
                    documents=rerank_candidates,
                    top_k=self.top_k
                )
                rerank_time = time.time() - rerank_start
                self.last_rerank_time = rerank_time
                
                logger.info(
                    f"Reranking: {len(rerank_candidates)} candidates -> {len(reranked_docs)} results "
                    f"(recall: {recall_time:.3f}s, rerank: {rerank_time:.3f}s)"
                )
                
                final_docs = reranked_docs
            except Exception as e:
                logger.warning(f"Reranking failed: {e}. Falling back to fused ranking.")
                final_docs = candidate_docs[:self.top_k]
                self.last_rerank_time = 0.0
        else:
            # No reranking: return top_k from fused results
            final_docs = candidate_docs[:self.top_k]
            self.last_rerank_time = 0.0
        
        if return_timing:
            timing = {
                'recall_time': self.last_recall_time,
                'rerank_time': self.last_rerank_time,
                'total_time': self.last_recall_time + self.last_rerank_time
            }
            return final_docs, timing
        
        return final_docs
    
    def format_results(self, documents: List[Document]) -> str:
        """
        Format retrieval results.
        
        Args:
            documents: List of documents
            
        Returns:
            Formatted string
        """
        if not documents:
            return "未找到相关内容。"
        
        result_parts = []
        result_parts.append(f"找到 {len(documents)} 个相关段落：\n")
        
        for i, doc in enumerate(documents, 1):
            source_file = doc.metadata.get('source_file', 'Unknown')
            page = doc.metadata.get('page', 'N/A')
            content = doc.page_content.strip()
            
            result_parts.append(f"[{i}] 来源: {source_file}")
            if page != 'N/A':
                result_parts.append(f" (第 {page + 1} 页)")
            result_parts.append(f"\n内容: {content}\n")
        
        return "\n".join(result_parts)


def create_retriever_tool(
    vectorstore: FAISS,
    bm25_index: BM25Index,
    config: Dict[str, Any]
) -> Tool:
    """
    Create retriever tool with optional reranking.
    
    Args:
        vectorstore: FAISS vector store
        bm25_index: BM25 keyword index
        config: Configuration dictionary
        
    Returns:
        LangChain Tool object
    """
    retriever_config = config.get('retriever', {})
    hybrid_config = retriever_config.get('hybrid', {})
    rerank_config = retriever_config.get('rerank', {})
    
    # Create reranker if enabled
    reranker = None
    if RERANKER_AVAILABLE and rerank_config.get('enabled', False):
        try:
            reranker = create_reranker(rerank_config)
            if reranker:
                logger.info("Reranker enabled and loaded successfully")
            else:
                logger.info("Reranker disabled (model load failed)")
        except Exception as e:
            logger.warning(f"Failed to initialize reranker: {e}. Continuing without reranking.")
    
    # Create hybrid retriever
    retriever = HybridRetriever(
        vectorstore=vectorstore,
        bm25_index=bm25_index,
        vector_weight=hybrid_config.get('vector_weight', 0.65),
        bm25_weight=hybrid_config.get('bm25_weight', 0.35),
        top_k=retriever_config.get('top_k', 4),
        reranker=reranker,
        top_n_candidates=rerank_config.get('top_n_candidates', None)
    )
    
    def retriever_func(query: str) -> str:
        """
        Retriever function.
        
        Args:
            query: Query text
            
        Returns:
            Formatted retrieval results
        """
        documents = retriever.search(query)
        return retriever.format_results(documents)
    
    return Tool(
        name="retriever",
        description=(
            "Retrieve relevant passages from local knowledge base (PDF/TXT/Markdown). "
            "Input should be a natural language query about concepts, definitions, theories, "
            "or literature content. Returns passages with source file names and page numbers."
        ),
        func=retriever_func
    )
