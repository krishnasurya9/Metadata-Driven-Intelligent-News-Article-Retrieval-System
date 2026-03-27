/**
 * Mining Lab - All Advanced Modules
 */

const MiningLab = {
    charts: {}, // Store Chart.js instances

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
                        <p class="panel-desc">Analyze article volume trends across categories over time using linear regression and correlation.</p>
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
                        <p class="panel-desc">TF-IDF vocabulary analysis. Identifies globally prominent and category-defining terms.</p>
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

        const clusterActions = document.querySelector('#mining-clustering .panel-actions');
        if (clusterActions && !document.getElementById('run-elbow')) {
            clusterActions.insertAdjacentHTML('afterbegin', '<button id="run-elbow" class="run-btn run-btn-secondary" style="margin-right:10px; background:#475569; color:white;">Find Optimal K</button>');
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
                const panel = document.getElementById(targetId);
                if (panel) panel.classList.add('active-panel');

                const breadcrumb = document.getElementById('mining-active-module-name');
                if (breadcrumb) {
                    breadcrumb.textContent = cur.querySelector('.mining-nav-label')?.textContent || '';
                }
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
        
        // Dynamically added ones
        document.getElementById('run-temporal')?.addEventListener('click', () => this.runTemporal());
        document.getElementById('run-keywords')?.addEventListener('click', () => this.runKeywords());

        this.initWarehouse();
    },

    // ── Warehouse ──
    initWarehouse() {
        // Dropzone parsing... simplified for clarity
        this.loadLocalDataInfo();
    },
    async loadLocalDataInfo() {
        const infoEl = document.getElementById('local-data-info');
        if (!infoEl) return;
        try {
            const res = await fetch('http://localhost:5000/api/data/info');
            const data = await res.json();
            infoEl.innerHTML = `Loaded Data Info: ${data.data.storage.total_articles} articles found.`;
        } catch {
            infoEl.innerHTML = 'Backend unreachable';
        }
    },
    async loadWarehouseStats() {
        const container = document.getElementById('warehouse-results');
        if(!container) return;
        container.innerHTML = 'Loading warehouse statistics...';
        try {
            const res = await fetch('http://localhost:5000/api/stats');
            const stats = await res.json();
            container.innerHTML = `<div class="warehouse-grid"><div class="warehouse-stat-card"><span class="warehouse-stat-value">${stats.data.total_articles || 0}</span><span class="warehouse-stat-label">Total Articles</span></div></div>`;
        } catch(e) { container.innerHTML = 'Error ' + e; }
    },
    async loadDataset() {
         // omitted boilerplate for brevity
         this.loadWarehouseStats();
    },

    // ── Preprocessing ──
    async runPreprocessingDemo() {
        const outputEl = document.getElementById('preprocessing-output');
        outputEl.innerHTML = '<div class="placeholder-box">Loading preprocessing stats from frozen corpus...</div>';
        try {
            const res = await fetch('http://localhost:5000/api/cdm/stats');
            const result = await res.json();
            if(result.status === 'success') {
                const d = result.data;
                outputEl.innerHTML = `
                    <div style="background:#f3f3f3;padding:15px;border-radius:8px;">
                        <h4>Frozen AG News Corpus</h4>
                        <p>Original Docs: ${d.total_docs.toLocaleString()} → Cleaned: ${d.docs_after_cleaning.toLocaleString()}</p>
                        <p>Avg Length: ${d.avg_text_length} words | Vocab Estimate: ${d.vocabulary_size.toLocaleString()}</p>
                    </div>
                `;
            } else { outputEl.innerHTML = 'Error'; }
        } catch(e) { outputEl.innerHTML = e.message; }
    },

    // ── Association ──
    async runAssociationRules() {
        const container = document.getElementById('association-results');
        const minSupport = document.getElementById('min-support')?.value || 0.01;
        const minConfidence = document.getElementById('min-confidence')?.value || 0.3;
        container.innerHTML = '<div class="placeholder-box">Running FP-Growth on Frozen Corpus... (~10s)</div>';
        try {
            const res = await fetch('http://localhost:5000/api/cdm/association', { 
                method: 'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({min_support: minSupport, min_confidence: minConfidence})
            });
            const result = await res.json();
            if(result.status === 'success') {
                const data = result.data;
                if(!data.rules || data.rules.length===0) { container.innerHTML = 'No rules found.'; return;}
                let html = `<table class="data-table"><thead><tr><th>Rule</th><th>Support</th><th>Confidence</th><th>Lift</th></tr></thead><tbody>`;
                data.rules.forEach(r => {
                    html += `<tr><td><strong>${r.antecedent}</strong> → ${r.consequent}</td><td>${r.support}</td><td>${r.confidence}</td><td>${r.lift}</td></tr>`;
                });
                html += "</tbody></table>";
                container.innerHTML = `<div><p>${data.interpretation}</p>${html}</div>`;
            } else { container.innerHTML = result.message; }
        } catch (e) { container.innerHTML = e.message; }
    },

    // ── Classification ──
    async runClassification() {
        const container = document.getElementById('classification-results');
        container.innerHTML = '<div class="placeholder-box">Benchmarking NB vs SVM on Frozen Corpus... (~30s)</div>';
        try {
            const res = await fetch('http://localhost:5000/api/cdm/classify', { method: 'POST' });
            const result = await res.json();
            if(result.status === 'success') {
                const d = result.data;
                const nb = d.naive_bayes;
                const svm = d.svm;
                
                const tableHtml = (name, report, acc, time) => {
                    return `
                    <div style="flex:1; padding:10px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;">
                        <h4 style="margin-bottom:10px;">${name} (Acc: ${(acc*100).toFixed(1)}%, Time: ${time}s)</h4>
                        <table class="data-table" style="font-size:12px;">
                            ${Object.keys(report).filter(k => k!=='accuracy').map(k => `<tr><td>${k}</td><td>${report[k]['f1-score']?.toFixed(2)||'-'}</td></tr>`).join('')}
                        </table>
                    </div>`;
                };

                const cmHtml = (name, cm, classes) => {
                     let rows = '';
                     for(let i=0; i<cm.length; i++){
                         rows += "<tr>";
                         for(let j=0; j<cm[i].length; j++) {
                             let bg = i===j ? 'rgba(34, 197, 94, 0.2)' : cm[i][j]>0 ? 'rgba(239, 68, 68, 0.1)' : 'transparent';
                             rows += `<td style="background:${bg};text-align:center;">${cm[i][j]}</td>`;
                         }
                         rows += "</tr>";
                     }
                     return `<div style="flex:1;"><h5>${name} Confusion Matrix</h5><table style="width:100%; border-collapse:collapse; font-size:11px;" border="1">${rows}</table></div>`;
                };

                container.innerHTML = `
                    <div style="margin-bottom:15px; padding:15px; background:#dcfce7; color:#166534; border-radius:8px;">
                        <strong>Winner: ${d.winner}</strong> (+${(d.accuracy_delta*100).toFixed(2)}%)<br>
                        ${d.recommendation}
                    </div>
                    <div style="display:flex; gap:20px; margin-bottom:20px;">
                        ${tableHtml('Naive Bayes', nb.classification_report, nb.accuracy, nb.training_time_seconds)}
                        ${tableHtml('Linear SVM', svm.classification_report, svm.accuracy, svm.training_time_seconds)}
                    </div>
                    <div style="display:flex; gap:20px;">
                        ${cmHtml('Naive Bayes', nb.confusion_matrix, nb.classes)}
                        ${cmHtml('SVM', svm.confusion_matrix, svm.classes)}
                    </div>
                `;
            } else { container.innerHTML = result.message; }
        } catch(e) { container.innerHTML = e.message; }
    },

    // ── Clustering ──
    async runClustering() {
        const container = document.getElementById('clustering-results');
        const nClusters = document.getElementById('num-clusters')?.value || 4;
        container.innerHTML = '<div class="placeholder-box">Running Bisecting K-Means + LSA...</div>';
        try {
            const res = await fetch('http://localhost:5000/api/cdm/cluster', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ n_clusters: nClusters })
            });
            const result = await res.json();
            if (result.status === 'success') {
                const d = result.data;
                let cards = d.clusters.map(c => `
                    <div class="cluster-card" style="${c.is_outlier_cluster ? 'border:2px solid #ef4444;' : ''}">
                        <h3>Cluster ${c.cluster_id + 1} ${c.is_outlier_cluster ? '⚠️ Outlier' : ''}</h3>
                        <p>Size: ${c.size} (${c.percentage}%) | Purity: ${(c.purity*100).toFixed(1)}%</p>
                        <p><strong>Dom. Category:</strong> ${c.dominant_category}</p>
                        <p style="font-size:11px; margin-top:5px;"><strong>Keywords:</strong> ${c.top_terms.join(', ')}</p>
                    </div>`).join('');
                container.innerHTML = `
                    <div class="stats-box" style="margin-bottom:15px;">
                        ${d.sampled ? `<span>Sampled: ${d.sample_size} docs</span>` : ''}
                        <span>Overall Purity: ${(d.overall_purity*100).toFixed(1)}%</span>
                        <span>Silhouette: ${d.silhouette_score.toFixed(3)}</span>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">${cards}</div>
                `;
            } else { container.innerHTML = result.message; }
        } catch(e) { container.innerHTML = e.message; }
    },

    async runElbowCurve() {
        const container = document.getElementById('clustering-results');
        container.innerHTML = '<div class="placeholder-box">Computing Elbow Curve...</div>';
        try {
            const res = await fetch('http://localhost:5000/api/cdm/elbow');
            const result = await res.json();
            if(result.status==='success') {
                 container.innerHTML = `
                    <div style="width: 100%; height: 300px; margin-bottom: 20px;">
                        <canvas id="elbowChart"></canvas>
                    </div>
                    <p style="text-align:center;"><strong>Recommended K: ${result.data.recommended_k}</strong></p>
                 `;
                 const ctx = document.getElementById('elbowChart').getContext('2d');
                 new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: result.data.k_values,
                        datasets: [{
                            label: 'Inertia (SSE)',
                            data: result.data.inertia,
                            borderColor: '#3b82f6',
                            background: 'transparent',
                            tension: 0.1,
                            pointRadius: 5
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                 });
            } else { container.innerHTML = result.message; }
        } catch(e) { container.innerHTML = e.message; }
    },

    // ── Temporal ──
    async runTemporal() {
        const container = document.getElementById('temporal-results');
        container.innerHTML = '<div class="placeholder-box">Analyzing time-series trends...</div>';
        try {
            const res = await fetch('http://localhost:5000/api/cdm/temporal', { method: 'POST' });
            const result = await res.json();
            if(result.status==='success') {
                 const d = result.data;
                 
                 // Prep data for chart
                 const labels = Object.keys(d.quarterly_volumes).sort();
                 const categories = ['World', 'Sports', 'Business', 'Technology'];
                 const colors = {World:'#3b82f6', Sports:'#ec4899', Business:'#22c55e', Technology:'#8b5cf6'};
                 const datasets = categories.map(cat => ({
                    label: cat,
                    data: labels.map(l => d.quarterly_volumes[l][cat] || 0),
                    borderColor: colors[cat],
                    fill: false,
                    tension: 0.2
                 }));

                 let corrHtml = Object.entries(d.cross_category_correlation || {})
                    .map(([k,v]) => `<span style="background:#f1f5f9; padding:4px 8px; border-radius:4px; font-size:12px;">${k}: <b>${v.toFixed(2)}</b></span>`).join(' ');

                 let trendHtml = Object.entries(d.category_trends || {})
                    .map(([k,v]) => {
                        let arrow = v.direction==='rising' ? '<span style="color:#22c55e;">↗ Rising</span>' : 
                                    v.direction==='declining' ? '<span style="color:#ef4444;">↘ Declining</span>' : '→ Stable';
                        return `<div style="padding:10px; border:1px solid #e2e8f0; border-radius:6px; background:#fff;"><b>${k}</b><br>${arrow} (slope: ${v.slope.toFixed(2)})</div>`;
                    }).join('');

                 container.innerHTML = `
                    <p style="margin-bottom:15px; font-size:14px; color:#475569;">${d.interpretation}</p>
                    <div style="width: 100%; height: 250px; margin-bottom: 20px;">
                        <canvas id="temporalChart"></canvas>
                    </div>
                    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:20px;">
                        ${trendHtml}
                    </div>
                    <div>
                        <h4 style="font-size:13px; margin-bottom:8px;">Cross-Category Correlations</h4>
                        <div style="display:flex; flex-wrap:wrap; gap:8px;">${corrHtml}</div>
                    </div>
                 `;
                 
                 const ctx = document.getElementById('temporalChart').getContext('2d');
                 new Chart(ctx, {
                     type: 'line', data: { labels, datasets },
                     options: { responsive: true, maintainAspectRatio: false }
                 });
            } else { container.innerHTML = result.message; }
        } catch(e) { container.innerHTML = e.message; }
    },

    // ── Keywords ──
    async runKeywords() {
        const container = document.getElementById('keywords-results');
        container.innerHTML = '<div class="placeholder-box">Extracting vocabulary prominence...</div>';
        try {
            const res = await fetch('http://localhost:5000/api/cdm/keywords', {
                method: 'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({top_n:20})
            });
            const result = await res.json();
            if(result.status==='success') {
                const d = result.data;
                const top20 = d.global_top_terms;
                
                let catsHtml = '';
                for(let [cat, terms] of Object.entries(d.category_defining_terms)) {
                    catsHtml += `
                    <div style="flex:1; border:1px solid #e2e8f0; border-radius:8px; padding:10px; background:#fff;">
                        <h4 style="margin-bottom:10px;">${cat}</h4>
                        <div style="display:flex; flex-wrap:wrap; gap:5px;">
                            ${terms.slice(0,10).map(t => `<span style="background:#f1f5f9; font-size:11px; padding:3px 6px; border-radius:4px;">${t.term}</span>`).join('')}
                        </div>
                    </div>`;
                }

                container.innerHTML = `
                    <div style="display:flex; gap:20px; margin-bottom:20px;">
                        <div style="flex:2; height:250px;">
                            <canvas id="keywordsChart"></canvas>
                        </div>
                        <div style="flex:1; padding:15px; background:#f8fafc; border-radius:8px;">
                            <h4>Cross-Category Terms</h4>
                            <p style="font-size:12px; color:#64748b; margin-bottom:10px;">Terms prominent in 3 or more categories:</p>
                            <div style="display:flex; flex-wrap:wrap; gap:5px;">
                                ${(d.cross_category_terms||[]).map(t => `<span style="background:#e2e8f0; font-size:11px; padding:3px 6px; border-radius:4px;">${t}</span>`).join('')}
                            </div>
                        </div>
                    </div>
                    <h4 style="margin-bottom:10px;">Category Defining Terms</h4>
                    <div style="display:flex; gap:10px;">${catsHtml}</div>
                `;

                 const ctx = document.getElementById('keywordsChart').getContext('2d');
                 new Chart(ctx, {
                     type: 'bar', 
                     data: { 
                         labels: top20.map(t=>t.term), 
                         datasets: [{
                             label: 'Global TF-IDF Score',
                             data: top20.map(t=>t.score),
                             backgroundColor: '#3b82f6'
                         }]
                     },
                     options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y' }
                 });

            } else { container.innerHTML = result.message; }
        } catch(e) { container.innerHTML = e.message; }
    }
};

window.MiningLab = MiningLab;
document.addEventListener('DOMContentLoaded', () => MiningLab.init());
