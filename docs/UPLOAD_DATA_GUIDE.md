# Upload Sample Data

Upload MacBook Pro and iPhone sample products into Supabase and build pgvector embeddings for RAG.

## Prerequisites

1. Supabase project ready
2. `backend/sql/supabase_setup.sql` and `backend/sql/pgvector_setup.sql` run
3. `backend/.env` with Supabase + OpenAI keys
4. Backend dependencies installed (`pip install -r requirements.txt`)
5. Images under `frontend/images/` (if you care about thumbnails)
6. **Backend server running** on `http://localhost:8000` (upload script calls the API)

Saved products / chat history SQL are not required for upload, but you need them for those UI features.

---

## Method 1: Upload script (recommended)

### Terminal 1 — API

```bash
cd backend
source venv/bin/activate
python main.py
```

### Terminal 2 — upload

```bash
cd backend
source venv/bin/activate
python upload_sample_data.py
```

Expected: both products succeed, 20 reviews each. The script deletes and re-uploads if a product already exists.

Embeddings are stored in Supabase (`document_embeddings`), so a backend restart does **not** clear them. Re-run the upload script only when you want to refresh sample products or regenerate vectors.

---

## Method 2: Web UI

1. Start backend + frontend (`python3 -m http.server 3000` in `frontend/`)
2. Sign in at http://localhost:3000
3. Use **+ Upload Product** and paste fields from `sample_products.json`

---

## Method 3: API (cURL)

```bash
curl -X POST http://localhost:8000/api/products/upload \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{ ... product JSON ... }
EOF
```

Prefer the script or UI unless you need raw API testing. Full payloads live in `sample_products.json` at the repo root.

---

## Verify

**Supabase** → Table Editor:

- `products` → `macbook_pro_m3_2024`, `iphone_15_pro_max_2024`
- `document_embeddings` → description + review rows per product

**API**

```bash
curl http://localhost:8000/api/products
```

**UI** — product list on the left; ask a question and check that sources/citations appear.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| Cannot connect to API | Start `python main.py` first |
| Product already exists | Script usually deletes/retries; or `DELETE /api/products/{id}` then re-run |
| `SUPABASE_URL` / key issues | Check `backend/.env` |
| `relation "products" does not exist` | Run `backend/sql/supabase_setup.sql` |
| `relation "document_embeddings" does not exist` | Run `backend/sql/pgvector_setup.sql` |
| Chat finds 0 documents | Confirm pgvector SQL ran, then re-run `upload_sample_data.py` |
| Images missing | Paths like `images/mbp.png` under `frontend/` |

---

## What gets written

- Product metadata + 20 reviews → **Supabase `products`**
- Description + review embeddings → **Supabase `document_embeddings` (pgvector)**

To add more products, edit `sample_products.json` and run the upload script again.
