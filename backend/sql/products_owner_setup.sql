-- Product ownership (run after supabase_setup.sql)
-- owner_id = uploading user; admins bypass ownership in the API via user_metadata.role = 'admin'

ALTER TABLE products
  ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_products_owner_id ON products(owner_id);

-- To make a user admin in Supabase Dashboard:
-- Authentication → Users → user → App Metadata / User Metadata:
--   { "role": "admin", "username": "...", ... }
-- This project reads role from user_metadata (same place as username).
