-- data_service/db_schema.sql

-- ユーザー情報テーブル
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash CHAR(64) NOT NULL,
    elo_rank INTEGER DEFAULT 1000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 対戦結果テーブル
CREATE TABLE IF NOT EXISTS match_results (
    id SERIAL PRIMARY KEY,
    match_id CHAR(36) NOT NULL, -- UUIDなどで生成される対戦ごとのID
    user_id VARCHAR(50) REFERENCES users(user_id),
    mode VARCHAR(10) NOT NULL,
    rank INTEGER NOT NULL,      -- このマッチでの順位 (1位, 2位など)
    score INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);