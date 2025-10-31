\echo 'Initializing database structure...'

-- Execute migrations
\i /docker-entrypoint-initdb.d/migrations/001_create_users.sql
\i /docker-entrypoint-initdb.d/migrations/002_create_transactions.sql
\i /docker-entrypoint-initdb.d/migrations/003_create_fraud_alerts.sql

\echo 'Database initialized successfully!'
