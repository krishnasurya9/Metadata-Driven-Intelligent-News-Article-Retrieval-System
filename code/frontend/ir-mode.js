/**
 * IR Mode - Search functionality
 * This file is kept for compatibility but main logic is now in app.js
 */

// Additional search-related utilities can be added here

// Highlight query terms in text
function highlightQueryTerms(text, query) {
    if (!text || !query) return text;

    const terms = query.toLowerCase().split(/\s+/).filter(t => t.length > 2);
    let result = text;

    terms.forEach(term => {
        const regex = new RegExp(`\\b(${term})\\b`, 'gi');
        result = result.replace(regex, '<mark>$1</mark>');
    });

    return result;
}

// Format date for display
function formatDate(dateStr) {
    if (!dateStr || dateStr === 'None' || dateStr === 'null') return '';

    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        return dateStr;
    }
}

// Truncate text to specified length
function truncateText(text, maxLength = 200) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
}

console.log('IR Mode loaded');
