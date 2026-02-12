/**
 * Mining Lab Logic
 * Handles Association Rules, Clustering, and Classification UI
 */

const MiningLab = {
    init: function () {
        console.log("Initializing Mining Lab...");
        this.bindEvents();
    },

    bindEvents: function () {
        // Tab switching within Mining Lab
        document.querySelectorAll('.mining-tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Deactivate all
                document.querySelectorAll('.mining-tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.mining-tab-content').forEach(c => c.classList.add('hidden'));

                // Activate clicked
                e.target.classList.add('active');
                const targetId = e.target.dataset.target;
                document.getElementById(targetId).classList.remove('hidden');
            });
        });

        // Run buttons
        document.getElementById('run-association')?.addEventListener('click', this.runAssociationRules.bind(this));
        document.getElementById('run-clustering')?.addEventListener('click', this.runClustering.bind(this));
        document.getElementById('run-classification')?.addEventListener('click', this.runClassification.bind(this));
    },

    async runAssociationRules() {
        const container = document.getElementById('association-results');
        container.innerHTML = '<div class="loader"></div> Generating rules...';

        try {
            const response = await fetch('http://localhost:5000/api/mining/association');
            const result = await response.json();

            if (result.status === 'success') {
                this.renderAssociationRules(result.data, container);
            } else {
                container.innerHTML = `<div class="error">Error: ${result.message}</div>`;
            }
        } catch (e) {
            container.innerHTML = `<div class="error">Network Error: ${e.message}</div>`;
        }
    },

    renderAssociationRules(data, container) {
        if (!data.rules || data.rules.length === 0) {
            container.innerHTML = '<p>No significant rules found. Try adding more data or adjusting thresholds.</p>';
            return;
        }

        let html = `
            <div class="stats-box">
                <p><strong>Transactions Analyzed:</strong> ${data.transaction_count}</p>
                <p><strong>Rules Found:</strong> ${data.rules.length}</p>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Rule (Antecedent → Consequent)</th>
                        <th>Support</th>
                        <th>Confidence</th>
                        <th>Lift</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.rules.forEach(rule => {
            html += `
                <tr>
                    <td>${rule.antecedent} ➡️ ${rule.consequent}</td>
                    <td>${rule.support}</td>
                    <td><strong>${rule.confidence}</strong></td>
                    <td>${rule.lift}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    },

    async runClustering() {
        const container = document.getElementById('clustering-results');
        const nClusters = document.getElementById('num-clusters').value;
        container.innerHTML = '<div class="loader"></div> Clustering documents...';

        try {
            const response = await fetch('http://localhost:5000/api/mining/clustering', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ n_clusters: nClusters })
            });
            const result = await response.json();

            if (result.status === 'success') {
                this.renderClustering(result.data, container);
            } else {
                container.innerHTML = `<div class="error">Error: ${result.message}</div>`;
            }
        } catch (e) {
            container.innerHTML = `<div class="error">Network Error: ${e.message}</div>`;
        }
    },

    renderClustering(data, container) {
        let html = '<div class="clusters-grid">';

        data.clusters.forEach(cluster => {
            html += `
                <div class="cluster-card">
                    <h3>Cluster ${cluster.cluster_id + 1}</h3>
                    <div class="cluster-size">${cluster.size} documents</div>
                    <div class="cluster-terms">
                        <strong>Keywords:</strong> ${cluster.top_terms.join(', ')}
                    </div>
                    <div class="cluster-samples">
                        <strong>Samples:</strong>
                        <ul>
                            ${cluster.samples.map(s => `<li>${s}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    },

    async runClassification() {
        const container = document.getElementById('classification-results');
        container.innerHTML = '<div class="loader"></div> Training classifier...';

        try {
            const response = await fetch('http://localhost:5000/api/mining/classification', {
                method: 'POST'
            });
            const result = await response.json();

            if (result.status === 'success') {
                this.renderClassification(result.data, container);
            } else {
                container.innerHTML = `<div class="error">Error: ${result.message}</div>`;
            }
        } catch (e) {
            container.innerHTML = `<div class="error">Network Error: ${e.message}</div>`;
        }
    },

    renderClassification(data, container) {
        const report = data.detailed_report;
        const accuracy = Math.round(data.accuracy * 100);

        let html = `
            <div class="model-score">
                <div class="score-circle">
                    <span>${accuracy}%</span>
                    <small>Accuracy</small>
                </div>
                <div class="score-info">
                    <h4>Random Forest Classifier</h4>
                    <p>Trained on ${Object.keys(report).length - 3} categories</p>
                </div>
            </div>
            
            <h3>Class-wise Performance</h3>
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
                <tbody>
        `;

        for (const [key, value] of Object.entries(report)) {
            if (['accuracy', 'macro avg', 'weighted avg'].includes(key)) continue;

            html += `
                <tr>
                    <td>${key}</td>
                    <td>${value['precision'].toFixed(2)}</td>
                    <td>${value['recall'].toFixed(2)}</td>
                    <td>${value['f1-score'].toFixed(2)}</td>
                    <td>${value['support']}</td>
                </tr>
            `;
        }

        html += '</tbody></table>';
        container.innerHTML = html;
    }
};

// Expose to window
window.MiningLab = MiningLab;
