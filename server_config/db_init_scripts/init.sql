-- distributed_game_project/server_config/db_init_scripts/init.sql

-- ユーザーテーブル (auth_match_serviceが使用)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL -- pending, approved, rejected
);

-- ゲームセッションテーブル (game_session_serviceが使用)
CREATE TABLE IF NOT EXISTS game_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    mode VARCHAR(50) NOT NULL,
    players TEXT[] NOT NULL, -- プレイヤーIDの配列
    server_ip VARCHAR(255) NOT NULL,
    server_port INT NOT NULL,
    status VARCHAR(50) DEFAULT 'active' NOT NULL, -- active, completed, cancelled
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE
);

-- ユーザーのランクや統計 (data_serviceが使用)
CREATE TABLE IF NOT EXISTS user_stats (
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    rank INT DEFAULT 1000,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    PRIMARY KEY (user_id)
);