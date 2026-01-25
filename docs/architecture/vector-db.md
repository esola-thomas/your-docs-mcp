---
title: Vector Database Integration
tags: [architecture, vector, search, chromadb, embeddings, semantic]
category: Architecture
order: 3
---

# Vector Database Integration

The documentation server uses ChromaDB for semantic search, enabling AI assistants to find relevant documentation even when queries don't match exact keywords.

## Overview

Traditional keyword search fails when:
- Users describe concepts instead of using exact terms
- Documentation uses different terminology than the query
- Related documents don't share common words

Semantic search solves this by understanding the *meaning* of queries and documents.

## Architecture

```text
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Document   │────▶│ Sentence         │────▶│  ChromaDB   │
│  Content    │     │ Transformer      │     │  Collection │
└─────────────┘     └──────────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  Embedding  │
                    │  Vector     │
                    │  [384 dims] │
                    └─────────────┘
```

## Components

### Embedding Model

Uses `all-MiniLM-L6-v2` from Sentence Transformers:
- 384-dimensional vectors
- Optimized for semantic similarity
- Fast inference on CPU

### Vector Store

ChromaDB provides:
- In-memory storage (ephemeral mode)
- Cosine similarity search
- Metadata filtering

### Indexing Strategy

Documents are indexed with:
- Title text
- First 2000 characters of content
- Metadata (tags, category, URI)

## Hybrid Search

The search combines two approaches:

### 1. Keyword Search
- Exact and partial word matching
- Fast for known terms
- High precision

### 2. Semantic Search
- Vector similarity comparison
- Understands synonyms and concepts
- High recall

### Score Combination

```python
# If both methods match, boost the score
if keyword_match and semantic_match:
    final_score = max(keyword_score, semantic_score) + 0.3
else:
    final_score = keyword_score or semantic_score
```

## Configuration

The vector store is configured in the services layer:

```python
from chromadb import Client
from chromadb.utils import embedding_functions

# Create embedding function
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Create ephemeral client (in-memory)
client = Client()
collection = client.create_collection(
    name="documentation",
    embedding_function=embedding_fn
)
```

## Search Flow

1. **Query Processing**
   ```python
   query = "how to authenticate with the API"
   ```

2. **Embedding Generation**
   ```python
   # Query is converted to vector
   query_vector = embedding_fn([query])
   ```

3. **Similarity Search**
   ```python
   results = collection.query(
       query_embeddings=query_vector,
       n_results=10
   )
   ```

4. **Result Ranking**
   ```python
   # Combine with keyword search results
   # Apply score boosting
   # Return ranked results
   ```

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Index time per document | ~50ms |
| Query time (semantic) | ~20ms |
| Memory per document | ~3KB |
| Model load time | ~2s (first query) |

## Limitations

### Ephemeral Storage
Currently, the vector store is ephemeral:
- Data is lost on server restart
- Index is rebuilt on each startup
- No persistence to disk

### CPU-Only
The embedding model runs on CPU:
- Works on any machine without GPU
- Sufficient for documentation search
- No CUDA/GPU acceleration needed

## Graceful Degradation

If the vector store fails:
1. Server continues with keyword search only
2. Warning logged for debugging
3. No impact on other functionality

```python
try:
    semantic_results = vector_store.search(query)
except Exception:
    logger.warning("Vector search failed, using keyword only")
    semantic_results = []
```

## Example Queries

| Query | Keyword Match | Semantic Match |
|-------|---------------|----------------|
| "authentication" | API auth docs | Login, OAuth, JWT docs |
| "how to set up" | Setup guides | Installation, config docs |
| "find errors" | Error reference | Debugging, troubleshooting |

## Next Steps

- [Architecture Overview](overview.md) - System architecture
- [MCP Protocol](mcp-protocol.md) - Protocol integration
- [Search Documentation](../guides/getting-started.md) - Using search
