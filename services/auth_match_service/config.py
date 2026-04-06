# S1とS2のゲームセッションサービスのエンドポイントリスト
# 実際は外部IPまたはホスト名になる
GAME_SESSION_ENDPOINTS = [
    {"ip": "192.168.200.102", "port": 8081, "server_id": "S1"},  # S1のゲームセッション
    {"ip": "192.168.200.103", "port": 8082, "server_id": "S2"},  # S2のゲームセッション
]

# 現在の負荷（使用状況）を追跡する（セッション割り当てに使用）
SERVER_STATUS = [ep.copy() for ep in GAME_SESSION_ENDPOINTS]
for status in SERVER_STATUS:
    # アクティブなセッション数を格納
    status["active_sessions"] = 0 

# 対戦モードの定義
MODE_CONFIG = {
    # 全員敵同士の対人戦 (FFA: Free-for-All)
    "ffa_4p": {"min_players": 4, "max_players": 4, "is_pvp": True}, # 4人対戦
    "ffa_3p": {"min_players": 3, "max_players": 3, "is_pvp": True}, # 3人対戦
    "ffa_2p": {"min_players": 2, "max_players": 2, "is_pvp": True}, # 2人対戦
    # CPU対戦モード
    "cpu": {"min_players": 1, "max_players": 1, "is_pvp": False}, # ユーザー1人 + CPU
}