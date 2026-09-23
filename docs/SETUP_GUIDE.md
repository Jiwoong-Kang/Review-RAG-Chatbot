# Setup Guide

Operational notes for running and debugging the current stack.

## Required credentials

### OpenAI

1. https://platform.openai.com/api-keys → create a secret key
2. Put it in `backend/.env` as `OPENAI_API_KEY`

Model used: `gpt-4o-mini` in `backend/chat_engine.py` (change there if you want another model).

### Supabase

1. Project URL + **anon** key in `.env`
2. Run SQL in order (see [SUPABASE_SETUP.md](SUPABASE_SETUP.md)):
   - `backend/sql/supabase_setup.sql`
   - `backend/sql/pgvector_setup.sql`
   - `backend/sql/saved_products_setup.sql`
   - `backend/sql/chat_history_setup.sql`
3. Email auth on; **Confirm email off** for local demos

---

## How the pieces fit

| Piece | What it stores / does |
|-------|------------------------|
| Supabase `products` | Shared catalog + review JSON (source of truth) |
| Supabase `document_embeddings` | Description/review text + pgvector embeddings for RAG |
| Supabase `saved_products` | Per-user interest + note |
| Supabase `chat_messages` | Per-user chat history + citation payloads |
| localStorage | Auth session JWT only |

Chat answers use retrieved reviews only; conflicting reviews should be summarized with citations (see system prompt in `chat_engine.py`).

---

## Auth UX notes

- Users sign up with **username**, not email
- Backend maps username → `username@users.local` for Supabase Auth
- Valid username: `[a-zA-Z0-9_]{3,30}`
- After API/auth changes, restart the backend
- Stuck “email not confirmed” users: delete in Supabase Auth → Users, sign up again

---

## RAG / embeddings notes

- Similarity search uses OpenAI `text-embedding-3-small` (1536-dim) + Supabase pgvector
- Vectors are durable in Postgres; restarting the API does **not** clear them
- Re-upload (script or UI) when you change product/review content and want fresh embeddings
- Match RPC: `match_document_embeddings(query_embedding, match_product_id, match_count)`
- If you previously used 768-dim local embeddings, drop `document_embeddings` / recreate from `pgvector_setup.sql`, then re-upload

---

## Common failures

| Symptom | Check |
|---------|--------|
| FastAPI / module import errors | `source venv/bin/activate`; broken venv → recreate |
| Chat empty / “no reviews indexed” | `pgvector_setup.sql` missing, or products never uploaded |
| Vague “mixed / unclear” answers | Prompt/rules in `chat_engine.py` (should cite both sides) |
| Saved / history HTTP 400 | Missing SQL tables or RLS |
| Signup / sign-in fails | Confirm email disabled? Username format? Backend restarted? |
| OpenAI 429 | Billing / rate limits on the OpenAI account |
| CORS | Frontend origin must be allowed; default local ports 3000 → 8000 |

---

## Optional later improvements

- Stricter RLS on `products` / `document_embeddings` for production
- Deploy API (Railway, Fly, etc.) + static frontend (Vercel/Netlify)
- Rate limiting / HTTPS at the reverse proxy

These are optional; the app already uses Supabase for persistence and Auth for multi-user saved products and history.
