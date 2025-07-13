-- Migration: Create user permissions table
-- Description: Control user access to core features (import data, create project, send chat)

-- Create user permissions table
CREATE TABLE IF NOT EXISTS user_permissions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    can_import_data BOOLEAN DEFAULT TRUE,
    can_create_project BOOLEAN DEFAULT TRUE,
    can_send_chat BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_permissions_updated_at BEFORE UPDATE
    ON user_permissions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE user_permissions IS 'Controls user access to core features';
COMMENT ON COLUMN user_permissions.user_id IS 'Reference to auth.users.id';
COMMENT ON COLUMN user_permissions.can_import_data IS 'Permission to access import data functionality';
COMMENT ON COLUMN user_permissions.can_create_project IS 'Permission to create new projects';
COMMENT ON COLUMN user_permissions.can_send_chat IS 'Permission to send chat messages'; 