# Improvements

Notes from reviewing the database / auth / vector-store code. Ordered roughly by priority.

## Done (2026-11-02)

### 1. Split reviews out of products — done
Reviews live in a `reviews` table keyed by `product_id` (`reviews_setup.sql`, `ReviewDatabase`). Upload / list / detail / add-review no longer use `products.reviews` JSONB. Optional leftover: drop the unused `products.reviews` column when ready.

### 3. Embed only what changed — done
`add_review` uses `add_review_embedding` (single insert). Full `create_embeddings` remains for initial product upload only.

### 4. Make embedding create safer — done
`create_embeddings` upserts by id first, then deletes stale ids for that product (no delete-all-before-insert gap).

### Related work the same day
- Add-review UI (product `...` menu → modal); `review_id` auto-generated.
- Review authors: `author_user_id` / `author_username` on `reviews`, `author_username` on `document_embeddings` + match RPC (`review_author_setup.sql`). Logged-in add-review stores username; chat sources show username (or Anonymous for sample reviews).
- `#8` partly done: product list no longer loads review JSON (counts from `reviews` table).
- `#11` partly done: `POST .../reviews` requires `bearer_token`; upload / delete still open.

## High priority

### 2. Refresh access tokens with `refresh_token`
Sign-up / sign-in already return `access_token` and `refresh_token`, and the frontend stores both in `localStorage`. There is no flow yet that uses `refresh_token` to obtain a new access token when the current one expires. Add that so users stay signed in without logging in again.

### 5. Real email auth later
For local development we avoid real email UX (synthetic `username@users.local`, Confirm email often disabled). Later, users should sign up / sign in with a real email address, including confirmation and recovery flows through Supabase Auth.

## Medium priority

### 6. Stable review order for summaries
`get_all_reviews_summary` has no `ORDER BY`, so which reviews feed the summary (first 20) can be unstable. Sort by `review_index` or date.

### 7. Distinguish errors from empty data
Several helpers return empty lists / empty summaries on DB or network failure. Callers then treat that like “no reviews” or “no matches”. Surface errors separately so the UI can show a real failure.

### 8. Lighter product list queries — partly done
List no longer selects review JSON; still could trim other unused fields if needed.

### 9. Similarity threshold on search
`search_similar_content` always returns up to `top_k` rows by rank, even when they are weakly related. Drop results below a similarity cutoff so the model gets less noise.

### 10. Wire up product summary in the UI
`generate_product_summary` in `chat_engine.py` already builds an overall review summary (pros, cons, overall take, who it suits), but nothing calls it yet—no API route and no frontend entry point. Expose it (e.g. product detail page or a “Review overview” action) so users can see key points without asking a chat question first. Also fix stable review ordering (#6) before relying on the first-20 slice.

### 11. Protect product write APIs with auth — partly done
`add-review` requires `bearer_token`. Upload / delete still do not. Require auth on those too (and later decide who may manage catalog data).

### 12. Handle embedding failure after product upload/review add
`upload_product` and `add_review` save to DB first, then call embedding helpers. If embedding fails afterward, the product/review can exist while chat search has nothing useful. Return a clear partial-failure status, retry embeddings, or roll back / mark the product as not searchable until embeddings succeed.

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

### 18. Drop unused `products.reviews` JSONB
After confirming the app only uses the `reviews` table, drop the column and `count_reviews(products)`.

## Suggested order (remaining)

1. Token refresh with `refresh_token`
2. Finish product write auth (upload / delete); align chat auth policy
3. Embedding failure handling after upload/review add
4. Real email auth
5. Summary ordering, clearer errors, similarity threshold, status-code consistency
6. Wire up product summary UI
7. Description-embedding policy, delete cleanup, drop `products.reviews`, CORS tightening
