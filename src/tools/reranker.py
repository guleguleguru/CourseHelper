"""
Reranker Module - Cross-encoder reranking for improved retrieval precision

This module provides reranking capabilities using cross-encoder models
to improve the relevance of retrieved documents.
"""

import hashlib
import logging
from typing import List, Optional
from langchain_core.documents import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import cross-encoder dependencies
try:
    from sentence_transformers import CrossEncoder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    try:
        from transformers import pipeline
        TRANSFORMERS_AVAILABLE = True
    except ImportError:
        TRANSFORMERS_AVAILABLE = False


class CrossEncoderReranker:
    """
    Cross-encoder reranker for improving retrieval precision.
    
    Uses a cross-encoder model to score query-document pairs,
    providing more accurate relevance ranking than first-stage retrieval.
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: str = "auto",
        batch_size: int = 32
    ):
        """
        Initialize the cross-encoder reranker.
        
        Args:
            model_name: HuggingFace model name for reranking
            device: Device to use ("cpu", "cuda", or "auto")
            batch_size: Batch size for scoring
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = None
        self.model_transformer = None
        self.tokenizer = None
        self.use_transformers = False
        self.device = self._determine_device(device)
        
        try:
            self._load_model()
        except Exception as e:
            logger.warning(f"Failed to load reranker model {model_name}: {e}")
            logger.warning("Reranking will be disabled. Install sentence-transformers or transformers to enable.")
            self.model = None
    
    def _determine_device(self, device: str) -> str:
        """Determine the device to use."""
        if device == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return device
    
    def _load_model(self):
        """Load the cross-encoder model."""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.info(f"Loading cross-encoder model: {self.model_name}")
            self.model = CrossEncoder(
                self.model_name,
                device=self.device,
                max_length=512
            )
            logger.info("Cross-encoder model loaded successfully")
        elif TRANSFORMERS_AVAILABLE:
            logger.info(f"Loading reranker via transformers: {self.model_name}")
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                import torch
                
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model_transformer = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                if self.device == "cuda" and torch.cuda.is_available():
                    self.model_transformer = self.model_transformer.cuda()
                self.model_transformer.eval()
                self.use_transformers = True
                logger.warning("Using transformers directly (slower). Consider installing sentence-transformers.")
            except Exception as e:
                logger.error(f"Failed to load model via transformers: {e}")
                raise
        else:
            raise ImportError(
                "Neither sentence-transformers nor transformers is available. "
                "Install one of them to enable reranking: "
                "pip install sentence-transformers"
            )
    
    def score(
        self,
        query: str,
        documents: List[Document]
    ) -> List[float]:
        """
        Score query-document pairs.
        
        Args:
            query: Query text
            documents: List of documents to score
            
        Returns:
            List of relevance scores (higher is better)
        """
        if self.model is None and not self.use_transformers:
            raise RuntimeError("Reranker model not loaded. Cannot score documents.")
        
        if not documents:
            return []
        
        # Prepare pairs: (query, document_content)
        pairs = [
            [query, doc.page_content[:512]]  # Limit content length
            for doc in documents
        ]
        
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                # Use CrossEncoder.predict() for batch scoring
                scores = self.model.predict(
                    pairs,
                    batch_size=self.batch_size,
                    show_progress_bar=False
                )
                # Convert to list if needed
                if hasattr(scores, 'tolist'):
                    scores = scores.tolist()
                return scores
            elif hasattr(self, 'use_transformers') and self.use_transformers:
                # Use transformers directly
                import torch
                scores = []
                
                # Process in batches
                for i in range(0, len(pairs), self.batch_size):
                    batch_pairs = pairs[i:i + self.batch_size]
                    
                    # Tokenize pairs: format depends on model
                    # For BGE reranker: use query and passage as separate arguments
                    inputs = self.tokenizer(
                        [p[0] for p in batch_pairs],  # queries
                        [p[1] for p in batch_pairs],  # passages
                        padding=True,
                        truncation=True,
                        max_length=512,
                        return_tensors="pt"
                    )
                    
                    if self.device == "cuda" and torch.cuda.is_available():
                        inputs = {k: v.cuda() for k, v in inputs.items()}
                    
                    # Score
                    with torch.no_grad():
                        outputs = self.model_transformer(**inputs)
                        # Extract scores (logits -> probabilities)
                        if outputs.logits.dim() > 1:
                            batch_scores = torch.sigmoid(outputs.logits).squeeze(-1).cpu().tolist()
                        else:
                            batch_scores = torch.sigmoid(outputs.logits).squeeze().cpu().tolist()
                    
                    if isinstance(batch_scores, float):
                        batch_scores = [batch_scores]
                    scores.extend(batch_scores)
                
                return scores
            else:
                # Fallback: return uniform scores
                logger.warning("Reranker model not properly initialized. Returning uniform scores.")
                return [0.5] * len(documents)
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Return uniform scores as fallback
            return [0.5] * len(documents)
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int
    ) -> List[Document]:
        """
        Rerank documents and return top-k.
        
        Args:
            query: Query text
            documents: List of candidate documents
            top_k: Number of documents to return
            
        Returns:
            Top-k reranked documents
        """
        if (self.model is None and not self.use_transformers) or not documents:
            # Fallback: return original order
            return documents[:top_k]
        
        # Score all documents
        scores = self.score(query, documents)
        
        # Sort by score (descending)
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        return [doc for doc, _ in scored_docs[:top_k]]


class LLMReranker:
    """
    Fallback LLM-based reranker.
    
    Uses LLM to score documents when cross-encoder is not available.
    This is a simple fallback and should be used sparingly.
    """
    
    def __init__(self, llm=None):
        """
        Initialize LLM reranker.
        
        Args:
            llm: LangChain LLM instance (optional)
        """
        self.llm = llm
        if llm is None:
            logger.warning("LLM reranker initialized without LLM. Reranking disabled.")
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int
    ) -> List[Document]:
        """
        Rerank documents using LLM.
        
        This is a simple implementation that asks LLM to rank documents.
        For production, consider more sophisticated approaches.
        """
        if self.llm is None or not documents:
            return documents[:top_k]
        
        # Simple approach: ask LLM to select most relevant
        # For better performance, use structured output or few-shot examples
        try:
            doc_texts = [
                f"[{i}] {doc.page_content[:200]}..." 
                for i, doc in enumerate(documents[:10])  # Limit to 10 for LLM
            ]
            
            prompt = f"""Given the query: "{query}"

Rank these documents by relevance (most relevant first):
{chr(10).join(doc_texts)}

Return only the numbers in order of relevance, separated by commas (e.g., 3,1,5,2,4):"""
            
            response = self.llm.invoke(prompt)
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Parse response (simple extraction)
            try:
                indices = [int(x.strip()) for x in content.split(',')[:top_k]]
                reranked = [documents[i] for i in indices if 0 <= i < len(documents)]
                return reranked[:top_k] if reranked else documents[:top_k]
            except (ValueError, IndexError):
                logger.warning("Failed to parse LLM reranking response. Using original order.")
                return documents[:top_k]
        except Exception as e:
            logger.error(f"LLM reranking failed: {e}")
            return documents[:top_k]


def create_reranker(config: dict) -> Optional[CrossEncoderReranker]:
    """
    Create a reranker instance from config.
    
    Args:
        config: Reranker configuration dictionary
        
    Returns:
        Reranker instance or None if disabled/failed
    """
    if not config.get('enabled', False):
        return None
    
    try:
        reranker = CrossEncoderReranker(
            model_name=config.get('model_name', 'BAAI/bge-reranker-base'),
            device=config.get('device', 'auto'),
            batch_size=config.get('batch_size', 32)
        )
        
        if reranker.model is None:
            logger.warning("Reranker model failed to load. Reranking disabled.")
            return None
        
        return reranker
    except Exception as e:
        logger.warning(f"Failed to create reranker: {e}. Reranking disabled.")
        return None

