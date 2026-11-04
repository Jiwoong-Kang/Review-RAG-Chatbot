-- Reviews table (split out of products.reviews JSONB)
-- Run in the Supabase SQL Editor AFTER supabase_setup.sql (products must exist).
-- App code reads/writes this table via ReviewDatabase.
-- Review counts for the product list come from ReviewDatabase.counts_by_product,
-- not from a SQL count_reviews(products) helper.

CREATE TABLE IF NOT EXISTS reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  review_id TEXT NOT NULL,
  content TEXT NOT NULL,
  rating DOUBLE PRECISION,
  review_date TEXT,
  review_index INTEGER NOT NULL DEFAULT 0,
  author_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  author_username TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (product_id, review_id)
);

-- If reviews already exists without author columns, also run review_author_setup.sql.

CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product_id_index
  ON reviews(product_id, review_index);

ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow all operations on reviews" ON reviews;
CREATE POLICY "Allow all operations on reviews" ON reviews
  FOR ALL
  USING (true)
  WITH CHECK (true);

