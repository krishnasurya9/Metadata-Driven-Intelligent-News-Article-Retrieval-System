/**
 * Analytics Mode — Real implementation with corpus stats + charts
 * Loads data from the backend API and renders Chart.js visualizations
 */

const Analytics = {
    charts: {},
    loaded: false,

    init() {
        document.getElementById('run-analytics-btn')?.addEventListener('click', () => {
            this.loadAll();
        });
    },

    async loadAll() {
        const btn = document.getElementById('run-analytics-btn');
        if (btn) { btn.textContent = '⏳ Loading...'; btn.disabled = true; }

        try {
            await Promise.all([
                this.loadStats(),
                this.loadCategoryChart(),
                this.loadSourceChart()
            ]);
            this.loaded = true;
        } catch (e) {
            console.error('Analytics load error:', e);
        } finally {
            if (btn) { btn.textContent = '🔄 Refresh'; btn.disabled = false; }
        }
    },

    async loadStats() {
        try {
            // Fetch corpus stats
            const [statsRes, healthRes, catRes, srcRes] = await Promise.all([
                fetch('http://localhost:5000/api/stats'),
                fetch('http://localhost:5000/api/health'),
                fetch('http://localhost:5000/api/categories'),
                fetch('http://localhost:5000/api/sources')
            ]);

            const stats  = await statsRes.json();
            const health = await healthRes.json();
            const cats   = await catRes.json();
            const srcs   = await srcRes.json();

            // Total articles
            const total = stats?.data?.total_articles ?? stats?.total_articles ?? '—';
            this._setVal('stat-total-articles', typeof total === 'number' ? total.toLocaleString() : total);

            // Categories count
            const catCount = Array.isArray(cats?.data) ? cats.data.length : '—';
            this._setVal('stat-categories', catCount);

            // Sources count
            const srcCount = Array.isArray(srcs?.data) ? srcs.data.length : '—';
            this._setVal('stat-sources', srcCount);

            // Indexed docs
            const indexed = health?.data?.index_status?.documents_indexed;
            this._setVal('stat-indexed', indexed ? indexed.toLocaleString() : '—');

        } catch (e) {
            console.warn('Stats load failed:', e);
        }
    },

    async loadCategoryChart() {
        try {
            const res = await fetch('http://localhost:5000/api/analytics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'category_distribution' })
            });
            const result = await res.json();
            const data = result?.data ?? {};

            // Destroy existing chart
            if (this.charts.category) { this.charts.category.destroy(); }

            const ctx = document.getElementById('category-chart');
            if (!ctx) return;

            const labels = Object.keys(data);
            const values = labels.map(k => data[k]?.count ?? data[k] ?? 0);
            const palette = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#3B82F6', '#8B5CF6', '#EC4899'];

            this.charts.category = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{
                        data: values,
                        backgroundColor: palette,
                        borderWidth: 2,
                        borderColor: '#FFFFFF',
                        hoverBorderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                font: { family: 'Inter', size: 12, weight: '600' },
                                color: '#5C6370',
                                padding: 14,
                                usePointStyle: true,
                                pointStyleWidth: 8
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toLocaleString()}`
                            }
                        }
                    },
                    cutout: '58%'
                }
            });
        } catch (e) {
            console.warn('Category chart failed:', e);
        }
    },

    async loadSourceChart() {
        try {
            const res = await fetch('http://localhost:5000/api/analytics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'source_bias' })
            });
            const result = await res.json();
            const sources = result?.data?.sources ?? result?.data ?? {};

            if (this.charts.source) { this.charts.source.destroy(); }

            const ctx = document.getElementById('source-chart');
            if (!ctx) return;

            // Sort and take top 10
            const sorted = Object.entries(sources)
                .sort((a, b) => (b[1]?.count ?? b[1] ?? 0) - (a[1]?.count ?? a[1] ?? 0))
                .slice(0, 10);

            const labels = sorted.map(([k]) => k);
            const values = sorted.map(([, v]) => v?.count ?? v ?? 0);

            this.charts.source = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        label: 'Articles',
                        data: values,
                        backgroundColor: 'rgba(99, 102, 241, 0.75)',
                        borderColor: '#6366F1',
                        borderWidth: 1.5,
                        borderRadius: 6,
                        borderSkipped: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => ` ${ctx.parsed.x.toLocaleString()} articles`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: '#F0EFE9' },
                            ticks: { font: { family: 'Inter', size: 11 }, color: '#9CA3AF' }
                        },
                        y: {
                            grid: { display: false },
                            ticks: { font: { family: 'Inter', size: 11, weight: '600' }, color: '#5C6370' }
                        }
                    }
                }
            });
        } catch (e) {
            console.warn('Source chart failed:', e);
        }
    },

    _setVal(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    }
};

// Auto-load when switching to analytics view
document.addEventListener('DOMContentLoaded', () => {
    Analytics.init();
});

// Expose for app.js switchMode to trigger auto-load
window.AnalyticsMode = Analytics;
