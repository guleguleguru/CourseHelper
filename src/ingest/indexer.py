"""
索引构建器 - FAISS 向量索引 + BM25 关键词索引
"""

import pickle
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi
import jieba


class BM25Index:
    """BM25 关键词索引"""
    
    def __init__(self, documents: List[Document]):
        """
        初始化 BM25 索引
        
        Args:
            documents: 文档列表
        """
        self.documents = documents
        
        # 对每个文档进行分词
        tokenized_corpus = []
        for doc in documents:
            # 混合中英文分词
            tokens = self._tokenize(doc.page_content)
            tokenized_corpus.append(tokens)
        
        # 构建 BM25 索引
        self.bm25 = BM25Okapi(tokenized_corpus)
    
    def _tokenize(self, text: str) -> List[str]:
        """
        对文本进行分词（支持中英文）
        
        Args:
            text: 输入文本
            
        Returns:
            分词列表
        """
        # 使用 jieba 分词（对中文友好，对英文也能处理）
        tokens = list(jieba.cut_for_search(text.lower()))
        return tokens
    
    def search(self, query: str, top_k: int = 5) -> List[tuple]:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回前 k 个结果
            
        Returns:
            (Document, score) 列表
        """
        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        
        # 获取 top_k 的索引
        top_indices = sorted(
            range(len(scores)), 
            key=lambda i: scores[i], 
            reverse=True
        )[:top_k]
        
        results = [(self.documents[i], scores[i]) for i in top_indices]
        return results


def build_indexes(
    documents: List[Document],
    embedding_model: str = "text-embedding-3-small",
    output_dir: str = "outputs"
) -> tuple:
    """
    构建向量索引和关键词索引
    
    Args:
        documents: 文档分块列表
        embedding_model: OpenAI 嵌入模型名称
        output_dir: 输出目录
        
    Returns:
        (FAISS 索引, BM25 索引)
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Starting index building...")
    print("=" * 60)
    
    # 1. 构建 FAISS 向量索引
    print("\n[1/2] Building FAISS vector index...")
    print(f"  Using embedding model: {embedding_model}")
    
    embeddings = OpenAIEmbeddings(model=embedding_model)
    
    # 创建 FAISS 索引
    vectorstore = FAISS.from_documents(documents, embeddings)
    
    # 保存向量索引
    faiss_path = output_path / "faiss_index"
    vectorstore.save_local(str(faiss_path))
    print(f"  [OK] FAISS index saved to: {faiss_path}")
    
    # 2. 构建 BM25 关键词索引
    print("\n[2/2] Building BM25 keyword index...")
    bm25_index = BM25Index(documents)
    
    # 保存 BM25 索引
    bm25_path = output_path / "bm25_index.pkl"
    with open(bm25_path, 'wb') as f:
        pickle.dump(bm25_index, f)
    print(f"  [OK] BM25 index saved to: {bm25_path}")
    
    print("\n" + "=" * 60)
    print("[COMPLETED] Index building finished!")
    print("=" * 60)
    
    return vectorstore, bm25_index


def load_indexes(
    embedding_model: str = "text-embedding-3-small",
    index_dir: str = "outputs"
) -> tuple:
    """
    加载已保存的索引
    
    Args:
        embedding_model: OpenAI 嵌入模型名称
        index_dir: 索引目录
        
    Returns:
        (FAISS 索引, BM25 索引)
        
    Raises:
        FileNotFoundError: 如果索引文件不存在
    """
    index_path = Path(index_dir)
    
    # 加载 FAISS 索引
    faiss_path = index_path / "faiss_index"
    if not faiss_path.exists():
        raise FileNotFoundError(f"FAISS 索引不存在: {faiss_path}")
    
    embeddings = OpenAIEmbeddings(model=embedding_model)
    vectorstore = FAISS.load_local(
        str(faiss_path), 
        embeddings,
        allow_dangerous_deserialization=True
    )
    
    # 加载 BM25 索引
    bm25_path = index_path / "bm25_index.pkl"
    if not bm25_path.exists():
        raise FileNotFoundError(f"BM25 索引不存在: {bm25_path}")
    
    with open(bm25_path, 'rb') as f:
        bm25_index = pickle.load(f)
    
    return vectorstore, bm25_index

