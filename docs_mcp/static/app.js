// ============================================================================
// Modern Markdown MCP Documentation Web Interface
// ============================================================================

// State Management
const state = {
    currentView: 'home',
    theme: localStorage.getItem('theme') || 'dark',
    searchResults: [],
    tocData: null,
    currentDocument: null,
    availableTags: [],
};

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    initializeEventListeners();
    loadHealthStats();
    showHomeView();
});

// ============================================================================
// Theme Management
// ============================================================================

function initializeTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    updateThemeIcon();
}

function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', state.theme);
    document.documentElement.setAttribute('data-theme', state.theme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const icon = document.querySelector('#theme-toggle i');
    icon.className = state.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
}

// ============================================================================
// Event Listeners
// ============================================================================

function initializeEventListeners() {
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

    // Mobile menu toggle
    document.getElementById('mobile-menu-toggle').addEventListener('click', toggleMobileMenu);

    // Logo click - go to home
    document.getElementById('logo-link').addEventListener('click', (e) => {
        e.preventDefault();
        navigateToView('home');
    });

    // Navigation links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function() {
            const view = this.getAttribute('data-view');
            navigateToView(view);
        });
    });

    // Header search
    const headerSearch = document.getElementById('header-search');
    headerSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = headerSearch.value.trim();
            if (query) {
                // Navigate to search view first, then perform search
                navigateToView('search');
                // Wait for DOM to update, then search
                setTimeout(() => {
                    const searchInput = document.getElementById('search-query-input');
                    if (searchInput) {
                        searchInput.value = query;
                    }
                    performSearch(query);
                }, 50);
            }
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // "/" to focus search
        if (e.key === '/' && !isInputFocused()) {
            e.preventDefault();
            document.getElementById('header-search').focus();
        }
        // Escape to clear search
        if (e.key === 'Escape') {
            document.getElementById('header-search').blur();
        }
    });
}

function isInputFocused() {
    const activeElement = document.activeElement;
    return activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA';
}

function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// ============================================================================
// Navigation
// ============================================================================

function navigateToView(view) {
    state.currentView = view;

    // Update navigation active state
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`.nav-link[data-view="${view}"]`)?.classList.add('active');

    // Close mobile menu
    document.getElementById('sidebar').classList.remove('open');

    // Load view
    switch(view) {
        case 'home':
            showHomeView();
            break;
        case 'search':
            showSearchView();
            break;
        case 'toc':
            showTocView();
            break;
        case 'tags':
            showTagsView();
            break;
        case 'release':
            showReleaseView();
            break;
        default:
            showHomeView();
    }
}

// ============================================================================
// Health Stats
// ============================================================================

async function loadHealthStats() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        document.getElementById('doc-count').textContent = data.documents || 0;
        document.getElementById('category-count').textContent = data.categories || 0;
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

// ============================================================================
// View Rendering
// ============================================================================

function showHomeView() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h1 class="card-title">Welcome to Markdown MCP Documentation</h1>
                <p class="card-subtitle">Browse and search documentation with the same powerful tools available to LLMs</p>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-top: 2rem;">
                <div class="card" style="cursor: pointer;" onclick="navigateToView('search')">
                    <div style="text-align: center;">
                        <i class="fas fa-search" style="font-size: 2.5rem; color: var(--accent-primary); margin-bottom: 1rem;"></i>
                        <h3 style="margin-bottom: 0.5rem; color: var(--text-primary);">Search</h3>
                        <p style="color: var(--text-secondary); font-size: 0.9375rem;">Full-text search across all documentation</p>
                    </div>
                </div>

                <div class="card" style="cursor: pointer;" onclick="navigateToView('toc')">
                    <div style="text-align: center;">
                        <i class="fas fa-list" style="font-size: 2.5rem; color: var(--accent-primary); margin-bottom: 1rem;"></i>
                        <h3 style="margin-bottom: 0.5rem; color: var(--text-primary);">Browse</h3>
                        <p style="color: var(--text-secondary); font-size: 0.9375rem;">Explore the documentation structure</p>
                    </div>
                </div>

                <div class="card" style="cursor: pointer;" onclick="navigateToView('tags')">
                    <div style="text-align: center;">
                        <i class="fas fa-tags" style="font-size: 2.5rem; color: var(--accent-primary); margin-bottom: 1rem;"></i>
                        <h3 style="margin-bottom: 0.5rem; color: var(--text-primary);">Tags</h3>
                        <p style="color: var(--text-secondary); font-size: 0.9375rem;">Filter documentation by tags</p>
                    </div>
                </div>

                <div class="card" style="cursor: pointer;" onclick="navigateToView('release')">
                    <div style="text-align: center;">
                        <i class="fas fa-file-pdf" style="font-size: 2.5rem; color: var(--accent-primary); margin-bottom: 1rem;"></i>
                        <h3 style="margin-bottom: 0.5rem; color: var(--text-primary);">Generate Release</h3>
                        <p style="color: var(--text-secondary); font-size: 0.9375rem;">Create PDF documentation releases</p>
                    </div>
                </div>
            </div>

            <div style="margin-top: 2rem; padding: 1.5rem; background: var(--bg-secondary); border-radius: var(--radius-lg);">
                <h3 style="margin-bottom: 1rem; color: var(--text-primary);">Quick Tips</h3>
                <ul style="color: var(--text-secondary); line-height: 2;">
                    <li>Press <code style="background: var(--bg-tertiary); padding: 0.125rem 0.5rem; border-radius: var(--radius-sm); font-family: 'JetBrains Mono', monospace;">/</code> to quickly focus the search bar</li>
                    <li>Use the table of contents to browse documentation hierarchically</li>
                    <li>Toggle dark mode with the moon/sun icon in the header</li>
                    <li>Click on any document card to view its full content with proper markdown rendering</li>
                </ul>
            </div>
        </div>
    `;
}

function showSearchView() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h1 class="card-title">Search Documentation</h1>
                <p class="card-subtitle">Search across all markdown documents with full-text search</p>
            </div>

            <div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
                <input
                    type="text"
                    id="search-query-input"
                    class="search-input"
                    placeholder="Enter your search query..."
                    style="flex: 1; padding: 0.75rem 1rem; font-size: 1rem;"
                    autocomplete="off"
                >
                <button class="btn btn-primary" id="search-submit-btn" style="padding: 0.75rem 2rem;">
                    <i class="fas fa-search" style="margin-right: 0.5rem;"></i>
                    Search
                </button>
            </div>

            <div id="search-results-container"></div>
        </div>
    `;

    // Add event listeners
    const searchInput = document.getElementById('search-query-input');
    const searchBtn = document.getElementById('search-submit-btn');

    searchInput.focus();
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch(searchInput.value);
        }
    });
    searchBtn.addEventListener('click', () => {
        performSearch(searchInput.value);
    });
}

function showTocView() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h1 class="card-title">Table of Contents</h1>
                <p class="card-subtitle">Browse all documentation organized by categories</p>
            </div>

            <div id="toc-container">
                <div class="loading-skeleton skeleton-title"></div>
                <div class="loading-skeleton skeleton-text"></div>
                <div class="loading-skeleton skeleton-text"></div>
                <div class="loading-skeleton skeleton-text"></div>
            </div>
        </div>
    `;

    loadTableOfContents();
}

function showTagsView() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h1 class="card-title">Browse by Tags</h1>
                <p class="card-subtitle">Filter documentation by metadata tags. Click tags below or type your own.</p>
            </div>

            <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                <input
                    type="text"
                    id="tags-input"
                    class="search-input"
                    placeholder="Enter tags (comma-separated)..."
                    style="flex: 1; padding: 0.75rem 1rem; font-size: 1rem;"
                    autocomplete="off"
                >
                <button class="btn btn-primary" id="tags-submit-btn" style="padding: 0.75rem 2rem;">
                    <i class="fas fa-filter" style="margin-right: 0.5rem;"></i>
                    Filter
                </button>
            </div>

            <div id="available-tags-container" style="margin-bottom: 2rem;">
                <div class="loading-skeleton skeleton-text" style="width: 60%;"></div>
            </div>

            <div id="tags-results-container"></div>
        </div>
    `;

    // Add event listeners
    const tagsInput = document.getElementById('tags-input');
    const tagsBtn = document.getElementById('tags-submit-btn');

    tagsInput.focus();
    tagsInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchByTags(tagsInput.value);
        }
    });
    tagsBtn.addEventListener('click', () => {
        searchByTags(tagsInput.value);
    });

    // Load available tags
    loadAvailableTags();
}

async function loadAvailableTags() {
    const container = document.getElementById('available-tags-container');
    if (!container) return;

    try {
        const response = await fetch('/api/tags?include_counts=true');
        const data = await response.json();

        if (data.error) {
            container.innerHTML = `<p style="color: var(--text-tertiary);">Could not load tags</p>`;
            return;
        }

        const tags = data.tag_counts || data.tags || [];
        if (tags.length === 0) {
            container.innerHTML = `<p style="color: var(--text-tertiary);">No tags found in documentation</p>`;
            return;
        }

        state.availableTags = Array.isArray(tags[0]) ? tags : tags.map(t => typeof t === 'string' ? { tag: t, document_count: 0 } : t);

        let html = `
            <div style="margin-bottom: 0.5rem; color: var(--text-secondary); font-size: 0.875rem;">
                <i class="fas fa-tags" style="margin-right: 0.5rem;"></i>
                Available tags (click to add):
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
        `;

        state.availableTags.forEach(item => {
            const tagName = item.tag || item;
            const count = item.document_count || 0;
            html += `
                <span class="tag tag-clickable" onclick="addTagToInput('${escapeHtml(tagName)}')" style="cursor: pointer; transition: all 0.2s;">
                    <i class="fas fa-tag"></i> ${escapeHtml(tagName)}
                    ${count > 0 ? `<span style="opacity: 0.7; margin-left: 0.25rem;">(${count})</span>` : ''}
                </span>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    } catch (err) {
        console.error('Failed to load tags:', err);
        container.innerHTML = `<p style="color: var(--text-tertiary);">Could not load tags</p>`;
    }
}

function addTagToInput(tag) {
    const tagsInput = document.getElementById('tags-input');
    if (!tagsInput) return;

    const currentValue = tagsInput.value.trim();
    const existingTags = currentValue ? currentValue.split(',').map(t => t.trim().toLowerCase()) : [];

    // Don't add duplicate tags
    if (existingTags.includes(tag.toLowerCase())) {
        return;
    }

    if (currentValue) {
        tagsInput.value = currentValue + ', ' + tag;
    } else {
        tagsInput.value = tag;
    }

    tagsInput.focus();
}

// ============================================================================
// Search Functionality
// ============================================================================

async function performSearch(query) {
    if (!query || query.trim() === '') {
        showEmptyState('search-results-container', 'Please enter a search query', 'fas fa-search');
        return;
    }

    const container = document.getElementById('search-results-container');
    if (!container) return;

    // Show loading
    container.innerHTML = `
        <div class="loading-skeleton skeleton-title"></div>
        <div class="loading-skeleton skeleton-text"></div>
        <div class="loading-skeleton skeleton-text"></div>
        <div class="loading-skeleton skeleton-text"></div>
    `;

    try {
        const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.error) {
            showErrorState(container, 'Search Error', data.error);
            return;
        }

        if (!data.results || data.results.length === 0) {
            showEmptyState('search-results-container', 'No results found', 'fas fa-search', 'Try different keywords or browse the table of contents');
            return;
        }

        displaySearchResults(data.results, container);
    } catch (err) {
        showErrorState(container, 'Search Failed', err.message);
    }
}

function displaySearchResults(results, container) {
    let html = `
        <div style="margin-bottom: 1.5rem; color: var(--text-secondary);">
            Found <strong style="color: var(--text-primary);">${results.length}</strong> result${results.length !== 1 ? 's' : ''}
        </div>
        <div class="results-grid">
    `;

    results.forEach(result => {
        if (result.error) {
            html += `<div class="error-state"><div class="error-content"><p>${escapeHtml(result.error)}</p></div></div>`;
            return;
        }

        const relevance = result.relevance !== undefined ? (result.relevance * 100).toFixed(0) : null;
        const excerpt = result.excerpt || truncateText(result.content, 200);

        html += `
            <div class="result-card" onclick='navigateToDocument("${escapeHtml(result.uri)}")'>
                <div class="result-header">
                    <div>
                        <div class="result-title">${escapeHtml(result.title || 'Untitled')}</div>
                        <div class="result-path">${escapeHtml(result.breadcrumbs || result.uri)}</div>
                    </div>
                    ${relevance ? `
                        <div class="result-relevance">
                            <i class="fas fa-chart-line"></i>
                            <span>${relevance}%</span>
                        </div>
                    ` : ''}
                </div>
                ${excerpt ? `<div class="result-excerpt">${excerpt}</div>` : ''}
                ${result.tags && result.tags.length > 0 ? `
                    <div class="result-tags">
                        ${result.tags.map(tag => `<span class="tag"><i class="fas fa-tag"></i> ${escapeHtml(tag)}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

// ============================================================================
// Table of Contents
// ============================================================================

async function loadTableOfContents() {
    const container = document.getElementById('toc-container');
    if (!container) return;

    try {
        const response = await fetch('/api/toc');
        const data = await response.json();

        if (data.error) {
            showErrorState(container, 'Failed to Load', data.error);
            return;
        }

        state.tocData = data;
        displayTableOfContents(data, container);
        updateQuickToc(data);
    } catch (err) {
        showErrorState(container, 'Failed to Load TOC', err.message);
    }
}

function displayTableOfContents(toc, container) {
    if (!toc.children || toc.children.length === 0) {
        showEmptyState('toc-container', 'No documentation found', 'fas fa-folder-open');
        return;
    }

    let html = '<ul class="toc-tree">';
    toc.children.forEach(child => {
        html += renderTocNode(child);
    });
    html += '</ul>';

    container.innerHTML = html;
}

function renderTocNode(node) {
    let html = '<li class="toc-item">';

    if (node.type === 'category') {
        html += `
            <div class="toc-category">
                <i class="fas fa-folder"></i>
                <span>${escapeHtml(node.name)}</span>
                <span style="margin-left: auto; font-size: 0.8125rem; color: var(--text-tertiary);">${node.document_count} docs</span>
            </div>
        `;

        if (node.children && node.children.length > 0) {
            html += '<ul class="toc-tree toc-children">';
            node.children.forEach(child => {
                html += renderTocNode(child);
            });
            html += '</ul>';
        }
    } else if (node.type === 'document') {
        html += `
            <div class="toc-document" onclick='navigateToDocument("${escapeHtml(node.uri)}")'>
                <i class="fas fa-file-alt"></i>
                <span>${escapeHtml(node.name)}</span>
            </div>
        `;
    }

    html += '</li>';
    return html;
}

function updateQuickToc(toc) {
    const quickToc = document.getElementById('quick-toc');
    if (!quickToc || !toc.children || toc.children.length === 0) return;

    let html = '<ul class="toc-tree">';

    // Show first few categories/documents as quick links
    const items = toc.children.slice(0, 5);
    items.forEach(item => {
        if (item.type === 'category' && item.children && item.children.length > 0) {
            // Show first document from each category
            const firstDoc = item.children.find(c => c.type === 'document');
            if (firstDoc) {
                html += `
                    <li class="toc-item">
                        <div class="toc-document" onclick='navigateToDocument("${escapeHtml(firstDoc.uri)}")'>
                            <i class="fas fa-file-alt"></i>
                            <span>${escapeHtml(firstDoc.name)}</span>
                        </div>
                    </li>
                `;
            }
        } else if (item.type === 'document') {
            html += `
                <li class="toc-item">
                    <div class="toc-document" onclick='navigateToDocument("${escapeHtml(item.uri)}")'>
                        <i class="fas fa-file-alt"></i>
                        <span>${escapeHtml(item.name)}</span>
                    </div>
                </li>
            `;
        }
    });

    html += '</ul>';
    quickToc.innerHTML = html;
}

// ============================================================================
// Tags Search
// ============================================================================

async function searchByTags(tagsInput) {
    if (!tagsInput || tagsInput.trim() === '') {
        showEmptyState('tags-results-container', 'Please enter at least one tag', 'fas fa-tags');
        return;
    }

    const tags = tagsInput.split(',').map(t => t.trim()).filter(t => t);
    const container = document.getElementById('tags-results-container');
    if (!container) return;

    // Show loading
    container.innerHTML = `
        <div class="loading-skeleton skeleton-title"></div>
        <div class="loading-skeleton skeleton-text"></div>
        <div class="loading-skeleton skeleton-text"></div>
    `;

    try {
        const response = await fetch('/api/search-by-tags', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tags }),
        });
        const data = await response.json();

        if (data.error) {
            showErrorState(container, 'Search Error', data.error);
            return;
        }

        if (!data.results || data.results.length === 0) {
            showEmptyState('tags-results-container', 'No documents found with these tags', 'fas fa-tags');
            return;
        }

        displaySearchResults(data.results, container);
    } catch (err) {
        showErrorState(container, 'Tag Search Failed', err.message);
    }
}

// ============================================================================
// PDF Release Generation
// ============================================================================

function showReleaseView() {
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h1 class="card-title">Generate PDF Release</h1>
                <p class="card-subtitle">Create a PDF documentation release with customizable metadata and optional confidentiality markings</p>
            </div>

            <div style="margin-bottom: 2rem;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem;">
                    <div>
                        <label style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-weight: 500;">
                            Document Title
                        </label>
                        <input
                            type="text"
                            id="release-title-input"
                            class="search-input"
                            placeholder="e.g., API Reference Documentation"
                            style="width: 100%; padding: 0.75rem 1rem; font-size: 1rem;"
                            autocomplete="off"
                        >
                    </div>

                    <div>
                        <label style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-weight: 500;">
                            Subtitle
                        </label>
                        <input
                            type="text"
                            id="release-subtitle-input"
                            class="search-input"
                            placeholder="e.g., Complete Documentation Release"
                            style="width: 100%; padding: 0.75rem 1rem; font-size: 1rem;"
                            autocomplete="off"
                        >
                    </div>

                    <div>
                        <label style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-weight: 500;">
                            Author
                        </label>
                        <input
                            type="text"
                            id="release-author-input"
                            class="search-input"
                            placeholder="e.g., Engineering Team"
                            style="width: 100%; padding: 0.75rem 1rem; font-size: 1rem;"
                            autocomplete="off"
                        >
                    </div>

                    <div>
                        <label style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-weight: 500;">
                            Version
                        </label>
                        <input
                            type="text"
                            id="release-version-input"
                            class="search-input"
                            placeholder="e.g., 2.0.0 (defaults to date)"
                            style="width: 100%; padding: 0.75rem 1rem; font-size: 1rem;"
                            autocomplete="off"
                        >
                    </div>
                </div>

                <div style="padding: 1rem; background: var(--bg-secondary); border-radius: var(--radius-lg); margin-bottom: 1.5rem;">
                    <div style="margin-bottom: 1rem;">
                        <label style="display: flex; align-items: center; gap: 0.75rem; cursor: pointer; color: var(--text-secondary);">
                            <input
                                type="checkbox"
                                id="release-confidential-checkbox"
                                style="width: 1.25rem; height: 1.25rem; cursor: pointer;"
                                onchange="toggleOwnerField()"
                            >
                            <span>
                                <strong style="color: var(--text-primary);">Add confidentiality markings</strong><br>
                                <small>Includes watermark, headers, footers with "CONFIDENTIAL" notices</small>
                            </span>
                        </label>
                    </div>

                    <div id="owner-field-container" style="display: none; margin-top: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; color: var(--text-secondary); font-weight: 500;">
                            Copyright Owner <small style="color: var(--text-tertiary);">(for confidentiality notices)</small>
                        </label>
                        <input
                            type="text"
                            id="release-owner-input"
                            class="search-input"
                            placeholder="e.g., Acme Corporation"
                            style="max-width: 400px; padding: 0.75rem 1rem; font-size: 1rem;"
                            autocomplete="off"
                        >
                    </div>
                </div>

                <button class="btn btn-primary" id="generate-pdf-btn" style="padding: 0.75rem 2rem;">
                    <i class="fas fa-file-pdf" style="margin-right: 0.5rem;"></i>
                    Generate PDF Release
                </button>
            </div>

            <div id="release-result-container"></div>

            <div style="margin-top: 2rem; padding: 1.5rem; background: var(--bg-secondary); border-radius: var(--radius-lg);">
                <h3 style="margin-bottom: 1rem; color: var(--text-primary);">
                    <i class="fas fa-info-circle" style="margin-right: 0.5rem;"></i>
                    Requirements
                </h3>
                <ul style="color: var(--text-secondary); line-height: 2;">
                    <li><strong>pandoc</strong> - Document converter (<code>sudo apt install pandoc</code>)</li>
                    <li><strong>texlive-xetex</strong> - LaTeX PDF engine (<code>sudo apt install texlive-xetex texlive-latex-extra</code>)</li>
                    <li><strong>Pillow</strong> - For ASCII diagram conversion (<code>pip install Pillow</code>)</li>
                </ul>
            </div>
        </div>
    `;

    // Add event listener
    document.getElementById('generate-pdf-btn').addEventListener('click', generatePDFRelease);
}

function toggleOwnerField() {
    const checkbox = document.getElementById('release-confidential-checkbox');
    const ownerContainer = document.getElementById('owner-field-container');
    ownerContainer.style.display = checkbox.checked ? 'block' : 'none';
}

async function generatePDFRelease() {
    const titleInput = document.getElementById('release-title-input');
    const subtitleInput = document.getElementById('release-subtitle-input');
    const authorInput = document.getElementById('release-author-input');
    const versionInput = document.getElementById('release-version-input');
    const confidentialCheckbox = document.getElementById('release-confidential-checkbox');
    const ownerInput = document.getElementById('release-owner-input');
    const container = document.getElementById('release-result-container');
    const btn = document.getElementById('generate-pdf-btn');

    const title = titleInput.value.trim() || null;
    const subtitle = subtitleInput.value.trim() || null;
    const author = authorInput.value.trim() || null;
    const version = versionInput.value.trim() || null;
    const confidential = confidentialCheckbox.checked;
    const owner = ownerInput.value.trim() || null;

    // Disable button and show loading
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 0.5rem;"></i> Generating...';

    container.innerHTML = `
        <div style="padding: 1.5rem; background: var(--bg-secondary); border-radius: var(--radius-lg); text-align: center;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--accent-primary); margin-bottom: 1rem;"></i>
            <p style="color: var(--text-secondary);">Generating PDF documentation release...</p>
            <p style="color: var(--text-tertiary); font-size: 0.875rem;">This may take a few moments</p>
        </div>
    `;

    try {
        const response = await fetch('/api/generate-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, subtitle, author, version, confidential, owner }),
        });
        const data = await response.json();

        if (!data.success) {
            container.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-circle error-icon"></i>
                    <div class="error-content">
                        <h3>PDF Generation Failed</h3>
                        <p>${escapeHtml(data.error || 'Unknown error')}</p>
                        ${data.stdout ? `<pre style="margin-top: 1rem; font-size: 0.8125rem; overflow-x: auto;">${escapeHtml(data.stdout)}</pre>` : ''}
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div style="padding: 1.5rem; background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1)); border: 1px solid var(--accent-primary); border-radius: var(--radius-lg);">
                <div style="text-align: center; margin-bottom: 1.5rem;">
                    <i class="fas fa-check-circle" style="font-size: 3rem; color: #10b981; margin-bottom: 1rem;"></i>
                    <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">PDF Generated Successfully!</h3>
                    <p style="color: var(--text-secondary);">${escapeHtml(data.message || 'Documentation release created')}</p>
                </div>

                <div style="background: var(--bg-tertiary); padding: 1rem; border-radius: var(--radius-md); font-family: 'JetBrains Mono', monospace; font-size: 0.875rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: var(--text-secondary);">Output File:</span>
                        <span style="color: var(--text-primary);">${escapeHtml(data.output_file || 'N/A')}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: var(--text-secondary);">Manifest:</span>
                        <span style="color: var(--text-primary);">${escapeHtml(data.manifest_file || 'N/A')}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: var(--text-secondary);">Version:</span>
                        <span style="color: var(--text-primary);">${escapeHtml(data.version || 'auto')}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: var(--text-secondary);">Confidential:</span>
                        <span style="color: var(--text-primary);">${data.confidential ? 'Yes' : 'No'}</span>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-circle error-icon"></i>
                <div class="error-content">
                    <h3>Request Failed</h3>
                    <p>${escapeHtml(err.message)}</p>
                </div>
            </div>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-file-pdf" style="margin-right: 0.5rem;"></i> Generate PDF Release';
    }
}

// ============================================================================
// Document Display
// ============================================================================

async function navigateToDocument(uri) {
    const contentArea = document.getElementById('content-area');

    // Show loading
    contentArea.innerHTML = `
        <div class="document-container">
            <div class="loading-skeleton skeleton-title"></div>
            <div class="loading-skeleton skeleton-text"></div>
            <div class="loading-skeleton skeleton-text"></div>
            <div class="loading-skeleton skeleton-text" style="width: 80%;"></div>
        </div>
    `;

    try {
        const response = await fetch(`/api/document?uri=${encodeURIComponent(uri)}`);
        const data = await response.json();

        if (data.error) {
            contentArea.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-circle error-icon"></i>
                    <div class="error-content">
                        <h3>Failed to Load Document</h3>
                        <p>${escapeHtml(data.error)}</p>
                    </div>
                </div>
            `;
            return;
        }

        state.currentDocument = data;
        displayDocument(data, contentArea);
    } catch (err) {
        contentArea.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-circle error-icon"></i>
                <div class="error-content">
                    <h3>Failed to Load Document</h3>
                    <p>${escapeHtml(err.message)}</p>
                </div>
            </div>
        `;
    }
}

function displayDocument(doc, container) {
    // Render breadcrumbs
    let breadcrumbsHtml = '';
    if (doc.breadcrumbs && Array.isArray(doc.breadcrumbs) && doc.breadcrumbs.length > 0) {
        breadcrumbsHtml = `
            <div class="breadcrumbs">
                <i class="fas fa-home"></i>
                ${doc.breadcrumbs.map((crumb, idx) => `
                    ${idx > 0 ? '<i class="fas fa-chevron-right breadcrumb-separator"></i>' : ''}
                    <span class="breadcrumb-link">${escapeHtml(crumb)}</span>
                `).join('')}
            </div>
        `;
    }

    // Render tags
    let tagsHtml = '';
    if (doc.tags && doc.tags.length > 0) {
        tagsHtml = `
            <div class="result-tags" style="margin-bottom: 0;">
                ${doc.tags.map(tag => `<span class="tag"><i class="fas fa-tag"></i> ${escapeHtml(tag)}</span>`).join('')}
            </div>
        `;
    }

    // Render markdown content using marked.js
    let contentHtml = '';
    if (doc.content) {
        try {
            // Configure marked for better rendering
            marked.setOptions({
                breaks: true,
                gfm: true,
                highlight: function(code, lang) {
                    if (lang && hljs.getLanguage(lang)) {
                        try {
                            return hljs.highlight(code, { language: lang }).value;
                        } catch (err) {
                            console.error('Highlight error:', err);
                        }
                    }
                    return hljs.highlightAuto(code).value;
                }
            });

            contentHtml = marked.parse(doc.content);
        } catch (err) {
            console.error('Markdown parsing error:', err);
            contentHtml = `<pre>${escapeHtml(doc.content)}</pre>`;
        }
    }

    container.innerHTML = `
        ${breadcrumbsHtml}

        <div class="document-container">
            <div class="document-header">
                <h1 class="document-title">${escapeHtml(doc.title || 'Untitled Document')}</h1>
                <div class="document-meta">
                    ${doc.category ? `
                        <div style="display: flex; align-items: center; gap: 0.375rem;">
                            <i class="fas fa-folder"></i>
                            <span>${escapeHtml(doc.category)}</span>
                        </div>
                    ` : ''}
                    ${doc.uri ? `
                        <div style="display: flex; align-items: center; gap: 0.375rem;">
                            <i class="fas fa-link"></i>
                            <code style="font-family: 'JetBrains Mono', monospace; font-size: 0.8125rem;">${escapeHtml(doc.uri)}</code>
                        </div>
                    ` : ''}
                </div>
                ${tagsHtml}
            </div>

            <div class="document-content">
                ${contentHtml}
            </div>
        </div>

        <div style="margin-top: 2rem; text-align: center;">
            <button class="btn btn-secondary" onclick="navigateToView('toc')">
                <i class="fas fa-arrow-left" style="margin-right: 0.5rem;"></i>
                Back to Table of Contents
            </button>
        </div>
    `;

    // Apply syntax highlighting to any code blocks
    container.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

// ============================================================================
// UI Helper Functions
// ============================================================================

function showEmptyState(containerId, title, icon, description = '') {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <div class="empty-state">
            <i class="${icon} empty-state-icon"></i>
            <h2 class="empty-state-title">${escapeHtml(title)}</h2>
            ${description ? `<p class="empty-state-description">${escapeHtml(description)}</p>` : ''}
        </div>
    `;
}

function showErrorState(container, title, message) {
    container.innerHTML = `
        <div class="error-state">
            <i class="fas fa-exclamation-circle error-icon"></i>
            <div class="error-content">
                <h3>${escapeHtml(title)}</h3>
                <p>${escapeHtml(message)}</p>
            </div>
        </div>
    `;
}

// ============================================================================
// Utility Functions
// ============================================================================

function escapeHtml(text) {
    if (typeof text !== 'string') return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return escapeHtml(text);
    return escapeHtml(text.substring(0, maxLength)) + '...';
}

// Make functions available globally for onclick handlers
window.navigateToView = navigateToView;
window.navigateToDocument = navigateToDocument;
window.performSearch = performSearch;
window.searchByTags = searchByTags;
window.addTagToInput = addTagToInput;
window.generatePDFRelease = generatePDFRelease;
