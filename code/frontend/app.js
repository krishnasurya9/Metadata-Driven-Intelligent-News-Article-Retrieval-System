/**
 * News Search - Main Application JavaScript
 * Handles core functionality, API calls, and state management
 */

const API_BASE = 'http://localhost:5000/api';

// Application State
const state = {
    currentMode: 'search',
    currentQuery: '',
    currentPage: 1,
    resultsPerPage: 10,
    allResults: [],
    searchTime: 0,
    currentSummary: null,
    isLoading: false
};

// DOM Elements
const elements = {
    // Main Container
    mainView: document.getElementById('main-view'),

    // Search Elements
    searchHero: document.getElementById('search-hero'),
    queryInput: document.getElementById('query-input'),
    searchBtn: document.getElementById('search-btn'),

    // Live News
    liveNewsContainer: document.getElementById('live-news-container'),

    // Header
    header: document.querySelector('.header'),
    logoLink: document.querySelector('.logo'),

    // Results
    resultsContainer: document.getElementById('results-container'),
    resultsCount: document.getElementById('results-count'),
    resultsTime: document.getElementById('results-time'),
    resultsList: document.getElementById('results-list'),
    pagination: document.getElementById('pagination'),

    // Summary
    searchSummary: document.getElementById('search-summary'),
    summaryText: document.getElementById('summary-text'),

    // Analytics
    mainAnalytics: document.getElementById('analytics-view'),

    // Mining
    mainMining: document.getElementById('mining-view'),


    // Navigation
    navBtns: document.querySelectorAll('.nav-btn'),

    // Loading
    loadingOverlay: document.getElementById('loading-overlay'),

    // Status Sidebar
    statusToggle: document.getElementById('status-toggle'),
    statusSidebar: document.getElementById('status-sidebar'),
    closeSidebar: document.getElementById('close-sidebar'),
    refreshStatus: document.getElementById('refresh-status'),

    // Status Indicators
    statusBackend: document.getElementById('status-backend'),
    statusDb: document.getElementById('status-db'),
    statusIndex: document.getElementById('status-index'),
    statusLlm: document.getElementById('status-llm'),

    // Metrics Sidebar
    metricsToggle: document.getElementById('metrics-toggle'),
    metricsSidebar: document.getElementById('metrics-sidebar'),
    closeMetrics: document.getElementById('close-metrics'),

    // Metric Values
    metricPrecision: document.getElementById('metric-precision'),
    metricRecall: document.getElementById('metric-recall'),
    metricF1: document.getElementById('metric-f1'),
    metricScore: document.getElementById('metric-score')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    // loadCorpusStats(); // Optional, if we want to show stats in placeholder
});

function initEventListeners() {
    // Search Input
    elements.searchBtn?.addEventListener('click', () => performSearch(elements.queryInput.value));

    elements.queryInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch(elements.queryInput.value);
    });

    // Logo click - back to home
    elements.logoLink?.addEventListener('click', (e) => {
        e.preventDefault();
        showHomePage();
    });

    // Navigation
    elements.navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            switchMode(mode);
        });
    });

    // Status Sidebar
    elements.statusToggle?.addEventListener('click', () => {
        elements.statusSidebar.classList.add('open');
        checkSystemStatus();
    });

    elements.closeSidebar?.addEventListener('click', () => {
        elements.statusSidebar.classList.remove('open');
    });

    elements.refreshStatus?.addEventListener('click', checkSystemStatus);

    // Metrics Sidebar
    elements.metricsToggle?.addEventListener('click', () => {
        elements.metricsSidebar.classList.add('open');
    });

    elements.closeMetrics?.addEventListener('click', () => {
        elements.metricsSidebar.classList.remove('open');
    });
}

// API Functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { status: 'error', message: error.message };
    }
}

async function loadCorpusStats() {
    const data = await apiCall('/stats');
    if (data && data.total_documents) {
        // Stats elements might not exist in placeholder logic, but we keep it safe
        const statsInfo = document.getElementById('stats-info');
        if (statsInfo) statsInfo.textContent = `Searching ${data.total_documents.toLocaleString()} articles`;

        const statDocs = document.getElementById('stat-docs');
        if (statDocs) statDocs.textContent = data.total_documents.toLocaleString();
    }

    // Load index info for vocabulary
    const indexInfo = await apiCall('/health');
    if (indexInfo && indexInfo.documents_indexed) {
        const statVocab = document.getElementById('stat-vocab');
        if (statVocab) statVocab.textContent = indexInfo.documents_indexed.toLocaleString();
    }
}

// Search Functions
async function performSearch(query, feelingLucky = false) {
    query = query.trim();
    if (!query) return;

    state.currentQuery = query;
    state.currentPage = 1;

    showLoading(true);
    const startTime = performance.now();

    const result = await apiCall('/search', {
        method: 'POST',
        body: JSON.stringify({
            query: query,
            top_k: 50
        })
    });

    state.searchTime = ((performance.now() - startTime) / 1000).toFixed(2);
    showLoading(false);

    if (result.status === 'success') {
        state.allResults = result.top_results || [];
        state.currentSummary = result.llm_summary || null;

        if (feelingLucky && state.allResults.length > 0) {
            // Open first result (simulate)
            alert(`Top result: ${state.allResults[0].title}`);
            return;
        }

        showResultsPage();
        renderResults();

        // If we have a summary but no results (fallback mode), ensure summary is shown
        renderSummary();

        // Update Metrics Sidebar
        if (result.metrics) {
            updateMetrics(result.metrics);
        }
    } else {
        state.allResults = [];
        state.currentSummary = null;
        showResultsPage();
        renderNoResults(query);
        updateMetrics(null); // Reset metrics
    }
}

function updateMetrics(metrics) {
    const format = (val) => val !== undefined && val !== null ? val.toFixed(3) : '-';

    if (elements.metricPrecision) elements.metricPrecision.textContent = metrics ? format(metrics.precision) : '-';
    if (elements.metricRecall) elements.metricRecall.textContent = metrics ? format(metrics.recall) : '-';
    if (elements.metricF1) elements.metricF1.textContent = metrics ? format(metrics.f1) : '-';
    // Use average_score if available, otherwise calculate from top results
    let avgScore = metrics ? metrics.average_score : null;
    if (elements.metricScore) elements.metricScore.textContent = avgScore !== null ? format(avgScore) : '-';
}

// UI Functions
function showHomePage() {
    elements.mainView.classList.remove('hidden');
    elements.mainAnalytics.classList.add('hidden');
    elements.mainMining?.classList.add('hidden');


    // Reset view
    elements.searchHero.style.display = 'block';
    elements.liveNewsContainer.classList.remove('hidden');
    elements.resultsContainer.classList.add('hidden');

    elements.queryInput.value = '';
    elements.queryInput.focus();

    updateNavButtons('search');
}

function showResultsPage() {
    elements.mainView.classList.remove('hidden');
    elements.mainAnalytics.classList.add('hidden');
    elements.mainMining?.classList.add('hidden');


    // Transition to results view
    elements.searchHero.style.display = 'none';
    elements.liveNewsContainer.classList.add('hidden'); // Optional: Hide news on search results
    elements.resultsContainer.classList.remove('hidden');

    elements.queryInput.value = state.currentQuery;

    updateNavButtons('search');
}

function showAnalyticsPage() {
    elements.mainView.classList.add('hidden');
    elements.mainAnalytics.classList.remove('hidden');
    elements.mainMining?.classList.add('hidden');


    updateNavButtons('analytics');
    loadAnalytics();
}

function showMiningPage() {
    elements.mainView.classList.add('hidden');
    elements.mainAnalytics.classList.add('hidden');
    elements.mainMining?.classList.remove('hidden');

    updateNavButtons('mining');

    // Initialize Mining Lab
    if (window.MiningLab) {
        window.MiningLab.init();
    }
}


function switchMode(mode) {
    state.currentMode = mode;
    if (mode === 'analytics') {
        showAnalyticsPage();
    } else if (mode === 'mining') {
        showMiningPage();
    } else {

        if (state.allResults.length > 0) {
            showResultsPage();
        } else {
            showHomePage();
        }
    }
}

function updateNavButtons(activeMode) {
    elements.navBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === activeMode);
    });
}

function showLoading(show) {
    state.isLoading = show;
    elements.loadingOverlay.classList.toggle('hidden', !show);
}

function renderResults() {
    const results = state.allResults;
    const start = (state.currentPage - 1) * state.resultsPerPage;
    const end = start + state.resultsPerPage;
    const pageResults = results.slice(start, end);

    // Update count
    elements.resultsCount.textContent = `About ${results.length} results`;
    elements.resultsTime.textContent = `(${state.searchTime} seconds)`;

    if (results.length === 0) {
        // If we have a fallback summary, don't show the "No results" generic message immediately
        // allowing the summary to be the focus.
        if (!state.currentSummary) {
            renderNoResults(state.currentQuery);
        } else {
            // Clear list but keep container ready
            elements.resultsList.innerHTML = '';
            elements.resultsCount.textContent = '0 news articles found';
            elements.pagination.innerHTML = '';
        }
        return;
    }

    // Render results
    elements.resultsList.innerHTML = pageResults.map((result, idx) => {
        const globalRank = start + idx + 1;
        const snippet = highlightTerms(result.content_excerpt || '', state.currentQuery);
        const source = result.metadata?.source || 'Unknown';
        const category = result.metadata?.category || '';
        const date = result.metadata?.published_at || '';
        const score = result.score ? result.score.toFixed(3) : '';

        return `
            <article class="result-item">
                <div class="result-url">
                    <div class="result-favicon">📰</div>
                    <div class="result-source-info">
                        <span class="result-source-name">${escapeHtml(source)}</span>
                        <span class="result-source-url">${category ? `Category: ${escapeHtml(category)}` : ''}</span>
                    </div>
                </div>
                <h3 class="result-title">
                    <a href="#" onclick="showArticleDetail(${result.doc_id}); return false;">
                        ${escapeHtml(result.title)}
                    </a>
                    ${score ? `<span class="result-score">Score: ${score}</span>` : ''}
                </h3>
                <p class="result-snippet">${snippet}</p>
                <div class="result-meta">
                    ${date && date !== 'None' ? `<span>📅 ${date}</span>` : ''}
                    ${result.metadata?.word_count ? `<span>📝 ${result.metadata.word_count} words</span>` : ''}
                </div>
            </article>
        `;
    }).join('');

    // Render pagination
    renderPagination(results.length);
}

function renderNoResults(query) {
    elements.resultsCount.textContent = 'No results found';
    elements.resultsTime.textContent = '';

    elements.resultsList.innerHTML = `
        <div class="no-results">
            <h3>No results found for "${escapeHtml(query)}"</h3>
            <p>Try different keywords or check your spelling.</p>
        </div>
    `;

    elements.pagination.innerHTML = '';
}

function renderPagination(totalResults) {
    const totalPages = Math.ceil(totalResults / state.resultsPerPage);
    if (totalPages <= 1) {
        elements.pagination.innerHTML = '';
        return;
    }

    let html = '';

    if (state.currentPage > 1) {
        html += `<button class="page-btn" onclick="goToPage(${state.currentPage - 1})">Previous</button>`;
    }

    for (let i = 1; i <= Math.min(totalPages, 10); i++) {
        html += `<button class="page-btn ${i === state.currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }

    if (state.currentPage < totalPages) {
        html += `<button class="page-btn" onclick="goToPage(${state.currentPage + 1})">Next</button>`;
    }

    elements.pagination.innerHTML = html;
}

function renderSummary() {
    const summary = state.currentSummary;
    if (summary) {
        elements.searchSummary.classList.remove('hidden');
        elements.summaryText.textContent = summary;
    } else {
        elements.searchSummary.classList.add('hidden');
    }
}

function goToPage(page) {
    state.currentPage = page;
    renderResults();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showArticleDetail(docId) {
    const article = state.allResults.find(r => r.doc_id === docId);
    if (article) {
        alert(`Article: ${article.title}\n\n${article.content_excerpt}`);
    }
}

// Analytics (placeholder)
async function loadAnalytics() {
    const stats = await apiCall('/stats');
    if (stats) {
        if (elements.statDocs) elements.statDocs.textContent = stats.total_documents?.toLocaleString() || '-';
    }
}

// Utility Functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function checkSystemStatus() {
    // Reset to checking state
    const setPending = (el) => {
        if (el) { el.textContent = 'Checking...'; el.className = 'status-value pending'; }
    };

    setPending(elements.statusBackend);
    setPending(elements.statusDb);
    setPending(elements.statusIndex);
    setPending(elements.statusLlm);

    try {
        const startTime = performance.now();
        const data = await apiCall('/health');
        const latency = Math.round(performance.now() - startTime);

        if (data && data.status) {
            // Backend Online
            if (elements.statusBackend) {
                elements.statusBackend.textContent = `Online (${latency}ms)`;
                elements.statusBackend.className = 'status-value online';
            }

            // Database
            if (elements.statusDb) {
                elements.statusDb.textContent = data.database === 'connected' ? 'Connected' : 'Error';
                elements.statusDb.className = data.database === 'connected' ? 'status-value online' : 'status-value offline';
            }

            // Index
            if (elements.statusIndex) {
                elements.statusIndex.textContent = `${data.documents_indexed} docs`;
                elements.statusIndex.className = 'status-value';
            }

            // LLM
            if (elements.statusLlm) {
                const llmStatus = data.llm || 'unavailable';
                elements.statusLlm.textContent = llmStatus === 'available' ? 'Ready' : 'Offline';
                elements.statusLlm.className = llmStatus === 'available' ? 'status-value online' : 'status-value offline';
            }
        }
    } catch (e) {
        if (elements.statusBackend) {
            elements.statusBackend.textContent = 'Offline';
            elements.statusBackend.className = 'status-value offline';
        }
    }
}

function highlightTerms(text, query) {
    if (!text || !query) return escapeHtml(text);

    const terms = query.toLowerCase().split(/\s+/).filter(t => t.length > 2);
    let result = escapeHtml(text);

    terms.forEach(term => {
        const regex = new RegExp(`(${term})`, 'gi');
        result = result.replace(regex, '<em>$1</em>');
    });

    return result;
}

// Make functions globally accessible
window.goToPage = goToPage;
window.showArticleDetail = showArticleDetail;
