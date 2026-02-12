"""
LLM Service Module - Integration with LM Studio (OpenAI-compatible API)
Handles summary and explanation generation using RAG approach

Supports:
- LM Studio (default, OpenAI-compatible API)
- Ollama (fallback)
- Rule-based explanations (when no LLM available)
"""

import requests
from typing import List, Dict, Any, Optional

# LM Studio Configuration (OpenAI-compatible API)
# Default LM Studio endpoint - runs on localhost:961
LM_STUDIO_URL = "http://localhost:961/v1/chat/completions"

# Ollama Configuration (alternative)
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama2"

# Active provider (auto-detected)
_active_provider = None


def detect_provider() -> str:
    """Auto-detect which LLM provider is available"""
    global _active_provider
    
    # Try LM Studio first (most common for local use)
    try:
        response = requests.get("http://localhost:961/v1/models", timeout=2)
        if response.status_code == 200:
            _active_provider = "lm_studio"
            return "lm_studio"
    except:
        pass
    
    # Try Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            _active_provider = "ollama"
            return "ollama"
    except:
        pass
    
    _active_provider = "fallback"
    return "fallback"


def is_available() -> bool:
    """Check if any LLM is running and available"""
    provider = detect_provider()
    return provider != "fallback"


def _call_lm_studio(prompt: str, system_prompt: str = None) -> Optional[str]:
    """Call LM Studio's OpenAI-compatible API"""
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = requests.post(LM_STUDIO_URL, json={
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 500,
            "stream": False
        }, timeout=60)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"LM Studio error: {e}")
    
    return None


def _call_ollama(prompt: str) -> Optional[str]:
    """Call Ollama API"""
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }, timeout=60)
        
        if response.status_code == 200:
            return response.json().get('response')
    except Exception as e:
        print(f"Ollama error: {e}")
    
    return None


def generate_text(prompt: str, system_prompt: str = None) -> str:
    """Generate text using available LLM provider"""
    provider = detect_provider()
    
    if provider == "lm_studio":
        result = _call_lm_studio(prompt, system_prompt)
        if result:
            return result
    
    elif provider == "ollama":
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        result = _call_ollama(full_prompt)
        if result:
            return result
    
    return None


def generate_search_summary(query: str, top_results: List[Dict], 
                           bottom_results: List[Dict]) -> str:
    """
    Generate a summary of search results using local LLM
    
    This follows RAG principle: LLM only summarizes, never searches
    """
    # Prepare context from results
    top_context = "\n".join([
        f"- {r.get('title', 'Untitled')}: {r.get('content_excerpt', '')[:150]}"
        for r in top_results[:5]
    ])
    
    bottom_context = "\n".join([
        f"- {r.get('title', 'Untitled')}: {r.get('content_excerpt', '')[:150]}"
        for r in bottom_results[:3]
    ])
    
    system_prompt = "You are a helpful news assistant. summarizing the content of news articles. Focus on the facts and events described."
    
    prompt = f"""Based on the following search results for the query "{query}", provide a clear and concise summary of the news.
    
    What is the main matter or topic discussed in these articles?
    
    Articles:
    {top_context}
    
    Summary of content:"""
    
    result = generate_text(prompt, system_prompt)
    return result if result else _fallback_search_summary(query, top_results, bottom_results)


def generate_general_answer(query: str) -> str:
    """
    Generate a general knowledge answer when no news results are found.
    """
    system_prompt = "You are a helpful AI assistant. The user asked a question, but our news database has no relevant articles. Provide a helpful general answer to their query based on your training data. Start by saying 'We don't have any specific news articles on this topic, but...'"
    
    prompt = f"User Query: {query}\n\nProvide a helpful answer."
    
    result = generate_text(prompt, system_prompt)
    return result if result else f"We don't have any news on '{query}', and the AI assistant is currently unavailable."


def generate_analytics_explanation(analysis_type: str, 
                                   analysis_data: Dict) -> str:
    """
    Generate explanation for analytics patterns using local LLM
    """
    system_prompt = "You are a data analyst explaining patterns in news data. Be concise (2-3 sentences)."
    
    # Prepare prompt based on analysis type
    if analysis_type == "category_distribution":
        data_summary = ", ".join([f"{k}: {v.get('count', v)}" for k, v in list(analysis_data.get('data', {}).items())[:5]])
        prompt = f"""Explain this category distribution in a news corpus:
{data_summary}

Why might this distribution exist? What does it tell us about the dataset?"""

    elif analysis_type == "top_bottom_comparison":
        top = analysis_data.get('top_20_analysis', {})
        bottom = analysis_data.get('bottom_20_analysis', {})
        prompt = f"""Compare these search result groups:
Top results: Category={top.get('dominant_category')}, Avg words={top.get('avg_word_count')}, Terms={top.get('common_terms', [])[:5]}
Bottom results: Category={bottom.get('dominant_category')}, Avg words={bottom.get('avg_word_count')}, Terms={bottom.get('common_terms', [])[:5]}

Why do top results rank higher? What differentiates them?"""

    else:
        return _fallback_analytics_explanation(analysis_type, analysis_data)
    
    result = generate_text(prompt, system_prompt)
    return result if result else _fallback_analytics_explanation(analysis_type, analysis_data)


def generate_result_explanation(doc: Dict, query: str, 
                                matched_terms: List[str]) -> str:
    """
    Generate explanation for why a specific document ranked high/low
    """
    system_prompt = "You are explaining document relevance. Be very brief (1-2 sentences)."
    
    prompt = f"""Explain why this document matches the query "{query}":
Title: {doc.get('title', 'Untitled')}
Matched terms: {', '.join(matched_terms)}
Category: {doc.get('metadata', {}).get('category', 'unknown')}
Score: {doc.get('score', 0)}"""

    result = generate_text(prompt, system_prompt)
    return result if result else _fallback_result_explanation(doc, query, matched_terms)


# Fallback functions when LLM is not available

def _fallback_search_summary(query: str, top_results: List[Dict], 
                            bottom_results: List[Dict]) -> str:
    """Rule-based summary when LLM unavailable"""
    if not top_results:
        return f"No results found for '{query}'."
    
    # Extract key info
    top_categories = list(set(r.get('metadata', {}).get('category') for r in top_results[:5] if r.get('metadata', {}).get('category')))
    avg_score = sum(r.get('score', 0) for r in top_results[:5]) / min(5, len(top_results))
    
    summary = f"The search for '{query}' returned {len(top_results)} relevant documents. "
    
    if top_categories:
        summary += f"Top results are primarily from: {', '.join(top_categories[:3])}. "
    
    summary += f"Average relevance score: {avg_score:.2f}. "
    
    if bottom_results:
        summary += "Lower-ranked results show less term overlap and different topical focus."
    
    return summary


def _fallback_analytics_explanation(analysis_type: str, 
                                    analysis_data: Dict) -> str:
    """Rule-based explanation when LLM unavailable"""
    if analysis_type == "category_distribution":
        data = analysis_data.get('data', {})
        if data:
            top_cat = list(data.keys())[0]
            return f"The corpus is dominated by '{top_cat}' content. This reflects the original dataset composition and source selection."
    
    elif analysis_type == "top_bottom_comparison":
        return "High-ranked documents contain more query-relevant terms and metadata matches. Low-ranked documents have less topical overlap."
    
    elif analysis_type == "term_frequency":
        return "Frequent terms represent the core vocabulary of the corpus. Domain-specific terms indicate the dataset's topical focus."
    
    elif analysis_type == "source_bias":
        return "Source distribution reflects the original dataset composition. Uneven distribution may affect perspective diversity in results."
    
    return "Pattern analysis based on statistical distribution of document features."


def _fallback_result_explanation(doc: Dict, query: str, 
                                 matched_terms: List[str]) -> str:
    """Rule-based result explanation when LLM unavailable"""
    score = doc.get('score', 0)
    
    if score > 0.7:
        relevance = "highly relevant"
    elif score > 0.4:
        relevance = "moderately relevant"
    else:
        relevance = "marginally relevant"
    
    explanation = f"This document is {relevance} to '{query}'. "
    
    if matched_terms:
        explanation += f"Key matches: {', '.join(matched_terms[:5])}. "
    
    category = doc.get('metadata', {}).get('category')
    if category:
        explanation += f"Category: {category}."
    
    return explanation


def get_status() -> Dict[str, Any]:
    """Get LLM service status"""
    provider = detect_provider()
    
    if provider == "lm_studio":
        try:
            response = requests.get("http://localhost:961/v1/models", timeout=2)
            models = response.json().get('data', [])
            return {
                "status": "available",
                "provider": "LM Studio",
                "endpoint": LM_STUDIO_URL,
                "models": [m.get('id') for m in models]
            }
        except:
            pass
    
    elif provider == "ollama":
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            models = response.json().get('models', [])
            return {
                "status": "available",
                "provider": "Ollama",
                "endpoint": OLLAMA_URL,
                "models": [m.get('name') for m in models]
            }
        except:
            pass
    
    return {
        "status": "unavailable",
        "provider": "Fallback (Rule-based)",
        "message": "No LLM running. Start LM Studio or Ollama for AI explanations.",
        "fallback": True
    }


def configure_lm_studio(host: str = "localhost", port: int = 1234):
    """Configure LM Studio endpoint if using custom settings"""
    global LM_STUDIO_URL
    LM_STUDIO_URL = f"http://{host}:{port}/v1/chat/completions"
    return {"status": "configured", "url": LM_STUDIO_URL}
