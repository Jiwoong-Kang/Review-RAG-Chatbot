# Improvements

Notes from reviewing the database / auth / vector-store code. Ordered roughly by priority.

## High priority

### 1. Split reviews out of products
Reviews are stored as a JSON array on each `products` row. That makes adding one review rewrite the whole array, risks lost updates under concurrent writes, and makes per-review queries harder. Move reviews to their own table keyed by `product_id`.

### 2. Refresh access tokens with `refresh_token`
Sign-up / sign-in already return `access_token` and `refresh_token`, and the frontend stores both in `localStorage`. There is no flow yet that uses `refresh_token` to obtain a new access token when the current one expires. Add that so users stay signed in without logging in again.

### 3. Embed only what changed
`create_embeddings` deletes all embeddings for a product and rebuilds them whenever a product is uploaded or a review is added. With many reviews this is slow and expensive. After reviews are separated, embed only new or updated rows instead of rebuilding everything.

### 4. Make embedding create safer
Embeddings are deleted first, then inserted. If insert fails mid-way, the product can end up with no searchable vectors. Prefer a safer replace strategy (e.g. write new rows then delete old ones, or use a transaction / upsert plan).

### 5. Real email auth later
For local development we avoid real email UX (synthetic `username@users.local`, Confirm email often disabled). Later, users should sign up / sign in with a real email address, including confirmation and recovery flows through Supabase Auth.

## Medium priority

### 6. Stable review order for summaries
`get_all_reviews_summary` has no `ORDER BY`, so which reviews feed the summary (first 20) can be unstable. Sort by `review_index` or date.

### 7. Distinguish errors from empty data
Several helpers return empty lists / empty summaries on DB or network failure. Callers then treat that like “no reviews” or “no matches”. Surface errors separately so the UI can show a real failure.

### 8. Lighter product list queries
`get_all_products` selects full `reviews` even for the list view. Return only fields needed for the list (e.g. id, name, description, image, created_at) and load reviews on the detail page.

### 9. Similarity threshold on search
`search_similar_content` always returns up to `top_k` rows by rank, even when they are weakly related. Drop results below a similarity cutoff so the model gets less noise.

### 10. Wire up product summary in the UI
`generate_product_summary` in `chat_engine.py` already builds an overall review summary (pros, cons, overall take, who it suits), but nothing calls it yet—no API route and no frontend entry point. Expose it (e.g. product detail page or a “Review overview” action) so users can see key points without asking a chat question first. Also fix stable review ordering (#6) before relying on the first-20 slice.

### 11. Protect product write APIs with auth
`products.py` upload / delete / add-review endpoints do not use `bearer_token`. The frontend login gate hides this in normal use, but anyone who can hit the API can create or delete products. Require auth (and later decide who is allowed to manage catalog data).

### 12. Handle embedding failure after product upload/review add
`upload_product` and `add_review` save to `products` first, then call `create_embeddings`. If embedding fails afterward, the product/review can exist while chat search has nothing useful. Return a clear partial-failure status, retry embeddings, or roll back / mark the product as not searchable until embeddings succeed.

### 13. Align chat auth: optional API vs required UI
`POST /api/chat` uses `optional_bearer`, but the frontend requires login before entering the app. Pick one policy: either allow true guest chat in both layers, or make the chat route require `bearer_token` like history/saved.

### 14. Unify auth-related HTTP status codes
Some routes map `"Unauthorized"` to 401 and others effectively surface auth/DB failures as 400. Standardize so the frontend can reliably detect “please sign in again” vs validation/server errors.

## Lower priority / cleanup

### 15. Description embeddings vs chat usage
Product descriptions are embedded and stored, but chat retrieval uses `content_type="review"` only. Decide whether to keep description vectors for future use / verification, or stop embedding them to save cost.

### 16. Redundant `delete_embeddings` on product delete
Product delete already cascades to `document_embeddings`. Calling `delete_embeddings` first is redundant, and if product delete fails afterward the product can remain without embeddings.

### 17. Tighten CORS for production
`main.py` currently allows all origins (`allow_origins=["*"]`), which is fine for local development. Later restrict CORS to the real frontend origin(s).

## Suggested order

1. Split reviews from products
2. Token refresh with `refresh_token`
3. Incremental embeddings
4. Safer embedding replace
5. Real email auth
6. Protect product write APIs; align chat auth policy
7. Embedding failure handling after upload/review add
8. Summary ordering, clearer errors, lighter list queries, similarity threshold, status-code consistency
9. Wire up product summary UI
10. Description-embedding policy, delete cleanup, CORS tightening
