-- Supabase Table Setup
-- Run this SQL in your Supabase SQL Editor first.
-- Reviews live in a separate table: run reviews_setup.sql (and review_author_setup.sql) after this.

-- Create products table
CREATE TABLE products (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  image TEXT,
  owner_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_products_created_at ON products(created_at DESC);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_owner_id ON products(owner_id);

-- Enable Row Level Security (RLS)
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (for development)
-- WARNING: In production, create more restrictive policies
CREATE POLICY "Allow all operations on products" ON products
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- If this DB was created with the old products.reviews JSONB column:
--   DROP FUNCTION IF EXISTS count_reviews(products);
--   ALTER TABLE products DROP COLUMN IF EXISTS reviews;
