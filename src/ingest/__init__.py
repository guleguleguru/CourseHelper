"""
文档摄入和索引构建模块
"""

from .document_loader import load_documents
from .indexer import build_indexes

__all__ = ['load_documents', 'build_indexes']



