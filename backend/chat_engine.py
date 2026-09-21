import os
import re
from typing import Dict, List, Optional
from openai import OpenAI
from vector_store import search_similar_content, get_all_reviews_summary

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"))

# The model emits this on the first line when the context cannot answer the question
INSUFFICIENT_EVIDENCE_TOKEN = "INSUFFICIENT_EVIDENCE"

NO_EVIDENCE_MESSAGE = "I don't have any reviews indexed for this product yet, so I can't answer from evidence."

def _parse_rating(raw_rating: str) -> Optional[float]:
    """Ratings are stored as strings in embedding metadata ('4.5', 'N/A')."""
    try:
        return float(raw_rating)
    except (TypeError, ValueError):
        return None

def generate_response(
    product_id: str,
    user_message: str,
    conversation_history: Optional[List[dict]] = None
) -> Dict:
    """
    Generate responses using RAG (Retrieval-Augmented Generation) pattern.
    1. Search for relevant reviews/descriptions related to user's question
    2. Pass retrieved content as context to LLM, each review tagged with a citation marker
    3. Return the answer along with the reviews it was allowed to cite

    Returns a dict with keys: answer, sources, insufficient_evidence.
    """
    
    if conversation_history is None:
        conversation_history = []
    
    # 1. Search for relevant reviews and descriptions
    search_results = search_similar_content(product_id, user_message, top_k=5)
    
    # Debug logging
    print(f"[DEBUG] Search results for '{user_message}':")
    print(f"  - Found {len(search_results['documents'])} documents")
    if search_results['documents']:
        print(f"  - First result type: {search_results['metadatas'][0].get('type', 'unknown')}")
    else:
        print(f"  - WARNING: No documents found! Check embeddings.")
    
    # 2. Build context, numbering each review so the answer can cite it
    context_parts = []
    sources = []
    
    for doc, meta in zip(search_results['documents'], search_results['metadatas']):
        if meta['type'] == 'description':
            context_parts.append(f"[Product Description]\n{doc}\n")
        elif meta['type'] == 'review':
            marker = len(sources) + 1
            rating = meta.get('rating', 'N/A')
            date = meta.get('date') or ""
            review_id = meta.get('review_id', f"review_{marker}")
            
            label = f"[{marker}] Review {review_id} - Rating: {rating}"
            if date:
                label += f" - Date: {date}"
            context_parts.append(f"{label}\n{doc}\n")
            
            sources.append({
                "marker": marker,
                "review_id": review_id,
                "content": doc,
                "rating": _parse_rating(rating),
                "date": date or None
            })
    
    context = "\n".join(context_parts)
    
    # Nothing retrieved: report missing evidence instead of asking the model to invent one
    if not context.strip():
        print(f"[WARNING] Empty context for product {product_id}!")
        print(f"[WARNING] This means embeddings might not be created properly.")
        return {
            "answer": NO_EVIDENCE_MESSAGE,
            "sources": [],
            "insufficient_evidence": True
        }
    
    # 3. Build prompt
    system_prompt = f"""You are a product review expert assistant.
When users ask about a product, provide accurate and helpful answers based on the provided product descriptions and actual user reviews.

Follow these rules:
1. Answer only based on the provided context (product descriptions and reviews). Never use outside knowledge.
2. Every claim taken from a review must end with that review's marker, e.g. "Battery lasts a full day [1]." Combine markers when several reviews agree, e.g. "[2][3]".
3. Only use markers that appear in the context below. Never invent a marker number.
4. When reviews disagree, that is still enough evidence. Summarize both sides with citations (e.g. positive [1][2], negative [3]), and if one side is more common, say so clearly. Do not answer with vague lines like "mixed / unclear / hard to say" without citing the concrete opinions.
5. Use {INSUFFICIENT_EVIDENCE_TOKEN} on the first line ONLY when the context does not discuss the asked topic at all. Conflicting opinions are not insufficient evidence. Do not guess or fill gaps with outside knowledge.
6. Respond in friendly and natural language that users can easily understand. Match the user's language when possible.
7. Emphasize points commonly mentioned across multiple reviews.

Product Information:
{context}
"""
    
    # 4. Build conversation history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add previous conversations (last 5 only)
    for msg in conversation_history[-5:]:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
    
    # Add current question
    messages.append({"role": "user", "content": user_message})
    
    # 5. Call OpenAI API
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo"
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = (response.choices[0].message.content or "").strip()
        
        # 6. Resolve evidence state and keep only the reviews the answer actually cited
        insufficient_evidence = answer.startswith(INSUFFICIENT_EVIDENCE_TOKEN)
        if insufficient_evidence:
            answer = answer[len(INSUFFICIENT_EVIDENCE_TOKEN):].lstrip(" :-\n")
            if not answer:
                answer = "The reviews lack information on this aspect."
            return {
                "answer": answer,
                "sources": [],
                "insufficient_evidence": True
            }
        
        cited_markers = {int(m) for m in re.findall(r"\[(\d+)\]", answer)}
        if cited_markers:
            sources = [s for s in sources if s["marker"] in cited_markers]
        
        return {
            "answer": answer,
            "sources": sources,
            "insufficient_evidence": False
        }
        
    except Exception as e:
        print(f"Error generating response: {e}")
        return {
            "answer": f"Sorry, an error occurred while generating the response: {str(e)}",
            "sources": [],
            "insufficient_evidence": False
        }

def generate_product_summary(product_id: str) -> str:
    """Summarize all reviews for a product."""
    
    summary_data = get_all_reviews_summary(product_id)
    
    if summary_data['total_reviews'] == 0:
        return "No reviews available yet."
    
    prompt = f"""Here is a description and {summary_data['total_reviews']} actual user reviews for a product.

Product Description:
{summary_data['description']}

Reviews:
"""
    
    for idx, review in enumerate(summary_data['reviews'][:20], 1):
        prompt += f"\nReview {idx} (Rating: {review['rating']}): {review['content']}\n"
    
    prompt += """

Please write a comprehensive summary including:
1. Main advantages (what users are most satisfied with)
2. Main disadvantages (what users are least satisfied with)
3. Overall evaluation
4. Who should buy this product

Please write in a friendly and easy-to-understand manner."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a product review analysis expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"An error occurred while generating summary: {str(e)}"

