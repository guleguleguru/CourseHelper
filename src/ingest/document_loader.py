"""
文档加载器 - 支持 PDF、TXT、Markdown
"""

from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_documents(
    knowledge_base_path: str = "knowledge_base",
    chunk_size: int = 800,
    chunk_overlap: int = 120
) -> List[Document]:
    """
    从知识库目录加载所有文档并分块
    
    Args:
        knowledge_base_path: 知识库目录路径
        chunk_size: 分块大小
        chunk_overlap: 分块重叠大小
        
    Returns:
        文档分块列表
    """
    kb_path = Path(knowledge_base_path)
    if not kb_path.exists():
        raise FileNotFoundError(f"知识库目录不存在: {kb_path}")
    
    documents = []
    
    # 支持的文件类型
    file_loaders = {
        '.pdf': PyPDFLoader,
        '.txt': TextLoader,
        '.md': TextLoader,
        '.markdown': TextLoader,
    }
    
    print(f"Scanning knowledge base: {kb_path}")
    
    # 遍历所有文件
    for file_path in kb_path.rglob('*'):
        if file_path.is_file():
            suffix = file_path.suffix.lower()
            
            if suffix in file_loaders:
                try:
                    print(f"  Loading file: {file_path.name}")
                    loader_class = file_loaders[suffix]
                    
                    if suffix == '.pdf':
                        loader = loader_class(str(file_path))
                    else:
                        loader = loader_class(str(file_path), encoding='utf-8')
                    
                    docs = loader.load()
                    
                    # 为每个文档添加元数据
                    for doc in docs:
                        doc.metadata['source_file'] = file_path.name
                        doc.metadata['file_type'] = suffix
                    
                    documents.extend(docs)
                    
                except Exception as e:
                    print(f"    [WARNING] Loading failed: {e}")
                    continue
    
    if not documents:
        print("[WARNING] No documents found!")
        return []
    
    print(f"\nTotal loaded: {len(documents)} document segments")
    
    # 文本分块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )
    
    print("Splitting text into chunks...")
    chunks = text_splitter.split_documents(documents)
    
    print(f"Chunking completed: {len(chunks)} text chunks created\n")
    
    return chunks


def extract_page_number(doc: Document) -> int:
    """
    从文档元数据中提取页码
    
    Args:
        doc: 文档对象
        
    Returns:
        页码（如果有），否则返回 0
    """
    if 'page' in doc.metadata:
        return doc.metadata['page']
    return 0

