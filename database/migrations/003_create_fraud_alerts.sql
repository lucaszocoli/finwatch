CREATE TABLE fraud_alerts (
    alert_id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    score FLOAT NOT NULL CHECK (score >= 0 AND score <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fraud_alerts_transaction_id ON fraud_alerts(transaction_id);
CREATE INDEX idx_fraud_alerts_user_id ON fraud_alerts(user_id);
CREATE INDEX idx_fraud_alerts_created_at ON fraud_alerts(created_at);
CREATE INDEX idx_fraud_alerts_score ON fraud_alerts(score);

CREATE TABLE user_stats (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    avg_transaction_amount DECIMAL(12,2),
    std_transaction_amount DECIMAL(12,2),
    transaction_count INTEGER DEFAULT 0,
    last_transaction_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
