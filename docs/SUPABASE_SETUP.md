# Supabase Setup Guide

Set up Supabase for products, embeddings (pgvector), auth, saved products, and chat history.

## Prerequisites

- Supabase account (free tier is fine)
- OpenAI API key and Python packages already set up (see [QUICK_START.md](QUICK_START.md))

---

## Step 1: Create a project

1. Go to https://supabase.com and create a project
2. Save the database password
3. Wait until the project is ready

---

## Step 2: Run SQL scripts (SQL Editor)

Run these **in order** from this repo (paste each file into **SQL Editor → New query → Run**):

| Order | File | Purpose |
|-------|------|---------|
| 1 | `backend/sql/supabase_setup.sql` | `products` table |
| 2 | `backend/sql/pgvector_setup.sql` | `document_embeddings` + `match_document_embeddings` |
| 3 | `backend/sql/saved_products_setup.sql` | `saved_products` + RLS |
| 4 | `backend/sql/chat_history_setup.sql` | `chat_messages` + RLS |

SQL is **not** run by the Python app — only in the Supabase SQL Editor.

If saved list or chat history returns 400, those tables/policies are usually missing. If chat finds no reviews, confirm `pgvector_setup.sql` ran and sample upload completed.

---

## Step 3: Auth settings

1. **Authentication → Providers → Email** — enable Email
2. For local/demo use, **disable Confirm email** (otherwise signup users cannot sign in)
3. Username/password in the UI maps to a synthetic email like `username@users.local` on the backend — users never enter an email

Username rules: `[a-zA-Z0-9_]{3,30}` (not an email address).

If you signed up while Confirm email was on, delete that user under **Authentication → Users** and sign up again after disabling confirmation.

---

## Step 4: API keys

**Project Settings → API**:

- **Project URL** → `SUPABASE_URL`
- **anon public** key → `SUPABASE_KEY` (not `service_role`)

---

## Step 5: Backend `.env`

```bash
cd backend
cp env_example.txt .env
```

```bash
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJ...   # anon public
HOST=0.0.0.0
PORT=8000
```

---

## Step 6: Verify

```bash
cd backend
source venv/bin/activate
python main.py
```

Open `http://localhost:8000` — expect something like:

```json
{"message":"Product Review Chat API","version":"2.0.0","database":"Supabase"}
```

Then upload sample data (server running):

```bash
python upload_sample_data.py
```

See [UPLOAD_DATA_GUIDE.md](UPLOAD_DATA_GUIDE.md).

---

## Schema overview

```
products               # shared catalog (id, name, description, image, reviews JSONB)
document_embeddings    # description + review text + vector(768) for RAG
saved_products         # per-user interest + note (RLS: own rows only)
chat_messages          # per-user, per-product history + sources (RLS: own rows only)
auth.users             # Supabase Auth
```

---

## Troubleshooting

| Symptom | Likely fix |
|---------|------------|
| `relation "products" does not exist` | Run `supabase_setup.sql` |
| `relation "document_embeddings" does not exist` / RPC missing | Run `pgvector_setup.sql` |
| Saved / chat history **400** | Run `saved_products_setup.sql` and `chat_history_setup.sql` |
| Invalid API key | Use **anon** key in `.env`, no quotes |
| Email not confirmed | Disable Confirm email; delete old user; sign up again |
| Signup fails on username | Use letters/numbers/`_` only, length 3–30 |

---

## Next steps

1. Run frontend on port 3000
2. Sign up → select product → chat
3. Optional: deploy backend + host static frontend
