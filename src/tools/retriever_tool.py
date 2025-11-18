"""
Retriever Tool - 混合检索工具（FAISS + BM25）
"""

from typing import List, Dict, Any
from langchain_core.tools import Tool
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from src.ingest.indexer import BM25Index


class HybridRetriever:
    """混合检索器（向量检索 + 关键词检索）"""
    
    def __init__(
        self,
        vectorstore: FAISS,
        bm25_index: BM25Index,
        vector_weight: float = 0.65,
        bm25_weight: float = 0.35,
        top_k: int = 4
    ):
        """
        初始化混合检索器
        
        Args:
            vectorstore: FAISS 向量存储
            bm25_index: BM25 索引
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重
            top_k: 返回前 k 个结果
        """
        self.vectorstore = vectorstore
        self.bm25_index = bm25_index
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.top_k = top_k
    
    def search(self, query: str) -> List[Document]:
        """
        执行混合检索
        
        Args:
            query: 查询文本
            
        Returns:
            相关文档列表
        """
        # 1. 向量检索
        vector_results = self.vectorstore.similarity_search_with_score(
            query, 
            k=self.top_k * 2  # 获取更多候选
        )
        
        # 2. BM25 检索
        bm25_results = self.bm25_index.search(query, top_k=self.top_k * 2)
        
        # 3. 融合分数（归一化 + 加权）
        doc_scores: Dict[str, tuple] = {}  # {doc_id: (Document, score)}
        
        # 归一化向量检索分数
        if vector_results:
            max_vector_score = max(score for _, score in vector_results)
            min_vector_score = min(score for _, score in vector_results)
            vector_range = max_vector_score - min_vector_score
            
            for doc, score in vector_results:
                # FAISS 距离越小越好，需要反转
                normalized_score = 1 - (score - min_vector_score) / (vector_range + 1e-10)
                doc_id = id(doc)
                
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = (doc, 0.0)
                
                current_doc, current_score = doc_scores[doc_id]
                doc_scores[doc_id] = (
                    doc, 
                    current_score + normalized_score * self.vector_weight
                )
        
        # 归一化 BM25 分数
        if bm25_results:
            max_bm25_score = max(score for _, score in bm25_results)
            
            for doc, score in bm25_results:
                normalized_score = score / (max_bm25_score + 1e-10)
                doc_id = id(doc)
                
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = (doc, 0.0)
                
                current_doc, current_score = doc_scores[doc_id]
                doc_scores[doc_id] = (
                    doc,
                    current_score + normalized_score * self.bm25_weight
                )
        
        # 4. 按融合分数排序
        sorted_docs = sorted(
            doc_scores.values(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 返回前 top_k 个文档
        return [doc for doc, _ in sorted_docs[:self.top_k]]
    
    def format_results(self, documents: List[Document]) -> str:
        """
        格式化检索结果
        
        Args:
            documents: 文档列表
            
        Returns:
            格式化的字符串
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
    创建检索工具
    
    Args:
        vectorstore: FAISS 向量存储
        bm25_index: BM25 索引
        config: 配置字典
        
    Returns:
        LangChain Tool 对象
    """
    retriever_config = config.get('retriever', {})
    hybrid_config = retriever_config.get('hybrid', {})
    
    retriever = HybridRetriever(
        vectorstore=vectorstore,
        bm25_index=bm25_index,
        vector_weight=hybrid_config.get('vector_weight', 0.65),
        bm25_weight=hybrid_config.get('bm25_weight', 0.35),
        top_k=retriever_config.get('top_k', 4)
    )
    
    def retriever_func(query: str) -> str:
        """
        检索函数
        
        Args:
            query: 查询文本
            
        Returns:
            检索结果
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

