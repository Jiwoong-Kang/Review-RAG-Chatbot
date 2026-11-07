# Improvements

Remaining work first; completed items at the bottom.

## Suggested order

1. Real email auth (#5)
2. Clearer errors (#7), similarity threshold (#9), status-code consistency (#14)
3. Product summary UI (#10) and browse-reviews UI (#19)
4. Description-embedding policy (#15), delete cleanup (#16), CORS (#17)
5. Optional: enforce `require_product_read` on GET list/detail; tighten products RLS

## High priority

### 5. Real email auth later
For local development we avoid real email UX (synthetic `username@users.local`, Confirm email often disabled). Later, users should sign up / sign in with a real email address, including confirmation and recovery flows through Supabase Auth.

## Medium priority

### 7. Distinguish errors from empty data
Several helpers return empty lists / empty summaries on DB or network failure. Callers then treat that like “no reviews” or “no matches”. Surface errors separately so the UI can show a real failure.

### 9. Similarity threshold on search
`search_similar_content` always returns up to `top_k` rows by rank, even when they are weakly related. Drop results below a similarity cutoff so the model gets less noise.

### 10. Wire up product summary in the UI
`generate_product_summary` in `chat_engine.py` already builds an overall review summary, but nothing calls it yet—no API route and no frontend entry point. Expose it (e.g. product detail or a “Review overview” action).

### 14. Unify auth-related HTTP status codes
Some routes map `"Unauthorized"` to 401 and others surface auth/DB failures as 400. Standardize so the frontend can reliably detect “please sign in again” vs validation/server errors.

### 19. Browse reviews in the UI
Selecting a product opens chat and shows a review **count**, but there is no screen to read the full review list. `GET /api/products/{id}` already returns `reviews`. Add a reviews view (panel, tab, or page) with content, rating, date, and `author_username` (or Anonymous). Fits well next to #10.

## Lower priority / cleanup

### 8. Lighter product list queries — nearly done
List no longer loads review JSON (counts come from the `reviews` table). Optional: trim any other unused product fields from the list query.

### 15. Description embeddings vs chat usage
Product descriptions are embedded and stored, but chat retrieval uses `content_type="review"` only. Decide whether to keep description vectors for future use / verification, or stop embedding them to save cost.

### 16. Redundant `delete_embeddings` on product delete
Product delete already cascades to `document_embeddings`. Calling `delete_embeddings` first is redundant, and if product delete fails afterward the product can remain without embeddings.

### 17. Tighten CORS for production
`main.py` currently allows all origins (`allow_origins=["*"]`), which is fine for local development. Later restrict CORS to the real frontend origin(s).

---

## Done

### 2026-11-02
- **#1** Split reviews out of products (`reviews` table, `ReviewDatabase`)
- **#3** Incremental embed on review add (`add_review_embedding`)
- **#4** Safer full embed replace (upsert, then delete stale ids)
- Add-review UI; review authors (`author_username`) in DB + chat sources
- **#18** `supabase_setup.sql` no longer creates `products.reviews` JSONB / `count_reviews`  
  Existing DB cleanup if needed:
  ```sql
  DROP FUNCTION IF EXISTS count_reviews(products);
  ALTER TABLE products DROP COLUMN IF EXISTS reviews;
  ```

### 2026-11-06
- **#2** Refresh access tokens (`POST /api/auth/refresh`, `apiJson` 401 retry)
- **#6** Summary uses all reviews, ordered by `review_index`
- **#12** Embedding failure rolls back: delete product on upload embed fail; delete review on add-review embed fail
- **#13** Chat requires login (`bearer_token`); `optional_bearer` kept in deps for possible future use
- **#11** Product ownership + admin:
  - `products.owner_id` (`products_owner_setup.sql` / `supabase_setup.sql`)
  - Upload / delete require login; delete is owner-or-admin
  - Admin via `user_metadata.role = "admin"` or `ADMIN_USERNAMES` env
  - `require_product_read` helper exists but GET list/detail stay public
  - Sample uploader signs in via `SAMPLE_UPLOAD_USERNAME` / `SAMPLE_UPLOAD_PASSWORD`
