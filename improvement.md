# Improvements

Remaining work first; completed items at the bottom.

## Suggested order

1. Real email auth (#5)
2. Product summary UI (#10) and browse-reviews UI (#19)
3. Description-embedding policy (#15), CORS (#17)
4. Optional: enforce `require_product_read` on GET list/detail; tighten products RLS

## High priority

### 5. Real email auth later
For local development we avoid real email UX (synthetic `username@users.local`, Confirm email often disabled). Later, users should sign up / sign in with a real email address, including confirmation and recovery flows through Supabase Auth.

## Medium priority

### 10. Wire up product summary in the UI
`generate_product_summary` in `chat_engine.py` already builds an overall review summary, but nothing calls it yet—no API route and no frontend entry point. Expose it (e.g. product detail or a “Review overview” action). On-demand generation (fetch current reviews when opened) is enough; no need for realtime auto-refresh at first.

### 19. Browse reviews in the UI
Selecting a product opens chat and shows a review **count**, but there is no screen to read the full review list. `GET /api/products/{id}` already returns `reviews`. Add a reviews view (panel, tab, or page) with content, rating, date, and `author_username` (or Anonymous). Fits well next to #10.

## Lower priority / cleanup

### 15. Description embeddings vs chat usage
Product descriptions are embedded and stored, but chat retrieval uses `content_type="review"` only. Keep description as product metadata/UI; decide whether to keep description **vectors** (cost) or stop embedding them. Chat should keep ignoring description for RAG.

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

### 2026-11-08
- **#16** Drop redundant `delete_embeddings` before product delete (DB CASCADE handles it)
- **#8** Lighter list query — skipped (`select *` is fine for now)
- **#9** Similarity threshold on search (`min_similarity=0.35`; empty → insufficient evidence)
- **#14** Unify service error HTTP codes: `raise_service_error` (401/500); saved maps 404/400/401/500 explicitly
- **#7** Distinguish errors from empty data:
  - `search_similar_content` / chat: search failure vs insufficient evidence
  - `list_reviews`, `get_all_products`, `count_reviews_by_product` → `{status, data|message}`
  - `get_all_reviews_summary` → status error vs empty reviews for `#10`
