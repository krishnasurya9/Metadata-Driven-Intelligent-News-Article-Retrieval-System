/**
 * Mining Lab - All 5 Modules
 * Module 1: Data Warehousing & ETL
 * Module 2: Data Preprocessing
 * Module 3: Association Rule Mining
 * Module 4: Automated Classification
 * Module 5: Clustering & Outlier Detection
 */

const MiningLab = {

    init() {
        this.bindTabSwitching();
        this.bindModuleButtons();
        // Auto-load warehouse stats when mining view becomes active
        document.querySelectorAll('.nav-btn[data-mode="mining"]').forEach(btn => {
            btn.addEventListener('click', () => this.loadWarehouseStats());
        });
    },

    // ── Tab Switching ───────────────────────────────────────────────
    bindTabSwitching() {
        document.querySelectorAll('.mining-nav-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const cur = e.currentTarget;
                // Update active nav item
                document.querySelectorAll('.mining-nav-item').forEach(b => b.classList.remove('active'));
                cur.classList.add('active');

                // Show target panel
                const targetId = cur.dataset.target;
                document.querySelectorAll('.mining-panel').forEach(p => p.classList.remove('active-panel'));
                const panel = document.getElementById(targetId);
                if (panel) panel.classList.add('active-panel');

                // Update breadcrumb
                const breadcrumb = document.getElementById('mining-active-module-name');
                if (breadcrumb) {
                    const label = cur.querySelector('.mining-nav-label')?.textContent || '';
                    breadcrumb.textContent = label;
                }
            });
        });
    },

    // ── Bind Module Action Buttons ─────────────────────────────────
    bindModuleButtons() {
        document.getElementById('run-warehouse-stats')?.addEventListener('click', () => this.loadWarehouseStats());
        document.getElementById('run-load-data')?.addEventListener('click', () => this.loadDataset());
        document.getElementById('run-preprocessing-demo')?.addEventListener('click', () => this.runPreprocessingDemo());
        document.getElementById('run-association')?.addEventListener('click', () => this.runAssociationRules());
        document.getElementById('run-classification')?.addEventListener('click', () => this.runClassification());
        document.getElementById('run-clustering')?.addEventListener('click', () => this.runClustering());

        // Initialize warehouse upload zone and local data
        this.initWarehouse();
    },


    // ═══════════════════════════════════════════════════════════════
    // DATA WAREHOUSE & ETL
    // ═══════════════════════════════════════════════════════════════

    initWarehouse() {
        // Wire upload zone interactions
        const dropZone = document.getElementById('upload-drop-zone');
        const fileInput = document.getElementById('csv-upload-input');
        const browseLink = document.getElementById('upload-browse-link');

        if (browseLink) {
            browseLink.addEventListener('click', e => { e.preventDefault(); fileInput?.click(); });
        }

        if (dropZone) {
            dropZone.addEventListener('click', () => fileInput?.click());
            dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
            dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
            dropZone.addEventListener('drop', e => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
                const file = e.dataTransfer?.files[0];
                if (file && file.name.endsWith('.csv')) {
                    MiningLab.uploadCSV(file);
                } else {
                    MiningLab.setUploadStatus('⚠ Please drop a valid .csv file', 'error');
                }
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', () => {
                if (fileInput.files[0]) MiningLab.uploadCSV(fileInput.files[0]);
            });
        }

        // Auto-load local data info
        this.loadLocalDataInfo();
    },

    async loadLocalDataInfo() {
        const infoEl = document.getElementById('local-data-info');
        if (!infoEl) return;
        try {
            const res = await fetch('http://localhost:5000/api/data/info');
            const data = await res.json();

            const csvFiles = (data.local_files || []).filter(f => f.name.endsWith('.csv'));
            const dbFiles = (data.local_files || []).filter(f => f.name.endsWith('.duckdb'));
            const wh = data.warehouse || {};

            let html = '';
            if (wh.total_documents > 0) {
                html += `<strong>${(wh.total_documents || 0).toLocaleString()}</strong> articles in warehouse · `;
                html += `${wh.total_categories || 0} categories · ${wh.total_sources || 0} sources<br>`;
            }
            if (csvFiles.length > 0) {
                html += `📄 CSV files: ${csvFiles.map(f => `${f.name} (${f.size_mb} MB)`).join(', ')}<br>`;
            }
            if (dbFiles.length > 0) {
                html += `🗄 DuckDB: ${dbFiles.map(f => `${f.name} (${f.size_mb} MB)`).join(', ')}`;
            }
            if (!html) html = 'No local data files found.';
            infoEl.innerHTML = html;
        } catch (e) {
            infoEl.textContent = 'Backend not reachable — start the server to see local data info.';
        }
    },

    setUploadStatus(message, type = 'info') {
        const bar = document.getElementById('upload-status');
        if (!bar) return;
        bar.style.display = 'block';
        bar.textContent = message;
        bar.style.color = type === 'error' ? '#dc2626' : type === 'success' ? '#16a34a' : '#555';
    },

    async uploadCSV(file) {
        const mode = document.getElementById('upload-mode')?.value || 'append';
        this.setUploadStatus(`Uploading ${file.name} (${mode} mode)...`);
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('mode', mode);
            const res = await fetch('http://localhost:5000/api/data/upload', { method: 'POST', body: formData });
            const result = await res.json();
            if (result.status === 'success') {
                const mapping = result.schema_mapping || {};
                const mapStr = Object.entries(mapping).map(([k, v]) => `${k}→${v}`).join(', ');
                this.setUploadStatus(
                    `✓ ${file.name} — ${(result.documents_loaded || 0).toLocaleString()} articles ingested (${mode}). ` +
                    `Total: ${(result.total_in_warehouse || 0).toLocaleString()}. ` +
                    `Schema: ${mapStr || 'auto-derived'}`,
                    'success'
                );
                this.loadLocalDataInfo();
                this.loadWarehouseStats();
            } else {
                this.setUploadStatus(`⚠ ${result.message}`, 'error');
            }
        } catch (e) {
            this.setUploadStatus(`⚠ Upload failed: ${e.message}`, 'error');
        }
    },

    async loadWarehouseStats() {
        const container = document.getElementById('warehouse-results');
        container.innerHTML = '<div class="placeholder-box">Loading warehouse statistics...</div>';

        try {
            const [statsRes, categoriesRes, sourcesRes] = await Promise.all([
                fetch('http://localhost:5000/api/stats'),
                fetch('http://localhost:5000/api/categories'),
                fetch('http://localhost:5000/api/sources')
            ]);

            const stats = await statsRes.json();
            const categories = await categoriesRes.json();
            const sources = await sourcesRes.json();

            const topCategory = Object.entries(categories.distribution || {})
                .sort((a, b) => b[1] - a[1])[0];
            const topSource = Object.entries(sources.distribution || {})
                .sort((a, b) => b[1] - a[1])[0];

            const dateRange = stats.date_range;
            const dateStr = dateRange ? `${dateRange.from?.slice(0, 10) || '—'} to ${dateRange.to?.slice(0, 10) || '—'}` : 'N/A';

            container.innerHTML = `
                <div class="warehouse-grid">
                    <div class="warehouse-stat-card">
                        <span class="warehouse-stat-value">${(stats.total_documents || 0).toLocaleString()}</span>
                        <span class="warehouse-stat-label">Total Articles</span>
                    </div>
                    <div class="warehouse-stat-card">
                        <span class="warehouse-stat-value">${Object.keys(categories.distribution || {}).length}</span>
                        <span class="warehouse-stat-label">Categories</span>
                    </div>
                    <div class="warehouse-stat-card">
                        <span class="warehouse-stat-value">${Object.keys(sources.distribution || {}).length}</span>
                        <span class="warehouse-stat-label">News Sources</span>
                    </div>
                    <div class="warehouse-stat-card">
                        <span class="warehouse-stat-value">${Math.round(stats.avg_word_count || 0)}</span>
                        <span class="warehouse-stat-label">Avg Word Count</span>
                    </div>
                    <div class="warehouse-stat-card">
                        <span class="warehouse-stat-value">${topCategory ? topCategory[1].toLocaleString() : 'N/A'}</span>
                        <span class="warehouse-stat-label">Top: ${topCategory ? topCategory[0] : '—'}</span>
                    </div>
                    <div class="warehouse-stat-card">
                        <span class="warehouse-stat-value">${topSource ? topSource[1].toLocaleString() : 'N/A'}</span>
                        <span class="warehouse-stat-label">Top: ${topSource ? topSource[0] : '—'}</span>
                    </div>
                </div>
                <div style="margin-top:16px; display:flex; justify-content:space-between; color:#888; font-size:12px;">
                    <span>Engine: DuckDB · Schema: Unified articles table</span>
                    <span>Date Range: ${dateStr}</span>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div class="placeholder-box">⚠ Backend not reachable: ${e.message}</div>`;
        }
    },

    async loadDataset() {
        const mode = document.getElementById('load-mode')?.value || 'replace';
        const container = document.getElementById('warehouse-results');
        container.innerHTML = `<div class="placeholder-box">Re-ingesting default CSV (${mode} mode)...</div>`;
        try {
            const res = await fetch('http://localhost:5000/api/data/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            });
            const result = await res.json();
            if (result.status === 'success') {
                const mapping = result.schema_mapping || {};
                const mapStr = Object.entries(mapping).map(([k, v]) => `${k} → ${v}`).join(' · ');

                container.innerHTML = `
                    <div class="warehouse-grid">
                        <div class="warehouse-stat-card">
                            <span class="warehouse-stat-value">${(result.documents_loaded || 0).toLocaleString()}</span>
                            <span class="warehouse-stat-label">Articles Ingested</span>
                        </div>
                        <div class="warehouse-stat-card">
                            <span class="warehouse-stat-value">${(result.total_in_warehouse || 0).toLocaleString()}</span>
                            <span class="warehouse-stat-label">Total in Warehouse</span>
                        </div>
                        <div class="warehouse-stat-card">
                            <span class="warehouse-stat-value">${(result.categories_found || []).length}</span>
                            <span class="warehouse-stat-label">Categories</span>
                        </div>
                        <div class="warehouse-stat-card">
                            <span class="warehouse-stat-value">${result.sources_found || 0}</span>
                            <span class="warehouse-stat-label">Sources</span>
                        </div>
                    </div>
                    <div style="margin-top:16px; color:#888; font-size:12px;">
                        <strong>Auto-Schema:</strong> ${mapStr || 'direct mapping'}<br>
                        <strong>Mode:</strong> ${mode} · <strong>File:</strong> ${result.file || 'news_articles.csv'}
                    </div>
                `;
                this.loadLocalDataInfo();
            } else {
                container.innerHTML = `<div class="placeholder-box">⚠ ${result.message}</div>`;
            }
        } catch (e) {
            container.innerHTML = `<div class="placeholder-box">⚠ ${e.message}</div>`;
        }
    },

    // ═══════════════════════════════════════════════════════════════
    // MODULE 2: Data Preprocessing Demo
    // ═══════════════════════════════════════════════════════════════
    async runPreprocessingDemo() {
        const outputEl = document.getElementById('preprocessing-output');
        outputEl.innerHTML = '<div style="color:#888;margin-top:12px;">Fetching a sample article to demonstrate preprocessing...</div>';

        try {
            const res = await fetch('http://localhost:5000/api/stats');
            const stats = await res.json();

            // Simulate a preprocessing demo with real corpus stats
            const sampleText = "The Federal Reserve announced new economic policies affecting global markets and technology stocks.";
            const tokens = sampleText.toLowerCase().replace(/[^a-z\s]/g, '').split(' ');
            const stopwords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are', 'was', 'were', 'new', 'be'];
            const filtered = tokens.filter(t => !stopwords.includes(t) && t.length > 2);

            outputEl.innerHTML = `
                <div style="margin-top:20px;">
                    <h4 style="color:#555;font-size:13px;margin-bottom:12px;text-transform:uppercase;letter-spacing:0.05em;">
                        Live Demo — Sample Article
                    </h4>
                    <div style="background:#f3f3f3;border:1px solid #e5e5e5;border-radius:8px;padding:14px;margin-bottom:12px;">
                        <div style="color:#888;font-size:11px;margin-bottom:4px;">RAW TEXT</div>
                        <div style="color:#111;font-size:13px;">"${sampleText}"</div>
                    </div>
                    <div style="background:#f3f3f3;border:1px solid #e5e5e5;border-radius:8px;padding:14px;margin-bottom:12px;">
                        <div style="color:#888;font-size:11px;margin-bottom:4px;">STEP 1 — TOKENIZATION (${tokens.length} tokens)</div>
                        <div style="color:#111;font-size:13px;">${tokens.map(t => `<span style="background:#e5e5e5;border-radius:4px;padding:2px 6px;margin:2px;display:inline-block;">${t}</span>`).join('')}</div>
                    </div>
                    <div style="background:#f3f3f3;border:1px solid #e5e5e5;border-radius:8px;padding:14px;margin-bottom:12px;">
                        <div style="color:#888;font-size:11px;margin-bottom:4px;">STEP 2 — AFTER STOPWORD REMOVAL (${filtered.length} tokens)</div>
                        <div style="color:#111;font-size:13px;">${filtered.map(t => `<span style="background:#d1d5db;border-radius:4px;padding:2px 6px;margin:2px;display:inline-block;">${t}</span>`).join('')}</div>
                    </div>
                    <div style="background:#f3f3f3;border:1px solid #e5e5e5;border-radius:8px;padding:14px;">
                        <div style="color:#888;font-size:11px;margin-bottom:4px;">CORPUS SIZE</div>
                        <div style="color:#333;font-size:13px;">
                            ${(stats.total_documents || 0).toLocaleString()} articles vectorized with TF-IDF (max 10,000 features, unigrams + bigrams)
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            outputEl.innerHTML = `<div style="color:#888;margin-top:12px;">⚠ ${e.message}</div>`;
        }
    },

    // ═══════════════════════════════════════════════════════════════
    // MODULE 3: Association Rule Mining
    // ═══════════════════════════════════════════════════════════════
    async runAssociationRules() {
        const container = document.getElementById('association-results');
        const minSupport = document.getElementById('min-support')?.value || 0.05;
        const minConfidence = document.getElementById('min-confidence')?.value || 0.2;
        container.innerHTML = '<div class="placeholder-box">Mining association rules... this may take a moment.</div>';

        try {
            const res = await fetch(`http://localhost:5000/api/mining/association?min_support=${minSupport}&min_confidence=${minConfidence}`);
            const result = await res.json();

            if (result.status === 'success') {
                this.renderAssociationRules(result.data, container);
            } else {
                container.innerHTML = `<div class="placeholder-box">⚠ ${result.message}</div>`;
            }
        } catch (e) {
            container.innerHTML = `<div class="placeholder-box">⚠ ${e.message}</div>`;
        }
    },

    renderAssociationRules(data, container) {
        if (!data.rules || data.rules.length === 0) {
            container.innerHTML = '<div class="placeholder-box">No significant rules found. Try lowering the thresholds.</div>';
            return;
        }
        let html = `
            <div class="stats-box">
                <span><strong>${data.transaction_count}</strong> transactions analyzed</span>
                <span><strong>${data.rules.length}</strong> rules found</span>
                <span>Support ≥ ${document.getElementById('min-support')?.value || '0.05'} · Confidence ≥ ${document.getElementById('min-confidence')?.value || '0.2'}</span>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Antecedent → Consequent</th>
                        <th>Support</th>
                        <th>Confidence</th>
                        <th>Lift</th>
                    </tr>
                </thead>
                <tbody>
        `;
        data.rules.slice(0, 30).forEach(rule => {
            const liftColor = rule.lift > 1.5 ? '#16a34a' : rule.lift > 1 ? '#ca8a04' : '#dc2626';
            html += `
                <tr>
                    <td><strong>${rule.antecedent}</strong> → ${rule.consequent}</td>
                    <td>${rule.support}</td>
                    <td><strong>${rule.confidence}</strong></td>
                    <td style="color:${liftColor};font-weight:600;">${rule.lift}</td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    },

    // ═══════════════════════════════════════════════════════════════
    // MODULE 4: Classification
    // ═══════════════════════════════════════════════════════════════
    async runClassification() {
        const container = document.getElementById('classification-results');
        container.innerHTML = '<div class="placeholder-box">Training Random Forest classifier... (~15–30 seconds)</div>';

        try {
            const res = await fetch('http://localhost:5000/api/mining/classification', { method: 'POST' });
            const result = await res.json();

            if (result.status === 'success') {
                this.renderClassification(result.data, container);
            } else {
                container.innerHTML = `<div class="placeholder-box">⚠ ${result.message}</div>`;
            }
        } catch (e) {
            container.innerHTML = `<div class="placeholder-box">⚠ ${e.message}</div>`;
        }
    },

    renderClassification(data, container) {
        const accuracy = Math.round(data.accuracy * 100);
        const report = data.detailed_report;

        let rows = '';
        for (const [key, value] of Object.entries(report)) {
            if (['accuracy', 'macro avg', 'weighted avg'].includes(key)) continue;
            rows += `
                <tr>
                    <td>${key}</td>
                    <td>${value['precision'].toFixed(2)}</td>
                    <td>${value['recall'].toFixed(2)}</td>
                    <td>${value['f1-score'].toFixed(2)}</td>
                    <td>${value['support']}</td>
                </tr>
            `;
        }

        container.innerHTML = `
            <div class="model-score">
                <div class="score-circle">
                    <span>${accuracy}%</span>
                    <small>Accuracy</small>
                </div>
                <div class="score-info">
                    <h4>Random Forest Classifier</h4>
                    <p>${data.classes.length} categories · 100 trees · TF-IDF features (top 2000)</p>
                </div>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Precision</th>
                        <th>Recall</th>
                        <th>F1-Score</th>
                        <th>Support</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    },

    // ═══════════════════════════════════════════════════════════════
    // MODULE 5: Clustering & Outlier Detection
    // ═══════════════════════════════════════════════════════════════
    async runClustering() {
        const container = document.getElementById('clustering-results');
        const nClusters = document.getElementById('num-clusters')?.value || 5;
        container.innerHTML = '<div class="placeholder-box">Running K-Means clustering...</div>';

        try {
            const res = await fetch('http://localhost:5000/api/mining/clustering', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ n_clusters: parseInt(nClusters) })
            });
            const result = await res.json();

            if (result.status === 'success') {
                this.renderClustering(result.data, container);
            } else {
                container.innerHTML = `<div class="placeholder-box">⚠ ${result.message}</div>`;
            }
        } catch (e) {
            container.innerHTML = `<div class="placeholder-box">⚠ ${e.message}</div>`;
        }
    },

    renderClustering(data, container) {
        const totalDocs = data.clusters.reduce((sum, c) => sum + c.size, 0);
        const outlierThreshold = Math.floor(totalDocs / data.n_clusters * 0.2);

        let cards = data.clusters.map(cluster => {
            const isOutlier = cluster.size <= outlierThreshold && cluster.size > 0;
            return `
                <div class="cluster-card" ${isOutlier ? 'style="border-color:#ca8a04;"' : ''}>
                    <h3>Cluster ${cluster.cluster_id + 1} ${isOutlier ? '⚠️' : ''}</h3>
                    <div class="cluster-size">${cluster.size} documents ${isOutlier ? '· Potential outlier group' : ''}</div>
                    <div class="cluster-terms">
                        <strong>Keywords:</strong> ${cluster.top_terms.join(', ')}
                    </div>
                    <div class="cluster-samples">
                        <strong style="font-size:12px;color:#888;">Sample Articles:</strong>
                        <ul>${cluster.samples.map(s => `<li>${s}</li>`).join('')}</ul>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `
            <div class="stats-box">
                <span><strong>${data.n_clusters}</strong> clusters</span>
                <span><strong>${totalDocs}</strong> documents clustered</span>
                <span>Algorithm: K-Means · Vectorizer: TF-IDF (1000 features)</span>
            </div>
            <div class="clusters-grid">${cards}</div>
        `;
    }
};

window.MiningLab = MiningLab;

// Auto-init when DOM is ready (mode-toggle.js loads first)
document.addEventListener('DOMContentLoaded', () => MiningLab.init());
