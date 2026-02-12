"""
Analytics Engine Module - Data Mining and Pattern Analysis
Handles corpus-level and result-level analytics
"""

from typing import List, Dict, Any, Optional
from collections import Counter
import statistics

from preprocessor import clean_text, tokenize, remove_stopwords


def analyze_category_distribution(documents: List[Dict], 
                                  doc_ids: List[int] = None) -> Dict[str, Any]:
    """
    Analyze category distribution across documents
    
    Args:
        documents: All documents
        doc_ids: Optional subset of doc IDs to analyze
    """
    if doc_ids:
        docs = [d for d in documents if d['doc_id'] in doc_ids]
    else:
        docs = documents
    
    category_counts = Counter(d.get('category', 'unknown') for d in docs)
    total = len(docs)
    
    distribution = {
        cat: {
            "count": count,
            "percentage": round(count / total * 100, 2) if total > 0 else 0
        }
        for cat, count in category_counts.most_common()
    }
    
    explanation = _generate_category_explanation(distribution)
    
    return {
        "analysis_type": "category_distribution",
        "total_documents": total,
        "data": distribution,
        "visualization_type": "bar_chart",
        "explanation": explanation
    }


def analyze_term_frequency(documents: List[Dict], 
                          doc_ids: List[int] = None,
                          top_n: int = 30) -> Dict[str, Any]:
    """
    Analyze most frequent terms in documents
    """
    if doc_ids:
        docs = [d for d in documents if d['doc_id'] in doc_ids]
    else:
        docs = documents
    
    all_terms = []
    for doc in docs:
        text = f"{doc.get('title', '')} {doc.get('content', '')}"
        cleaned = clean_text(text)
        tokens = tokenize(cleaned)
        tokens = remove_stopwords(tokens)
        all_terms.extend(tokens)
    
    term_counts = Counter(all_terms)
    top_terms = dict(term_counts.most_common(top_n))
    
    explanation = _generate_term_explanation(top_terms, len(docs))
    
    return {
        "analysis_type": "term_frequency",
        "total_documents": len(docs),
        "total_terms": len(all_terms),
        "unique_terms": len(term_counts),
        "data": top_terms,
        "visualization_type": "word_cloud",
        "explanation": explanation
    }


def analyze_source_bias(documents: List[Dict],
                        doc_ids: List[int] = None) -> Dict[str, Any]:
    """
    Analyze distribution of articles by source
    """
    if doc_ids:
        docs = [d for d in documents if d['doc_id'] in doc_ids]
    else:
        docs = documents
    
    source_counts = Counter(d.get('source', 'unknown') for d in docs)
    total = len(docs)
    
    # Calculate dominance metrics
    top_source, top_count = source_counts.most_common(1)[0] if source_counts else ('unknown', 0)
    dominance_ratio = top_count / total if total > 0 else 0
    
    distribution = {
        src: {
            "count": count,
            "percentage": round(count / total * 100, 2) if total > 0 else 0
        }
        for src, count in source_counts.most_common(15)
    }
    
    explanation = _generate_source_explanation(distribution, dominance_ratio, top_source)
    
    return {
        "analysis_type": "source_bias",
        "total_documents": total,
        "unique_sources": len(source_counts),
        "dominant_source": top_source,
        "dominance_ratio": round(dominance_ratio, 4),
        "data": distribution,
        "visualization_type": "pie_chart",
        "explanation": explanation
    }


def analyze_time_trends(documents: List[Dict],
                        doc_ids: List[int] = None) -> Dict[str, Any]:
    """
    Analyze temporal trends in document publication
    """
    if doc_ids:
        docs = [d for d in documents if d['doc_id'] in doc_ids]
    else:
        docs = documents
    
    # Group by month/year
    time_counts = Counter()
    for doc in docs:
        date = doc.get('published_at')
        if date:
            # Extract year-month
            date_str = str(date)[:7] if len(str(date)) >= 7 else str(date)[:4]
            time_counts[date_str] += 1
    
    # Sort chronologically
    sorted_dates = sorted(time_counts.items())
    
    explanation = _generate_time_explanation(sorted_dates)
    
    return {
        "analysis_type": "time_trends",
        "total_documents": len(docs),
        "date_range": {
            "earliest": sorted_dates[0][0] if sorted_dates else None,
            "latest": sorted_dates[-1][0] if sorted_dates else None
        },
        "data": dict(sorted_dates),
        "visualization_type": "line_chart",
        "explanation": explanation
    }


def compare_top_bottom(top_results: List[Dict], 
                       bottom_results: List[Dict],
                       documents: List[Dict]) -> Dict[str, Any]:
    """
    Compare characteristics of top-ranked vs bottom-ranked results
    """
    doc_lookup = {d['doc_id']: d for d in documents}
    
    def analyze_group(results: List[Dict]) -> Dict[str, Any]:
        doc_ids = [r['doc_id'] for r in results]
        docs = [doc_lookup[id] for id in doc_ids if id in doc_lookup]
        
        if not docs:
            return {}
        
        # Category analysis
        categories = Counter(d.get('category') for d in docs)
        dominant_cat = categories.most_common(1)[0][0] if categories else None
        
        # Word count analysis
        word_counts = [d.get('word_count', 0) for d in docs]
        avg_word_count = statistics.mean(word_counts) if word_counts else 0
        
        # Term analysis
        all_terms = []
        for doc in docs:
            text = f"{doc.get('title', '')} {doc.get('content', '')}"
            cleaned = clean_text(text)
            tokens = tokenize(cleaned)
            tokens = remove_stopwords(tokens)
            all_terms.extend(tokens)
        
        common_terms = [t for t, c in Counter(all_terms).most_common(10)]
        
        # Score analysis
        scores = [r['score'] for r in results]
        avg_score = statistics.mean(scores) if scores else 0
        
        return {
            "dominant_category": dominant_cat,
            "category_distribution": dict(categories.most_common(5)),
            "avg_word_count": round(avg_word_count, 0),
            "avg_score": round(avg_score, 4),
            "common_terms": common_terms,
            "doc_count": len(docs)
        }
    
    top_analysis = analyze_group(top_results)
    bottom_analysis = analyze_group(bottom_results)
    
    explanation = _generate_comparison_explanation(top_analysis, bottom_analysis)
    
    return {
        "analysis_type": "top_bottom_comparison",
        "top_20_analysis": top_analysis,
        "bottom_20_analysis": bottom_analysis,
        "visualization_type": "comparison_chart",
        "explanation": explanation
    }


def get_corpus_overview(documents: List[Dict]) -> Dict[str, Any]:
    """
    Get a comprehensive overview of the corpus
    """
    total = len(documents)
    
    # Category stats
    categories = Counter(d.get('category') for d in documents)
    
    # Source stats
    sources = Counter(d.get('source') for d in documents)
    
    # Word count stats
    word_counts = [d.get('word_count', 0) for d in documents if d.get('word_count')]
    
    return {
        "total_documents": total,
        "categories": {
            "count": len(categories),
            "distribution": dict(categories.most_common(10))
        },
        "sources": {
            "count": len(sources),
            "top_sources": dict(sources.most_common(10))
        },
        "word_counts": {
            "min": min(word_counts) if word_counts else 0,
            "max": max(word_counts) if word_counts else 0,
            "avg": round(statistics.mean(word_counts), 0) if word_counts else 0,
            "median": round(statistics.median(word_counts), 0) if word_counts else 0
        }
    }


# Explanation generators

def _generate_category_explanation(distribution: Dict) -> str:
    if not distribution:
        return "No category data available."
    
    top_cats = list(distribution.keys())[:3]
    explanation = f"This pattern exists because:\n"
    explanation += f"• The corpus is dominated by {', '.join(top_cats)} categories\n"
    explanation += f"• These categories represent the most frequently published topics in the dataset\n"
    explanation += f"• Category imbalance may affect retrieval performance for underrepresented topics"
    return explanation


def _generate_term_explanation(top_terms: Dict, doc_count: int) -> str:
    if not top_terms:
        return "No term data available."
    
    top_words = list(top_terms.keys())[:5]
    explanation = f"This pattern exists because:\n"
    explanation += f"• High-frequency terms like '{', '.join(top_words)}' appear across many documents\n"
    explanation += f"• These terms define the core vocabulary of the corpus\n"
    explanation += f"• Domain-specific terms indicate the topical focus of the collection"
    return explanation


def _generate_source_explanation(distribution: Dict, dominance_ratio: float, top_source: str) -> str:
    explanation = f"This pattern exists because:\n"
    if dominance_ratio > 0.5:
        explanation += f"• The corpus shows source bias - {top_source} dominates with {dominance_ratio*100:.1f}% of articles\n"
        explanation += f"• This may affect diversity of perspectives in search results\n"
    else:
        explanation += f"• Sources are relatively balanced across the corpus\n"
        explanation += f"• Top source {top_source} contributes {dominance_ratio*100:.1f}% of articles\n"
    explanation += f"• Source diversity: {len(distribution)} unique sources in the dataset"
    return explanation


def _generate_time_explanation(sorted_dates: List) -> str:
    if not sorted_dates:
        return "No temporal data available."
    
    explanation = f"This pattern exists because:\n"
    explanation += f"• Publication dates range from {sorted_dates[0][0]} to {sorted_dates[-1][0]}\n"
    
    # Find peak periods
    if len(sorted_dates) > 2:
        peak = max(sorted_dates, key=lambda x: x[1])
        explanation += f"• Peak publication period: {peak[0]} with {peak[1]} articles\n"
    
    explanation += f"• Temporal distribution may reflect news cycles and event-driven coverage"
    return explanation


def _generate_comparison_explanation(top: Dict, bottom: Dict) -> str:
    explanation = f"This pattern exists because:\n"
    
    if top.get('dominant_category') != bottom.get('dominant_category'):
        explanation += f"• High-ranked docs favor '{top.get('dominant_category')}' category, low-ranked favor '{bottom.get('dominant_category')}'\n"
    
    if top.get('avg_word_count', 0) > bottom.get('avg_word_count', 0):
        explanation += f"• High-ranked docs are longer (avg {top.get('avg_word_count', 0):.0f} words vs {bottom.get('avg_word_count', 0):.0f})\n"
    
    explanation += f"• High-ranked docs have domain-specific vocabulary matching the query\n"
    explanation += f"• Low-ranked docs use more generic terms with less query relevance"
    
    return explanation
