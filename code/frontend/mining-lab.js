/**
 * Mining Lab - CDM Enhanced
 * Visual rule cards, confidence meters, live predict, no-gridline charts
 */

const MiningLab = {
    charts: {},

    init() {
        this.injectNewModules();
        this.bindTabSwitching();
        this.bindModuleButtons();
        document.querySelectorAll('.nav-btn[data-mode="mining"]').forEach(btn => {
            btn.addEventListener('click', () => this.loadWarehouseStats());
        });
    },

    injectNewModules() {
        const nav = document.querySelector('.mining-sidebar-nav');
        const main = document.querySelector('.mining-main');
        if (!nav || !main || document.getElementById('mining-temporal')) return;

        nav.insertAdjacentHTML('beforeend', `
            <button class="mining-nav-item" data-target="mining-temporal">
                <span class="mining-nav-icon">📈</span>
                <div class="mining-nav-text">
                    <span class="mining-nav-label">Temporal Patterns</span>
                    <span class="mining-nav-sub">Time-Series Mining</span>
                </div>
            </button>
            <button class="mining-nav-item" data-target="mining-keywords">
                <span class="mining-nav-icon">🔠</span>
                <div class="mining-nav-text">
                    <span class="mining-nav-label">Keyword Prominence</span>
                    <span class="mining-nav-sub">TF-IDF Vocabulary</span>
                </div>
            </button>
        `);

        main.insertAdjacentHTML('beforeend', `
            <div id="mining-temporal" class="mining-panel">
                <div class="panel-header">
                    <div>
                        <h2 class="panel-title">📈 Temporal Pattern Mining</h2>
                        <p class="panel-desc">Analyze article volume trends across categories over time using linear regression.</p>
                    </div>
                    <div class="panel-actions">
                        <button id="run-temporal" class="run-btn">Analyze Temporal Patterns</button>
                    </div>
                </div>
                <div id="temporal-results" class="panel-results">
                    <div class="placeholder-box">Run analysis to view time-series trends.</div>
                </div>
            </div>
            <div id="mining-keywords" class="mining-panel">
                <div class="panel-header">
                    <div>
                        <h2 class="panel-title">🔠 Keyword Prominence</h2>
                        <p class="panel-desc">TF-IDF vocabulary analysis identifying globally prominent and category-defining terms.</p>
                    </div>
                    <div class="panel-actions">
                        <button id="run-keywords" class="run-btn">Analyze Keywords</button>
                    </div>
                </div>
                <div id="keywords-results" class="panel-results">
                    <div class="placeholder-box">Run analysis to view dominant vocabulary.</div>
                </div>
            </div>
        `);

        // Live predict section injected before classification results
        const classResults = document.getElementById('classification-results');
        if (classResults && !document.getElementById('live-predict-text')) {
            classResults.insertAdjacentHTML('beforebegin', `
                <div class="live-predict-section" id="live-predict-wrapper">
                    <h4>Live Article Classifier</h4>
                    <div class="live-predict-row">
                        <textarea id="live-predict-text" class="live-predict-input"
                            placeholder="Paste any news headline or article text to classify..."></textarea>
                        <button id="live-predict-btn" class="live-predict-btn">Classify</button>
                    </div>
                    <div class="predict-progress" id="predict-progress">
                        <div class="predict-progress-inner"></div>
                    </div>
                    <div class="live-predict-result" id="live-predict-result">
                        <div class="predict-category" id="predict-category-output"></div>
                        <div class="confidence-meter-wrap" id="predict-confidence"></div>
                    </div>
                </div>
            `);
        }

        const clusterActions = document.querySelector('#mining-clustering .panel-actions');
        if (clusterActions && !document.getElementById('run-elbow')) {
            clusterActions.insertAdjacentHTML('afterbegin',
                '<button id="run-elbow" class="run-btn run-btn-secondary" style="margin-right:10px;">Find Optimal K</button>');
        }
    },

    bindTabSwitching() {
        document.querySelectorAll('.mining-nav-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const cur = e.currentTarget;
                document.querySelectorAll('.mining-nav-item').forEach(b => b.classList.remove('active'));
                cur.classList.add('active');
                const targetId = cur.dataset.target;
                document.querySelectorAll('.mining-panel').forEach(p => p.classList.remove('active-panel'));
                document.getElementById(targetId)?.classList.add('active-panel');
                const bc = document.getElementById('mining-active-module-name');
                if (bc) bc.textContent = cur.querySelector('.mining-nav-label')?.textContent || '';
            });
        });
    },

    bindModuleButtons() {
        document.getElementById('run-warehouse-stats')?.addEventListener('click', () => this.loadWarehouseStats());
        document.getElementById('run-load-data')?.addEventListener('click', () => this.loadDataset());
        document.getElementById('run-preprocessing-demo')?.addEventListener('click', () => this.runPreprocessingDemo());
        document.getElementById('run-association')?.addEventListener('click', () => this.runAssociationRules());
        document.getElementById('run-classification')?.addEventListener('click', () => this.runClassification());
        document.getElementById('run-clustering')?.addEventListener('click', () => this.runClustering());
        document.getElementById('run-elbow')?.addEventListener('click', () => this.runElbowCurve());
        document.getElementById('run-pca')?.addEventListener('click', () => this.runPCAScatter());
        document.getElementById('run-temporal')?.addEventListener('click', () => this.runTemporal());
        document.getElementById('run-keywords')?.addEventListener('click', () => this.runKeywords());
        document.getElementById('live-predict-btn')?.addEventListener('click', () => this.runLivePredict());
        document.getElementById('review-mode-toggle')?.addEventListener('change', (e) => {
            document.querySelector('.mining-view')?.classList.toggle('review-mode', !!e.target.checked);
        });
        this.initWarehouse();
    },

    setRunStatus(state, text) {
        const badge = document.getElementById('cdm-run-status');
        if (!badge) return;
        badge.className = `cdm-status-badge ${state}`;
        badge.textContent = text;
    },

    renderStandardSections({ method, params, metrics, interpretation }) {
        const metricRows = Object.entries(metrics || {}).map(([k, v]) =>
            `<div class="rule-stat-chip">${k}: <strong>${v}</strong></div>`
        ).join('');
        return `
            <div class="result-card-standard">
                <h4>Method</h4>
                <p>${method || 'N/A'}</p>
            </div>
            <div class="result-card-standard">
                <h4>Input Params</h4>
                <p>${params || 'Default params'}</p>
            </div>
            <div class="result-card-standard">
                <h4>Key Metrics</h4>
                <div style="display:flex;flex-wrap:wrap;gap:8px;">${metricRows || '<span class="rule-stat-chip">No metrics</span>'}</div>
            </div>
            <div class="result-card-standard">
                <h4>Interpretation</h4>
                <p>${interpretation || 'No interpretation available.'}</p>
            </div>
        `;
    },

    // Warehouse
    initWarehouse() {
        this.loadLocalDataInfo();
        const dropZone = document.getElementById('upload-drop-zone');
        const fileInput = document.getElementById('csv-upload-input');
        const browseLink = document.getElementById('upload-browse-link');
        dropZone?.addEventListener('click', () => fileInput?.click());
        browseLink?.addEventListener('click', e => { e.preventDefault(); fileInput?.click(); });
        fileInput?.addEventListener('change', () => { if (fileInput.files[0]) this.uploadFile(fileInput.files[0]); });
        dropZone?.addEventListener('dragover', e => { e.preventDefault(); dropZone.style.borderColor = 'var(--accent)'; });
        dropZone?.addEventListener('dragleave', () => { dropZone.style.borderColor = ''; });
        dropZone?.addEventListener('drop', e => {
            e.preventDefault(); dropZone.style.borderColor = '';
            if (e.dataTransfer.files[0]) this.uploadFile(e.dataTransfer.files[0]);
        });
    },

    async loadLocalDataInfo() {
        const el = document.getElementById('local-data-info');
        if (!el) return;
        try {
            const r = await fetch('http://localhost:5000/api/data/info');
            const d = await r.json();
            const count = d?.data?.storage?.total_articles ?? '?';
            el.innerHTML = `<span style="font-weight:700;color:var(--accent)">${Number(count).toLocaleString()}</span> articles loaded`;
        } catch { el.innerHTML = 'Backend unreachable'; }
    },

    async loadWarehouseStats() {
        const el = document.getElementById('warehouse-results');
        if (!el) return;
        el.innerHTML = '<div class="placeholder-box">Loading...</div>';
        try {
            const r = await fetch('http://localhost:5000/api/stats');
            const s = (await r.json())?.data ?? {};
            el.innerHTML = `<div class="warehouse-grid">
                <div class="warehouse-stat-card"><span class="warehouse-stat-value">${(s.total_articles||0).toLocaleString()}</span><span class="warehouse-stat-label">Articles</span></div>
                <div class="warehouse-stat-card"><span class="warehouse-stat-value">${s.categories||0}</span><span class="warehouse-stat-label">Categories</span></div>
                <div class="warehouse-stat-card"><span class="warehouse-stat-value">${s.sources||0}</span><span class="warehouse-stat-label">Sources</span></div>
            </div>`;
        } catch(e) { el.innerHTML = `<div class="placeholder-box">Error: ${e.message}</div>`; }
    },

    async loadDataset() { this.loadWarehouseStats(); },

    async uploadFile(file) {
        const statusEl = document.getElementById('upload-status');
        if (statusEl) { statusEl.style.display='block'; statusEl.textContent='Uploading...'; }
        const fd = new FormData();
        fd.append('file', file);
        fd.append('mode', document.getElementById('upload-mode')?.value || 'append');
        try {
            const r = await fetch('http://localhost:5000/api/data/upload', { method:'POST', body:fd });
            const result = await r.json();
            if (statusEl) statusEl.textContent = result.status==='success' ? 'Upload complete.' : result.message;
        } catch(e) { if (statusEl) statusEl.textContent = `Error: ${e.message}`; }
    },

    // Preprocessing
    async runPreprocessingDemo() {
        const el = document.getElementById('preprocessing-output');
        this.setRunStatus('running', 'Running: Preprocessing');
        el.innerHTML = '<div class="placeholder-box">Loading...</div>';
        try {
            const r = await fetch('http://localhost:5000/api/cdm/stats');
            const result = await r.json();
            if (result.status === 'success') {
                const d = result.data;
                el.innerHTML = `<div class="warehouse-grid">
                    <div class="warehouse-stat-card"><span class="warehouse-stat-value">${(d.total_docs||0).toLocaleString()}</span><span class="warehouse-stat-label">Raw Docs</span></div>
                    <div class="warehouse-stat-card"><span class="warehouse-stat-value">${(d.docs_after_cleaning||0).toLocaleString()}</span><span class="warehouse-stat-label">After Cleaning</span></div>
                    <div class="warehouse-stat-card"><span class="warehouse-stat-value">${d.avg_text_length||0}</span><span class="warehouse-stat-label">Avg Words</span></div>
                    <div class="warehouse-stat-card"><span class="warehouse-stat-value">${(d.vocabulary_size||0).toLocaleString()}</span><span class="warehouse-stat-label">Vocab Size</span></div>
                </div>`;
                this.setRunStatus('success', 'Success: Preprocessing');
            } else {
                this.setRunStatus('error', 'Failed: Preprocessing');
                el.innerHTML = `<div class="placeholder-box">Failed to load preprocessing stats. Ensure frozen_corpus.csv exists.</div>`;
            }
        } catch(e) {
            this.setRunStatus('error', 'Failed: Preprocessing');
            el.innerHTML = `<div class="placeholder-box">Request failed: ${e.message}</div>`;
        }
    },

    // Association Rules — visual cards
    async runAssociationRules() {
        const container = document.getElementById('association-results');
        const minSupport = document.getElementById('min-support')?.value || 0.05;
        const minConfidence = document.getElementById('min-confidence')?.value || 0.2;
        this.setRunStatus('running', 'Running: Association');
        container.innerHTML = '<div class="placeholder-box">Running FP-Growth... (~10s)</div>';
        try {
            const r = await fetch('http://localhost:5000/api/cdm/association', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({min_support: minSupport, min_confidence: minConfidence})
            });
            const result = await r.json();
            if (result.status === 'success') {
                const data = result.data;
                if (!data.rules || !data.rules.length) {
                    this.setRunStatus('error', 'Failed: Association');
                    container.innerHTML = '<div class="placeholder-box">No rules found. Try lower support/confidence values.</div>';
                    return;
                }
                const cards = data.rules.slice(0, 24).map((rule, i) => {
                    const liftCls = parseFloat(rule.lift) > 2 ? 'rule-lift-high' : '';
                    return `<div class="rule-card stagger-item" style="--i:${Math.floor(i/2)}">
                        <div class="rule-arrow-row">
                            <span class="rule-antecedent">${rule.antecedent}</span>
                            <span class="rule-arrow-symbol">&#8594;</span>
                            <span class="rule-consequent">${rule.consequent}</span>
                        </div>
                        <div class="rule-stats">
                            <span class="rule-stat-chip">Sup: ${rule.support}</span>
                            <span class="rule-stat-chip">Conf: ${rule.confidence}</span>
                            <span class="rule-stat-chip ${liftCls}">Lift: ${rule.lift}</span>
                        </div>
                    </div>`;
                }).join('');
                const standard = this.renderStandardSections({
                    method: data.method,
                    params: `min_support=${minSupport}, min_confidence=${minConfidence}`,
                    metrics: { rules: data.rules.length, itemsets: data.frequent_itemsets_found, transactions: data.transaction_count },
                    interpretation: data.interpretation
                });
                container.innerHTML = `${standard}<div class="rule-cards-grid">${cards}</div>`;
                this.setRunStatus('success', 'Success: Association');
            } else {
                this.setRunStatus('error', 'Failed: Association');
                container.innerHTML = `<div class="placeholder-box">${result.message || 'Association call failed. Check frozen corpus and thresholds.'}</div>`;
            }
        } catch(e) {
            this.setRunStatus('error', 'Failed: Association');
            container.innerHTML = `<div class="placeholder-box">Error: ${e.message}</div>`;
        }
    },

    // Classification — scorecards + confidence bars
    async runClassification() {
        const container = document.getElementById('classification-results');
        this.setRunStatus('running', 'Running: Classification');
        container.innerHTML = '<div class="placeholder-box">Benchmarking NB vs SVM... (~30s)</div>';
        try {
            const r = await fetch('http://localhost:5000/api/cdm/classify', { method:'POST' });
            const result = await r.json();
            if (result.status === 'success') {
                const d = result.data;
                const nb = d.naive_bayes;
                const svm = d.svm;
                const wname = (d.winner||'').toLowerCase();

                const makeCard = (label, clf, isWinner) => {
                    const pct = Math.round((clf.accuracy||0)*100);
                    const barCls = pct>=85?'good':pct>=70?'':'warn';
                    const cats = Object.keys(clf.classification_report||{})
                        .filter(k=>!['accuracy','macro avg','weighted avg'].includes(k));
                    const catBars = cats.map(cat => {
                        const f1 = clf.classification_report[cat]?.['f1-score']??0;
                        const fp = Math.round(f1*100);
                        return `<div style="margin-bottom:8px;">
                            <div class="confidence-label"><span>${cat}</span><span>${fp}%</span></div>
                            <div class="confidence-bar-track">
                                <div class="confidence-bar-fill ${fp>=85?'good':fp>=70?'':'warn'}" data-w="${fp}"></div>
                            </div></div>`;
                    }).join('');
                    return `<div class="classifier-card ${isWinner?'winner':''}">
                        <div class="classifier-name">${label} ${isWinner?'<span class="classifier-badge">Winner</span>':''}</div>
                        <div class="classifier-accuracy">${pct}%</div>
                        <div class="classifier-meta">Accuracy &middot; ${clf.training_time_seconds||'?'}s training</div>
                        <div style="margin-top:14px;">
                            <div class="confidence-label"><span>Overall</span><span>${pct}%</span></div>
                            <div class="confidence-bar-track">
                                <div class="confidence-bar-fill ${barCls}" data-w="${pct}"></div>
                            </div>
                        </div>
                        <div style="margin-top:14px;border-top:1px solid var(--border);padding-top:12px;">
                            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3);margin-bottom:10px;">F1 per Class</div>
                            ${catBars}
                        </div>
                    </div>`;
                };

                const makeCM = (label, cm) => {
                    if (!cm||!cm.length) return '';
                    const rows = cm.map((row,i)=>'<tr>'+row.map((v,j)=>
                        `<td class="${i===j?'cm-cell-hit':v>0?'cm-cell-miss':''}">${v}</td>`
                    ).join('')+'</tr>').join('');
                    return `<div class="confusion-matrix-wrap">
                        <h5>${label}</h5>
                        <table class="cm-table"><tbody>${rows}</tbody></table>
                    </div>`;
                };

                const standard = this.renderStandardSections({
                    method: 'Dual Classifier Benchmark (Naive Bayes vs Linear SVM)',
                    params: 'test_size=0.2, vectorizer=TF-IDF(1,2), max_features=10000',
                    metrics: {
                        winner: d.winner,
                        accuracy_delta: (d.accuracy_delta * 100).toFixed(2) + '%',
                        dataset_size: d.dataset_size
                    },
                    interpretation: d.recommendation
                });
                container.innerHTML = `${standard}
                    <div class="winner-banner">
                        <span>🏆</span>
                        <div><strong>${d.winner}</strong> wins by +${(d.accuracy_delta*100).toFixed(2)}% &mdash; ${d.recommendation||''}</div>
                    </div>
                    <div class="classifier-grid">
                        ${makeCard('Naive Bayes', nb, wname.includes('naive'))}
                        ${makeCard('Linear SVM', svm, wname.includes('svm'))}
                    </div>
                    <div class="confusion-grid">
                        ${makeCM('Naive Bayes Confusion Matrix', nb.confusion_matrix)}
                        ${makeCM('SVM Confusion Matrix', svm.confusion_matrix)}
                    </div>`;
                this.setRunStatus('success', 'Success: Classification');

                setTimeout(() => {
                    container.querySelectorAll('.confidence-bar-fill[data-w]').forEach(bar => {
                        requestAnimationFrame(() => { bar.style.width = bar.dataset.w + '%'; });
                    });
                }, 80);
            } else {
                this.setRunStatus('error', 'Failed: Classification');
                container.innerHTML = `<div class="placeholder-box">${result.message || 'Classification failed. Ensure frozen corpus is available.'}</div>`;
            }
        } catch(e) {
            this.setRunStatus('error', 'Failed: Classification');
            container.innerHTML = `<div class="placeholder-box">Error: ${e.message}</div>`;
        }
    },

    // Live Predict
    async runLivePredict() {
        const text = document.getElementById('live-predict-text')?.value?.trim();
        if (!text) return;
        const progress = document.getElementById('predict-progress');
        const resultEl = document.getElementById('live-predict-result');
        const catEl = document.getElementById('predict-category-output');
        const confEl = document.getElementById('predict-confidence');
        progress?.classList.add('running');
        resultEl?.classList.remove('visible');
        try {
            const r = await fetch('http://localhost:5000/api/cdm/predict', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({text})
            });
            const result = await r.json();
            progress?.classList.remove('running');
            if (result.status === 'success') {
                const cat = result.data.predicted_category || result.data.category || 'Unknown';
                const conf = Math.round((result.data.confidence||result.data.probability||0)*100);
                if (catEl) catEl.textContent = cat;
                if (confEl) {
                    confEl.innerHTML = `
                        <div class="confidence-label"><span>Confidence</span><span>${conf}%</span></div>
                        <div class="confidence-bar-track">
                            <div class="confidence-bar-fill ${conf>=80?'good':conf>=60?'':'warn'}" id="lpbar"></div>
                        </div>`;
                    setTimeout(() => { const b=document.getElementById('lpbar'); if(b) b.style.width=conf+'%'; }, 60);
                }
                resultEl?.classList.add('visible');
            }
        } catch(e) { progress?.classList.remove('running'); }
    },

    // Clustering
    async runClustering() {
        const container = document.getElementById('clustering-results');
        const k = document.getElementById('num-clusters')?.value || 4;
        this.setRunStatus('running', 'Running: Clustering');
        container.innerHTML = '<div class="placeholder-box">Running Bisecting K-Means + LSA...</div>';
        try {
            const r = await fetch('http://localhost:5000/api/cdm/cluster', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({n_clusters: k})
            });
            const result = await r.json();
            if (result.status === 'success') {
                const d = result.data;
                const cards = d.clusters.map((c, i) => {
                    const purity = (c.purity*100).toFixed(1);
                    return `<div class="cluster-card stagger-item" style="--i:${i};${c.is_outlier_cluster?'border:2px solid var(--red);':''}">
                        <h3 style="margin-bottom:10px;">Cluster ${c.cluster_id+1} ${c.is_outlier_cluster?'⚠️ Outlier':''}</h3>
                        <div class="confidence-label"><span>Purity</span><span>${purity}%</span></div>
                        <div class="confidence-bar-track" style="margin-bottom:10px;">
                            <div class="confidence-bar-fill good" style="width:${purity}%"></div>
                        </div>
                        <p style="font-size:12px;color:var(--text-2);margin-bottom:8px;"><strong>${c.dominant_category}</strong> &middot; ${c.size} docs (${c.percentage}%)</p>
                        <div class="keyword-cloud">
                            ${c.top_terms.slice(0,8).map(t=>`<span class="keyword-tag">${t}</span>`).join('')}
                        </div>
                    </div>`;
                }).join('');
                const standard = this.renderStandardSections({
                    method: d.method,
                    params: `n_clusters=${k}`,
                    metrics: { silhouette: d.silhouette_score, overall_purity: (d.overall_purity * 100).toFixed(1) + '%' },
                    interpretation: d.interpretation
                });
                container.innerHTML = `${standard}
                    <div class="stats-box" style="margin-bottom:16px;">
                        ${d.sampled?`<span>Sampled: ${d.sample_size} docs</span>`:''}
                        <span>Overall Purity: ${(d.overall_purity*100).toFixed(1)}%</span>
                        <span>Silhouette: ${d.silhouette_score.toFixed(3)}</span>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;">${cards}</div>`;
                this.setRunStatus('success', 'Success: Clustering');
            } else {
                this.setRunStatus('error', 'Failed: Clustering');
                container.innerHTML = `<div class="placeholder-box">${result.message || 'Clustering failed. Check K range and frozen data.'}</div>`;
            }
        } catch(e) {
            this.setRunStatus('error', 'Failed: Clustering');
            container.innerHTML = `<div class="placeholder-box">Error: ${e.message}</div>`;
        }
    },


    // PCA Scatter -- 2D projection of cluster assignments (CDM plan: Scatter Plots)
    async runPCAScatter(nClusters) {
        const container = document.getElementById('clustering-results');
        this.setRunStatus('running', 'Running: PCA');
        const existing = container.querySelector('#pca-canvas-wrap');
        if (existing) existing.remove();

        const k = nClusters || document.getElementById('num-clusters')?.value || 4;
        const loadEl = document.createElement('div');
        loadEl.className = 'placeholder-box';
        loadEl.id = 'pca-loading';
        loadEl.textContent = 'Computing 2D PCA projection... (~15s)';
        container.insertAdjacentElement('afterbegin', loadEl);

        try {
            const r = await fetch('http://localhost:5000/api/cdm/pca', {
                method: 'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({n_clusters: k, sample_size: 1500})
            });
            const result = await r.json();
            loadEl.remove();

            if (result.status === 'success') {
                const d = result.data;
                const clusterColors = ['#6366F1','#10B981','#EC4899','#F59E0B','#3B82F6','#8B5CF6','#EF4444','#06B6D4'];
                const clusterLabels = d.cluster_labels || {};

                // Group points by cluster
                const datasets = [];
                for (let c = 0; c < d.n_clusters; c++) {
                    const pts = d.points.filter(p => p.cluster === c);
                    datasets.push({
                        label: clusterLabels[String(c)] || ('Cluster ' + (c+1)),
                        data: pts.map(p => ({x: p.x, y: p.y, title: p.title})),
                        backgroundColor: (clusterColors[c] || '#999') + 'AA',
                        borderColor: clusterColors[c] || '#999',
                        borderWidth: 0.5,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    });
                }

                const wrap = document.createElement('div');
                wrap.id = 'pca-canvas-wrap';
                wrap.innerHTML = '<div style="width:100%;height:360px;margin-bottom:20px;"><canvas id="pcaChart"></canvas></div>' +
                    '<p style="text-align:center;font-size:12px;color:var(--text-3);">2D PCA Projection ' +
                    (d.sampled ? ('sampled ' + d.sample_size + ' docs') : '') + ' &middot; ' + d.total_points + ' points</p>';
                container.insertAdjacentElement('afterbegin', wrap);

                if (this.charts.pca) { this.charts.pca.destroy(); }
                const ctx = document.getElementById('pcaChart').getContext('2d');
                this.charts.pca = new Chart(ctx, {
                    type: 'scatter',
                    data: { datasets },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        animation: { duration: 600 },
                        plugins: {
                            legend: { labels: { font: { family: 'Inter', size: 11 }, usePointStyle: true, pointStyleWidth: 10 } },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        const pt = ctx.raw;
                                        return pt.title ? pt.title.substring(0, 60) : ctx.dataset.label;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { grid: { display: false }, ticks: { display: false }, title: { display: true, text: 'PCA Component 1', color: '#9CA3AF', font: { size: 10 } } },
                            y: { grid: { display: false }, ticks: { display: false }, title: { display: true, text: 'PCA Component 2', color: '#9CA3AF', font: { size: 10 } } }
                        }
                    }
                });
                this.setRunStatus('success', 'Success: PCA');
            }
        } catch(e) {
            this.setRunStatus('error', 'Failed: PCA');
            if (loadEl.parentNode) loadEl.remove();
        }
    },

    async runElbowCurve() {
        const container = document.getElementById('clustering-results');
        this.setRunStatus('running', 'Running: Elbow');
        container.innerHTML = '<div class="placeholder-box">Computing Elbow Curve...</div>';
        try {
            const r = await fetch('http://localhost:5000/api/cdm/elbow');
            const result = await r.json();
            if (result.status==='success') {
                container.innerHTML = `
                    <div style="width:100%;height:280px;margin-bottom:16px;"><canvas id="elbowChart"></canvas></div>
                    <p style="text-align:center;font-size:13px;">Recommended K: <strong>${result.data.recommended_k}</strong></p>`;
                new Chart(document.getElementById('elbowChart').getContext('2d'), {
                    type:'line',
                    data:{labels:result.data.k_values,datasets:[{
                        label:'Inertia',data:result.data.inertia,
                        borderColor:'#6366F1',backgroundColor:'rgba(99,102,241,0.07)',
                        fill:true,tension:0.3,borderWidth:2,pointRadius:5,pointBackgroundColor:'#6366F1'
                    }]},
                    options:{responsive:true,maintainAspectRatio:false,
                        plugins:{legend:{display:false}},
                        scales:{x:{grid:{display:false},ticks:{color:'#9CA3AF'}},
                                y:{grid:{color:'rgba(0,0,0,0.04)'},ticks:{color:'#9CA3AF'}}}}
                });
                this.setRunStatus('success', 'Success: Elbow');
            } else {
                this.setRunStatus('error', 'Failed: Elbow');
                container.innerHTML = `<div class="placeholder-box">${result.message || 'Elbow computation failed.'}</div>`;
            }
        } catch(e) {
            this.setRunStatus('error', 'Failed: Elbow');
            container.innerHTML = `<div class="placeholder-box">Error: ${e.message}</div>`;
        }
    },

    // Temporal
    async runTemporal() {
        const container = document.getElementById('temporal-results');
        this.setRunStatus('running', 'Running: Temporal');
        container.innerHTML = '<div class="placeholder-box">Analyzing time-series trends...</div>';
        try {
            const r = await fetch('http://localhost:5000/api/cdm/temporal', {method:'POST'});
            const result = await r.json();
            if (result.status==='success') {
                const d = result.data;
                const labels = Object.keys(d.quarterly_volumes).sort();
                const colorMap = {World:'#6366F1',Sports:'#EC4899',Business:'#10B981',Technology:'#F59E0B'};
                const datasets = Object.keys(colorMap).map(cat=>({
                    label:cat,data:labels.map(l=>d.quarterly_volumes[l][cat]||0),
                    borderColor:colorMap[cat],backgroundColor:colorMap[cat]+'18',
                    fill:true,tension:0.35,borderWidth:2,pointRadius:3
                }));
                const trendHtml = Object.entries(d.category_trends||{}).map(([k,v])=>{
                    const cls=v.direction==='rising'?'rising':v.direction==='declining'?'declining':'stable';
                    const icon=v.direction==='rising'?'↗':v.direction==='declining'?'↘':'→';
                    return `<div style="padding:12px;border:1px solid var(--border);border-radius:var(--r-md);background:var(--bg-card);">
                        <strong style="font-size:13px;">${k}</strong><br>
                        <span class="trend-chip trend-${cls}">${icon} ${v.direction}</span>
                        <div style="font-size:11px;color:var(--text-3);margin-top:4px;">slope: ${v.slope.toFixed(2)}</div>
                    </div>`;
                }).join('');
                const corrHtml = Object.entries(d.cross_category_correlation||{}).map(([k,v])=>
                    `<span class="rule-stat-chip">${k}: <strong>${v.toFixed(2)}</strong></span>`).join('');
                const standard = this.renderStandardSections({
                    method: d.analysis_type,
                    params: 'default temporal analysis',
                    metrics: { categories: Object.keys(d.category_trends || {}).length, correlations: Object.keys(d.cross_category_correlation || {}).length },
                    interpretation: d.interpretation
                });
                container.innerHTML = `${standard}
                    <div style="width:100%;height:240px;margin-bottom:20px;"><canvas id="temporalChart"></canvas></div>
                    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;margin-bottom:20px;">${trendHtml}</div>
                    <div>
                        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3);margin-bottom:10px;">Cross-Category Correlations</div>
                        <div style="display:flex;flex-wrap:wrap;gap:8px;">${corrHtml}</div>
                    </div>`;
                new Chart(document.getElementById('temporalChart').getContext('2d'),{
                    type:'line',data:{labels,datasets},
                    options:{responsive:true,maintainAspectRatio:false,
                        plugins:{legend:{labels:{font:{family:'Inter',size:11},usePointStyle:true}}},
                        scales:{x:{grid:{display:false},ticks:{color:'#9CA3AF',font:{size:10}}},
                                y:{grid:{color:'rgba(0,0,0,0.04)'},ticks:{color:'#9CA3AF',font:{size:10}}}}}
                });
                this.setRunStatus('success', 'Success: Temporal');
            } else {
                this.setRunStatus('error', 'Failed: Temporal');
                container.innerHTML = `<div class="placeholder-box">${result.message || 'Temporal analysis failed.'}</div>`;
            }
        } catch(e) {
            this.setRunStatus('error', 'Failed: Temporal');
            container.innerHTML = `<div class="placeholder-box">Error: ${e.message}</div>`;
        }
    },

    // Keywords
    async runKeywords() {
        const container = document.getElementById('keywords-results');
        this.setRunStatus('running', 'Running: Keywords');
        container.innerHTML = '<div class="placeholder-box">Extracting vocabulary prominence...</div>';
        try {
            const r = await fetch('http://localhost:5000/api/cdm/keywords', {
                method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({top_n:20})
            });
            const result = await r.json();
            if (result.status==='success') {
                const d = result.data;
                const top20 = d.global_top_terms;
                const catsHtml = Object.entries(d.category_defining_terms).map(([cat,terms])=>`
                    <div style="flex:1;border:1px solid var(--border);border-radius:var(--r-lg);padding:14px;background:var(--bg-card);">
                        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3);margin-bottom:10px;">${cat}</div>
                        <div class="keyword-cloud">
                            ${terms.slice(0,10).map((t,i)=>`<span class="keyword-tag ${i<3?'prominent':''}">${t.term}</span>`).join('')}
                        </div>
                    </div>`).join('');
                const crossHtml = (d.cross_category_terms||[]).map(t=>`<span class="keyword-tag">${t}</span>`).join('');
                const standard = this.renderStandardSections({
                    method: 'TF-IDF Keyword Prominence',
                    params: 'top_n=20',
                    metrics: { global_terms: (d.global_top_terms || []).length, cross_category_terms: (d.cross_category_terms || []).length },
                    interpretation: d.interpretation
                });
                container.innerHTML = `${standard}
                    <div style="display:flex;gap:20px;margin-bottom:24px;">
                        <div style="flex:2;height:240px;"><canvas id="keywordsChart"></canvas></div>
                        <div style="flex:1;padding:16px;background:var(--bg-subtle);border-radius:var(--r-lg);border:1px solid var(--border);">
                            <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3);margin-bottom:8px;">Cross-Category</div>
                            <div class="keyword-cloud">${crossHtml}</div>
                        </div>
                    </div>
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3);margin-bottom:12px;">Category Defining Terms</div>
                    <div style="display:flex;gap:12px;flex-wrap:wrap;">${catsHtml}</div>`;
                new Chart(document.getElementById('keywordsChart').getContext('2d'),{
                    type:'bar',
                    data:{labels:top20.map(t=>t.term),datasets:[{
                        label:'TF-IDF',data:top20.map(t=>t.score),
                        backgroundColor:top20.map((_,i)=>`hsl(${240+i*4},80%,${55+i*1.5}%)`),
                        borderRadius:4
                    }]},
                    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
                        plugins:{legend:{display:false}},
                        scales:{x:{grid:{display:false},ticks:{color:'#9CA3AF',font:{size:10}}},
                                y:{grid:{display:false},ticks:{color:'#5C6370',font:{size:11,weight:'600'}}}}}
                });
                this.setRunStatus('success', 'Success: Keywords');
            } else {
                this.setRunStatus('error', 'Failed: Keywords');
                container.innerHTML = `<div class="placeholder-box">${result.message || 'Keyword analysis failed.'}</div>`;
            }
        } catch(e) {
            this.setRunStatus('error', 'Failed: Keywords');
            container.innerHTML = `<div class="placeholder-box">Error: ${e.message}</div>`;
        }
    }
};

window.MiningLab = MiningLab;
document.addEventListener('DOMContentLoaded', () => MiningLab.init());
