-- PostgreSQL initialization script for AI Search Server
-- This script creates the necessary databases for LiteLLM and Keycloak services
-- It runs automatically when PostgreSQL container starts with an empty data directory

-- =============================================================================
-- Keycloak Database Setup
-- =============================================================================

-- Create keycloak database if it doesn't exist
SELECT 'CREATE DATABASE keycloak'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak')\gexec

-- Connect to keycloak database to set up additional configurations
\c keycloak;

-- Create schema if needed (optional, Keycloak will handle its own schema)
-- CREATE SCHEMA IF NOT EXISTS keycloak;

-- Grant all privileges on keycloak database to the admin user
-- Note: The admin user is created by POSTGRES_USER environment variable
\c postgres;
GRANT ALL PRIVILEGES ON DATABASE keycloak TO admin;

-- Allow admin user to create schemas in keycloak database
GRANT CREATE ON DATABASE keycloak TO admin;

-- =============================================================================
-- LiteLLM Database Setup
-- =============================================================================

-- Create litellm database if it doesn't exist
SELECT 'CREATE DATABASE litellm'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'litellm')\gexec

-- Connect to litellm database to set up additional configurations
\c litellm;

-- Create schema if needed (optional, LiteLLM will handle its own schema)
-- CREATE SCHEMA IF NOT EXISTS litellm;

-- Grant all privileges on litellm database to the admin user
\c postgres;
GRANT ALL PRIVILEGES ON DATABASE litellm TO admin;

-- Allow admin user to create schemas in litellm database
GRANT CREATE ON DATABASE litellm TO admin;

-- =============================================================================
-- Additional Configuration
-- =============================================================================

-- Ensure the admin user has necessary privileges for both services
ALTER USER admin CREATEDB;

-- Set default encoding for better compatibility
ALTER DATABASE keycloak SET client_encoding TO 'UTF8';
ALTER DATABASE litellm SET client_encoding TO 'UTF8';

-- Set default transaction isolation level for better performance
ALTER DATABASE keycloak SET default_transaction_isolation TO 'read committed';
ALTER DATABASE litellm SET default_transaction_isolation TO 'read committed';

-- =============================================================================
-- Verification Output
-- =============================================================================

-- List all databases (for logging purposes)
\l

-- Show user privileges (for logging purposes)
\du

-- Output a success message
\echo 'Database initialization completed successfully!'
\echo 'Created databases: keycloak, litellm'
\echo 'Configured user: admin'
