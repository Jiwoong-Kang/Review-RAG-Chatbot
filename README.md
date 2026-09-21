# Product Review Chatbot

RAG chatbot that answers product questions from real user reviews, with citations, auth, saved products, and per-user chat history.

## Features

- **RAG Q&A**: Retrieves the most relevant reviews (pgvector), then answers with GPT
- **Review citations**: Answers cite source reviews; UI shows the supporting snippets
- **Auth gate**: Username / display name / password (Supabase Auth under the hood)
- **Saved products**: Interest level + personal note per user
- **Chat history**: Stored in Supabase per user + product (not localStorage)
- **Sample catalog**: MacBook Pro M3 and iPhone 15 Pro Max (20 reviews each)

## Architecture

```
reviewer/
├── backend/
│   ├── main.py              # FastAPI app (CORS + routers)
│   ├── chat_engine.py       # RAG generation + citations
│   ├── vector_store.py      # Sentence Transformers + Supabase pgvector search
│   ├── upload_sample_data.py
│   ├── database/            # Supabase client, auth, products, saved, chat history
│   ├── routers/             # auth, products, saved, chat
│   ├── sql/                 # Run these in Supabase SQL Editor
│   ├── requirements.txt
│   └── env_example.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js               # Boot
│   ├── auth.js / products.js / chat.js / saved.js
│   └── images/
├── docs/                    # Setup guides
├── sample_products.json
└── README.md
```

**Data roles**

| Store | Role |
|-------|------|
| **Supabase** | Products, reviews (source of truth), auth, saved products, chat messages, **embeddings (pgvector)** |
| **OpenAI** | Answer generation from retrieved context |
| **localStorage** | Auth session only |

Embeddings live in Supabase (`document_embeddings`) next to product data, so they survive backend restarts. Upload sample data once (or when you change products); you do not need to re-index after every API restart.

## Quick setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp env_example.txt .env
# Edit .env: OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY
```

### 2. Supabase

In the Supabase SQL Editor, run **in order**:

1. `backend/sql/supabase_setup.sql` — products
2. `backend/sql/pgvector_setup.sql` — embeddings table + match RPC
3. `backend/sql/saved_products_setup.sql` — saved products + RLS
4. `backend/sql/chat_history_setup.sql` — chat messages + RLS

Also under **Authentication → Providers → Email**:

- Enable Email provider
- For local testing, **disable Confirm email**

Details: [`docs/SUPABASE_SETUP.md`](docs/SUPABASE_SETUP.md)

### 3. Run

```bash
# Terminal 1 — API
cd backend && source venv/bin/activate && python main.py
# → http://localhost:8000

# Terminal 2 — sample products + embeddings (server must be running)
cd backend && source venv/bin/activate && python upload_sample_data.py

# Terminal 3 — UI
cd frontend && python3 -m http.server 3000
# → http://localhost:3000
```

### 4. Use the app

1. Sign up with **username** (`[a-zA-Z0-9_]{3,30}`), name, password — not an email address
2. Select a product and ask questions (e.g. battery life, pros/cons)
3. Optionally save the product with interest level + note
4. Switch products — chat history restores from Supabase

## Docs

| Guide | Contents |
|-------|----------|
| [`docs/QUICK_START.md`](docs/QUICK_START.md) | Minimal run path |
| [`docs/SUPABASE_SETUP.md`](docs/SUPABASE_SETUP.md) | Project, SQL, auth settings |
| [`docs/UPLOAD_DATA_GUIDE.md`](docs/UPLOAD_DATA_GUIDE.md) | Sample data upload |
| [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md) | Ops notes & troubleshooting |

## Tech stack

- **Backend**: FastAPI, OpenAI GPT-4o-mini, Sentence Transformers, Supabase + pgvector
- **Frontend**: Vanilla JS (modular), HTML/CSS

## API (overview)

Swagger: `http://localhost:8000/docs`

| Area | Endpoints |
|------|-----------|
| Auth | `POST /api/auth/signup`, `/signin`, `/signout`, `GET /api/auth/me` |
| Products | `GET/POST/DELETE /api/products...` |
| Saved | `GET/POST/DELETE /api/saved-products...` |
| Chat | `POST /api/chat`, `GET /api/chat/history/{product_id}` |

## Requirements

- Python 3.9+
- OpenAI API key
- Supabase project (URL + **anon** key)

## License

MIT
