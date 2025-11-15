// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load health stats on page load
fetch('/api/health')
    .then(res => res.json())
    .then(data => {
        document.getElementById('doc-count').textContent = data.documents;
        document.getElementById('category-count').textContent = data.categories;
    })
    .catch(err => console.error('Failed to load stats:', err));

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function() {
        const tabName = this.getAttribute('data-tab');

        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // Remove active class from all tabs
        document.querySelectorAll('.tab').forEach(t => {
            t.classList.remove('active');
        });

        // Show selected tab content
        document.getElementById(tabName + '-tab').classList.add('active');

        // Add active class to clicked tab
        this.classList.add('active');
    });
});

// Search button
document.getElementById('search-btn').addEventListener('click', performSearch);
document.getElementById('search-query').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') performSearch();
});

// TOC button
document.getElementById('toc-btn').addEventListener('click', loadTableOfContents);

// Tags button
document.getElementById('tags-btn').addEventListener('click', searchByTags);
document.getElementById('tags-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') searchByTags();
});

// Document button
document.getElementById('document-btn').addEventListener('click', getDocument);
document.getElementById('document-uri').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') getDocument();
});

async function performSearch() {
    const query = document.getElementById('search-query').value;
    if (!query) {
        alert('Please enter a search query');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.results && data.results.length > 0) {
            displaySearchResults(data.results);
        } else {
            showNoResults();
        }
    } catch (err) {
        showError('Search failed: ' + err.message);
    }
}

async function loadTableOfContents() {
    showLoading();

    try {
        const response = await fetch('/api/toc');
        const data = await response.json();
        displayTableOfContents(data);
    } catch (err) {
        showError('Failed to load table of contents: ' + err.message);
    }
}

async function searchByTags() {
    const tagsInput = document.getElementById('tags-input').value;
    if (!tagsInput) {
        alert('Please enter at least one tag');
        return;
    }

    const tags = tagsInput.split(',').map(t => t.trim()).filter(t => t);

    showLoading();

    try {
        const response = await fetch('/api/search-by-tags', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ tags }),
        });
        const data = await response.json();

        if (data.results && data.results.length > 0) {
            displaySearchResults(data.results);
        } else {
            showNoResults();
        }
    } catch (err) {
        showError('Tag search failed: ' + err.message);
    }
}

async function getDocument() {
    const uri = document.getElementById('document-uri').value;
    if (!uri) {
        alert('Please enter a document URI');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`/api/document?uri=${encodeURIComponent(uri)}`);
        const data = await response.json();

        if (data.error) {
            showError(data.error);
        } else {
            displayDocument(data);
        }
    } catch (err) {
        showError('Failed to get document: ' + err.message);
    }
}

async function navigateToUri(uri) {
    showLoading();

    try {
        const response = await fetch(`/api/document?uri=${encodeURIComponent(uri)}`);
        const data = await response.json();

        if (data.error) {
            showError(data.error);
        } else {
            displayDocument(data);
        }
    } catch (err) {
        showError('Failed to navigate: ' + err.message);
    }
}

function displaySearchResults(results) {
    const resultsDiv = document.getElementById('results');

    let html = '<h2 style="margin-bottom: 1.5rem;">Search Results (' + results.length + ')</h2>';

    results.forEach((result, index) => {
        if (result.error) {
            html += '<div class="error">' + escapeHtml(result.error) + '</div>';
            return;
        }

        html += '<div class="result-item">';
        html += '<div class="result-title" data-uri="' + escapeHtml(result.uri) +
                '" data-result-index="' + index + '">' +
                escapeHtml(result.title || 'Untitled') + '</div>';
        if (result.breadcrumbs) {
            html += '<div class="breadcrumbs">' + escapeHtml(result.breadcrumbs) + '</div>';
        }
        if (result.excerpt) {
            html += '<div class="excerpt">' + result.excerpt + '</div>';
        }
        if (result.relevance !== undefined) {
            html += '<span class="relevance">Relevance: ' +
                    (result.relevance * 100).toFixed(0) + '%</span>';
        }
        html += '</div>';
    });

    resultsDiv.innerHTML = html;

    // Add click handlers after inserting HTML
    document.querySelectorAll('.result-title[data-uri]').forEach(el => {
        el.style.cursor = 'pointer';
        el.addEventListener('click', function() {
            navigateToUri(this.getAttribute('data-uri'));
        });
    });
}

function displayTableOfContents(toc) {
    const resultsDiv = document.getElementById('results');

    let html = '<h2 style="margin-bottom: 1.5rem;">Table of Contents</h2>';
    html += '<ul class="toc-tree">';

    // Render children if they exist
    if (toc.children && toc.children.length > 0) {
        toc.children.forEach(child => {
            html += renderTocNode(child);
        });
    } else {
        html += '<li>No documentation found</li>';
    }

    html += '</ul>';

    resultsDiv.innerHTML = html;

    // Add click handlers for documents
    document.querySelectorAll('.toc-document[data-uri]').forEach(el => {
        el.addEventListener('click', function() {
            navigateToUri(this.getAttribute('data-uri'));
        });
    });
}

function renderTocNode(node) {
    let html = '';

    if (node.type === 'category') {
        html += '<li class="toc-item">';
        html += '<div class="toc-category">' + escapeHtml(node.name) +
                ' (' + node.document_count + ' docs)</div>';

        if (node.children && node.children.length > 0) {
            html += '<ul class="toc-tree">';
            node.children.forEach(child => {
                html += renderTocNode(child);
            });
            html += '</ul>';
        }

        html += '</li>';
    } else if (node.type === 'document') {
        html += '<li class="toc-item">';
        html += '<div class="toc-document" data-uri="' + escapeHtml(node.uri) + '">' +
                escapeHtml(node.name) + '</div>';
        html += '</li>';
    }

    return html;
}

function displayDocument(doc) {
    const resultsDiv = document.getElementById('results');

    let html = '<div class="document-content">';
    html += '<h1>' + escapeHtml(doc.title) + '</h1>';

    if (doc.breadcrumbs && Array.isArray(doc.breadcrumbs)) {
        const breadcrumbsText = doc.breadcrumbs.map(b => escapeHtml(b)).join(' > ');
        html += '<div class="breadcrumbs">' + breadcrumbsText + '</div>';
    }

    if (doc.tags && doc.tags.length > 0) {
        html += '<div style="margin: 1rem 0;">';
        doc.tags.forEach(tag => {
            html += '<span style="background: #e0e0e0; padding: 0.25rem 0.5rem; border-radius: 3px; margin-right: 0.5rem;">' +
                    escapeHtml(tag) + '</span>';
        });
        html += '</div>';
    }

    html += '<hr style="margin: 1.5rem 0; border: none; border-top: 1px solid #e0e0e0;">';

    // Render content with proper newline handling
    const rawContent = doc.content || '';

    // Split by newlines, escape each line, then join with <br>
    const lines = rawContent.split('\n');
    const escapedLines = lines.map(line => {
        let escaped = escapeHtml(line);
        // Apply basic markdown after escaping
        escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        escaped = escaped.replace(/\*(.+?)\*/g, '<em>$1</em>');
        escaped = escaped.replace(/`(.+?)`/g, '<code>$1</code>');
        return escaped;
    });

    const content = escapedLines.join('<br>');

    html += '<div>' + content + '</div>';
    html += '</div>';

    resultsDiv.innerHTML = html;
}

function showLoading() {
    document.getElementById('results').innerHTML =
        '<div class="loading">Loading...</div>';
}

function showNoResults() {
    document.getElementById('results').innerHTML =
        '<div style="text-align: center; color: #666; padding: 2rem;">No results found</div>';
}

function showError(message) {
    document.getElementById('results').innerHTML =
        '<div class="error">' + escapeHtml(message) + '</div>';
}
