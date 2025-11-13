---
title: Performance Optimization
tags: [advanced, performance, optimization, caching, tuning]
category: "Guides"
order: 10
---

# Performance Optimization

Learn how to optimize the Hierarchical Documentation MCP server for better performance.

## Caching Strategies

The server uses intelligent caching to improve response times.

### Cache Configuration

```bash
# Increase cache TTL for static documentation
export MCP_DOCS_CACHE_TTL=7200  # 2 hours

# Allocate more memory for cache
export MCP_DOCS_MAX_CACHE_MB=1000  # 1 GB
```

## When to Clear Cache

The server automatically invalidates cache when files change. Manual clearing is rarely needed, but you can restart the server to clear all caches.

## File Organization

Organize files for optimal performance:

### Best Practices

1. **Keep directories shallow**: Avoid deeply nested structures (max 3-4 levels)
2. **Use consistent naming**: Makes files easier to cache and find
3. **Group related content**: Put related documents in the same category
4. **Limit file size**: Break large documents into smaller, focused pages

### Example Structure

```text
docs/
├── guides/           # Good: organized by type
│   ├── getting-started.md
│   └── advanced.md
├── api/
│   └── reference.md
└── tutorials/
    └── first-steps.md
```

## Search Performance

### Indexing

The server builds search indexes on startup. For large documentation sets:

```bash
# Limit search results to improve response time
export MCP_DOCS_SEARCH_LIMIT=10
```

## Optimize Search Queries

- Use specific terms instead of generic words
- Use tags and categories to filter results
- Leverage metadata search when possible

## Memory Management

### Monitor Memory Usage

For large documentation sets, monitor memory usage:

```bash
# Set maximum cache size based on available RAM
export MCP_DOCS_MAX_CACHE_MB=500

# Enable audit logging to track memory patterns
export MCP_DOCS_AUDIT_LOG=true
```

## Reduce Memory Footprint

1. **Exclude unnecessary files**: Use exclude patterns in config
2. **Disable file watching**: Set `watch_files: false` for static docs
3. **Limit cache size**: Reduce `max_cache_mb` if needed

## File Watching

The server watches for file changes by default. For static documentation:

```yaml
# In .mcp-docs.yaml
watch_files: false  # Disable for better performance on static docs
```

## Benchmarking

### Measure Query Performance

Track common query times:

```bash
# Enable DEBUG logging
export LOG_LEVEL=DEBUG

# Monitor response times in logs
hierarchical-docs-mcp
```

## Performance Metrics

Key metrics to monitor:
- **File scan time**: Should be < 1s for 1000 files
- **Search query time**: Should be < 100ms
- **Cache hit rate**: Aim for > 80% for repeated queries
- **Memory usage**: Should stabilize after initial scan

## Production Deployment

### Recommended Settings

For production deployments:

```env
# Cache for 1 hour (docs don't change often)
MCP_DOCS_CACHE_TTL=3600

# Allocate adequate memory
MCP_DOCS_MAX_CACHE_MB=1000

# Disable file watching if docs are updated via deployment
MCP_DOCS_WATCH_FILES=false

# Production logging
LOG_LEVEL=WARN
MCP_DOCS_AUDIT_LOG=true
```

## Scaling Considerations

- **Horizontal scaling**: Deploy multiple instances behind a load balancer
- **CDN integration**: Cache static file responses
- **Database backend**: Consider external search index for 10,000+ documents

## Troubleshooting Slow Performance

### Common Issues

**Slow initial startup**
- Reduce directory depth
- Exclude large binary files
- Use include/exclude patterns

**High memory usage**
- Reduce cache size
- Limit number of indexed files
- Check for very large markdown files

**Slow search queries**
- Reduce search limit
- Use more specific search terms
- Enable category-based filtering

## Monitoring and Profiling

Enable detailed logging to identify bottlenecks:

```bash
export LOG_LEVEL=DEBUG
hierarchical-docs-mcp 2>&1 | grep -E "duration|time|cache"
```

## Next Steps

- Review [CLI Commands](../../reference/cli-commands.md) for profiling tools
- Check [Configuration Guide](../configuration.md) for tuning options
- Explore caching strategies in the advanced documentation
