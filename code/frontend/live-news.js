/**
 * Live News Module
 * Fetches and displays real-time news from the backend API
 */

document.addEventListener('DOMContentLoaded', () => {
    fetchLiveNews();
});

async function fetchLiveNews() {
    const grid = document.getElementById('live-news-grid');
    if (!grid) return;

    try {
        const response = await fetch('http://localhost:5000/api/live-news');
        const data = await response.json();

        if (data.status === 'success') {
            if (data.articles.length > 0) {
                renderNewsGrid(data.articles);
            }

            // Show notification if new articles were archived
            if (data.archived_count > 0) {
                const toast = document.createElement('div');
                toast.className = 'toast-notification';
                toast.innerHTML = `
                    <span class="icon">📥</span>
                    <div class="message">
                        <strong>Auto-Archived</strong>
                        <div>Saved ${data.archived_count} new articles to database</div>
                    </div>
                `;
                document.body.appendChild(toast);

                // Add styles dynamically if not present
                if (!document.getElementById('toast-style')) {
                    const style = document.createElement('style');
                    style.id = 'toast-style';
                    style.textContent = `
                        .toast-notification {
                            position: fixed;
                            bottom: 20px;
                            right: 20px;
                            background: white;
                            border-left: 4px solid #10b981;
                            padding: 16px;
                            border-radius: 8px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                            display: flex;
                            align-items: center;
                            gap: 12px;
                            z-index: 1000;
                            animation: slideIn 0.3s ease-out;
                        }
                        .toast-notification .icon { font-size: 20px; }
                        @keyframes slideIn {
                            from { transform: translateX(100%); opacity: 0; }
                            to { transform: translateX(0); opacity: 1; }
                        }
                    `;
                    document.head.appendChild(style);
                }

                // Remove after 5 seconds
                setTimeout(() => {
                    toast.style.opacity = '0';
                    toast.style.transform = 'translateY(10px)';
                    toast.style.transition = 'all 0.3s';
                    setTimeout(() => toast.remove(), 300);
                }, 5000);

                // Trigger status refresh to update doc count
                if (typeof checkSystemStatus === 'function') {
                    checkSystemStatus();
                }
            }
        } else {
            // Handle error or empty state
            grid.innerHTML = `
                <div class="error-state" style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">
                    <p>${data.message || 'Unable to load live news at the moment.'}</p>
                    ${data.status === 'error' && data.message.includes('API key') ?
                    '<p style="font-size: 12px; margin-top: 8px;">Please add API keys to .env file in backend.</p>' : ''}
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching live news:', error);
        grid.innerHTML = `
            <div class="error-state" style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">
                <p>Failed to connect to news service.</p>
            </div>
        `;
    }
}

function renderNewsGrid(articles) {
    const grid = document.getElementById('live-news-grid');
    grid.innerHTML = ''; // Clear loading spinner

    articles.forEach(article => {
        // Validate image
        const hasImage = article.image && !article.image.includes('null');
        const imageUrl = hasImage ? article.image : 'data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%22280%22%20height%3D%22160%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%20fill%3D%22%23eee%22%20width%3D%22280%22%20height%3D%22160%22%2F%3E%3Ctext%20x%3D%2250%25%22%20y%3D%2250%25%22%20dominant-baseline%3D%22middle%22%20text-anchor%3D%22middle%22%20fill%3D%22%23aaa%22%20font-family%3D%22sans-serif%22%20font-size%3D%2214%22%3ENo%20Image%3C%2Ftext%3E%3C%2Fsvg%3E';

        const card = document.createElement('div');
        card.className = 'news-card';
        card.onclick = () => window.open(article.url, '_blank');

        const date = new Date(article.published_at).toLocaleDateString(undefined, {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });

        card.innerHTML = `
            <div class="news-image" style="background-image: url('${imageUrl}')"></div>
            <div class="news-content">
                <div class="news-source">${article.source || 'Unknown Source'}</div>
                <h3 class="news-title">${article.title}</h3>
                <div class="news-time">${date}</div>
            </div>
        `;

        grid.appendChild(card);
    });
}
