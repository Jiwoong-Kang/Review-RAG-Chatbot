-- Add review author fields (run after reviews_setup.sql and pgvector_setup.sql)
-- Safe to re-run: ADD COLUMN IF NOT EXISTS, then recreate match RPC.

ALTER TABLE reviews
  ADD COLUMN IF NOT EXISTS author_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS author_username TEXT;

ALTER TABLE document_embeddings
  ADD COLUMN IF NOT EXISTS author_username TEXT;

-- Recreate RPC so similarity search returns author_username
DROP FUNCTION IF EXISTS match_document_embeddings(vector(1536), text, int);

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
  author_username text,
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
    de.author_username,
    (1 - (de.embedding <=> query_embedding))::float AS similarity
  FROM document_embeddings de
  WHERE de.product_id = match_product_id
  ORDER BY de.embedding <=> query_embedding
  LIMIT match_count;
$$;

GRANT EXECUTE ON FUNCTION match_document_embeddings(vector(1536), text, int)
  TO anon, authenticated, service_role;
