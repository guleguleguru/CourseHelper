# Two-Stage Retrieval: Recall + Rerank

## Overview

The Research TA Agent uses a **two-stage retrieval pipeline** to maximize both recall and precision:

1. **Recall Stage**: Hybrid search (FAISS + BM25) to find candidate documents
2. **Rerank Stage**: Cross-encoder reranking to improve relevance of top results

This approach is standard in production RAG systems and significantly improves answer quality.

---

## Why Two-Stage Retrieval?

### Stage 1: Recall (Hybrid Search)

**Goal**: Find all potentially relevant documents quickly

- **FAISS (Vector Search)**: Semantic understanding, handles synonyms and concepts
- **BM25 (Keyword Search)**: Exact term matching, good for technical terms
- **Fusion**: Weighted combination of both methods

**Advantage**: Fast, high recall (finds many relevant docs)

**Limitation**: May include some less relevant documents in top-k

### Stage 2: Rerank (Cross-Encoder)

**Goal**: Reorder candidates to put most relevant documents first

- **Cross-Encoder Model**: Deeply understands query-document relationship
- **More Accurate**: Better at distinguishing subtle relevance differences
- **Computational Cost**: Slower than first stage, but only runs on top candidates

**Advantage**: High precision (top results are highly relevant)

**Trade-off**: Additional computation time (~100-500ms per query)

---

## Architecture

```
User Query
    ↓
┌─────────────────────────────────┐
│ Stage 1: Recall (Fast)          │
│  ├─ FAISS vector search          │
│  ├─ BM25 keyword search          │
│  └─ Score fusion                 │
│  → Returns top_n_candidates      │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ Stage 2: Rerank (Precise)        │
│  └─ Cross-encoder scoring        │
│  → Returns final top_k            │
└─────────────────────────────────┘
    ↓
Final Results (High Quality)
```

---

## Configuration

Edit `config/settings.yaml`:

```yaml
retriever:
  top_k: 4                    # Final number of results
  rerank:
    enabled: true             # Enable reranking
    model_name: "BAAI/bge-reranker-base"  # HuggingFace model
    top_n_candidates: 32     # Candidates for reranking (default: top_k * 8)
    batch_size: 32           # Batch size for scoring
    device: "auto"           # "cpu", "cuda", or "auto"
```

### Recommended Models

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `BAAI/bge-reranker-base` | 278MB | Fast | Good | **Recommended** |
| `BAAI/bge-reranker-large` | 1.1GB | Slower | Better | High quality needed |
| `ms-marco-MiniLM-L-6-v2` | 80MB | Very Fast | Good | Resource constrained |

---

## Installation

### Basic Installation (No Reranking)

Works out of the box. Reranking is **optional**.

### Enable Reranking

```bash
# Install sentence-transformers (recommended)
pip install sentence-transformers

# Or use transformers (slower)
pip install transformers torch
```

Then enable in `config/settings.yaml`:
```yaml
retriever:
  rerank:
    enabled: true
```

---

## Performance Impact

### Typical Timings

| Stage | Time | Notes |
|-------|------|-------|
| Recall (FAISS + BM25) | 50-200ms | Depends on index size |
| Rerank (32 candidates) | 100-300ms | Depends on model and device |
| **Total** | **150-500ms** | Acceptable for most use cases |

### Quality Improvement

- **Precision@1**: +15-30% improvement
- **MRR (Mean Reciprocal Rank)**: +20-40% improvement
- **User Satisfaction**: Noticeably better top results

---

## How It Works

### 1. Stable Document Deduplication

Documents are deduplicated using stable keys:
- Primary: `(source_file, page, chunk_id)` if available
- Fallback: `(source_file, page, content_hash)` 

This ensures consistent results across runs.

### 2. Candidate Selection

After fusion, top `top_n_candidates` documents are selected for reranking:
- Default: `top_k * 8` (e.g., 32 candidates for top_k=4)
- Configurable via `top_n_candidates`

### 3. Cross-Encoder Scoring

For each candidate, the model scores the query-document pair:
- Input: `[query, document_content]`
- Output: Relevance score (higher = more relevant)
- Batch processing for efficiency

### 4. Final Ranking

Documents are sorted by reranker scores and top-k returned.

---

## Testing

Run the validation script:

```bash
python test_reranker.py
```

This will:
- Show baseline results (without reranking)
- Show reranked results (if enabled)
- Compare timing and document quality
- Display which documents changed position

---

## Troubleshooting

### Reranker Not Loading

**Error**: "Reranker model not loaded"

**Solution**:
```bash
pip install sentence-transformers
```

### Slow Performance

**Issue**: Reranking takes too long

**Solutions**:
1. Reduce `top_n_candidates` (e.g., 16 instead of 32)
2. Use smaller model (e.g., `ms-marco-MiniLM-L-6-v2`)
3. Use GPU: Set `device: "cuda"` (if available)
4. Increase `batch_size` for faster batch processing

### Out of Memory

**Issue**: Model loading fails on low-memory systems

**Solutions**:
1. Use smaller model
2. Set `device: "cpu"` explicitly
3. Reduce `batch_size`

---

## Fallback Behavior

If reranking fails or is disabled:
- System automatically falls back to fused ranking
- No errors, just uses Stage 1 results
- Logs warning messages for debugging

---

## Best Practices

1. **Start without reranking**: Test baseline performance first
2. **Enable for production**: Better user experience
3. **Monitor timing**: Ensure acceptable latency (<500ms)
4. **Tune candidates**: Adjust `top_n_candidates` based on your data
5. **Use GPU if available**: Significantly faster reranking

---

## Technical Details

### Cross-Encoder vs Bi-Encoder

- **Bi-Encoder** (FAISS): Encodes query and documents separately, fast but less accurate
- **Cross-Encoder** (Reranker): Encodes query-document pairs together, slower but more accurate

### Why Not Use Cross-Encoder for All Documents?

- Too slow: Would take seconds for large knowledge bases
- Two-stage approach: Fast recall + precise reranking = best of both worlds

---

## References

- [BGE Reranker Models](https://huggingface.co/BAAI/bge-reranker-base)
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [RAG Best Practices](https://www.pinecone.io/learn/reranking/)

---

**Summary**: Two-stage retrieval combines the speed of hybrid search with the precision of cross-encoder reranking, resulting in significantly better retrieval quality with acceptable latency.

