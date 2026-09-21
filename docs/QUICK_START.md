# Quick Start

Minimal path to run the app locally.

## 1. Python env + packages (~2 min)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Environment (~1 min)

```bash
cp env_example.txt .env
# Set OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY
```

Get an OpenAI key at https://platform.openai.com/api-keys

Supabase project + SQL: see [SUPABASE_SETUP.md](SUPABASE_SETUP.md)  
(You need all four SQL scripts and Confirm email disabled for local signup.)

## 3. Backend (~30 sec)

```bash
# still in backend/, venv active
python main.py
```

API: http://localhost:8000

## 4. Sample products + embeddings (~1 min)

**Keep the backend running.** In a second terminal:

```bash
cd backend
source venv/bin/activate
python upload_sample_data.py
```

This writes products and pgvector embeddings to Supabase. You only need to re-run it when refreshing sample data — not after every backend restart.

## 5. Frontend (~30 sec)

Third terminal:

```bash
cd frontend
python3 -m http.server 3000
```

Open http://localhost:3000

## 6. Sign in and chat

1. **Sign Up** — display name, username (`letters/numbers/_`, 3–30 chars), password
2. Select MacBook or iPhone
3. Ask e.g. “How is the battery life?” / “What are the downsides?”
4. Optionally save the product under **My Saved Products**

---

## Checklist

- [ ] venv + `pip install -r requirements.txt`
- [ ] `.env` with OpenAI + Supabase anon key
- [ ] Four SQL scripts run in Supabase; Confirm email off
- [ ] Backend on `:8000`
- [ ] `upload_sample_data.py` succeeded
- [ ] Frontend on `:3000`
- [ ] Signup / chat / citations work

---

## Troubleshooting

**`ModuleNotFoundError`** — activate venv (`source venv/bin/activate`), then reinstall requirements.

**OpenAI errors / 429** — check key and account credits.

**Chat finds 0 documents** — run `pgvector_setup.sql`, then `upload_sample_data.py` with the server up.

**Saved list / history 400** — run `saved_products_setup.sql` and `chat_history_setup.sql`.

**CORS** — backend `:8000`, frontend `:3000`.

More detail: [SETUP_GUIDE.md](SETUP_GUIDE.md)
