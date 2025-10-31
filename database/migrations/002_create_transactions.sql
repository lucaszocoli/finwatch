CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    type VARCHAR(30) NOT NULL CHECK (type IN ('deposit', 'withdraw', 'transfer', 'payment')),
    status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (status IN ('completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location VARCHAR(255),
    device_info VARCHAR(255),
    is_flagged BOOLEAN DEFAULT FALSE,
    is_analyzed BOOLEAN DEFAULT FALSE,
    analyzed_at TIMESTAMP NULL
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_transactions_is_flagged ON transactions(is_flagged);
CREATE INDEX idx_transactions_amount ON transactions(amount);
CREATE INDEX idx_transactions_is_analyzed ON transactions(is_analyzed);
CREATE INDEX idx_transactions_analyzed_at ON transactions(analyzed_at);
CREATE INDEX idx_transactions_flagged_analyzed ON transactions(is_flagged, is_analyzed);
