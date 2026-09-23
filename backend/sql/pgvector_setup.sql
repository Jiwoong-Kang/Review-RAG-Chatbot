-- pgvector setup for durable review / description embeddings
-- Run in Supabase SQL Editor AFTER supabase_setup.sql (products table must exist)

-- Enable the vector extension (available on Supabase by default)
CREATE EXTENSION IF NOT EXISTS vector;

-- One row per searchable chunk (product description or individual review)
CREATE TABLE IF NOT EXISTS document_embeddings (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  content_type TEXT NOT NULL CHECK (content_type IN ('description', 'review')),
  content TEXT NOT NULL,
  review_id TEXT,
  rating TEXT,
  review_date TEXT,
  review_index INTEGER,
  -- text-embedding-3-small produces 1536-dimensional embeddings
  embedding vector(1536) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_embeddings_product_id
  ON document_embeddings(product_id);

-- Cosine distance index (works well with normalized embeddings)
CREATE INDEX IF NOT EXISTS idx_document_embeddings_embedding
  ON document_embeddings
  USING hnsw (embedding vector_cosine_ops);

ALTER TABLE document_embeddings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow all operations on document_embeddings" ON document_embeddings;
CREATE POLICY "Allow all operations on document_embeddings" ON document_embeddings
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Similarity search scoped to a single product
CREATE OR REPLACE FUNCTION match_document_embeddings(
  query_embedding vector(1536),
  match_product_id text,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id text,
  product_id text,
  content_type text,
  content text,
  review_id text,
  rating text,
  review_date text,
  review_index int,
  similarity float
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    de.id,
    de.product_id,
    de.content_type,
    de.content,
    de.review_id,
    de.rating,
    de.review_date,
    de.review_index,
    (1 - (de.embedding <=> query_embedding))::float AS similarity
  FROM document_embeddings de
  WHERE de.product_id = match_product_id
  ORDER BY de.embedding <=> query_embedding
  LIMIT match_count;
$$;

GRANT EXECUTE ON FUNCTION match_document_embeddings(vector(1536), text, int)
  TO anon, authenticated, service_role;
