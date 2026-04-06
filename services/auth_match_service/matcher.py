from config import SERVER_STATUS, MODE_CONFIG
import time

# 対人戦モードのリストを作成 (クラス外で定義してもOK)
PVP_MODES = [mode for mode in MODE_CONFIG if MODE_CONFIG[mode]["is_pvp"]]

class Matcher:
    def __init__(self):
        # モードごとのマッチングキューを初期化
        self.matching_queue = {mode: [] for mode in MODE_CONFIG if MODE_CONFIG[mode]["is_pvp"]}
        # マッチング成立情報を一時保存する辞書 { user_id: match_result }
        self.pending_matches = {}
        # ACTIVE_SESSIONS は外部から更新されるか、別のサービスで管理

    def reset_matcher_state(self):
        """
        サーバーが起動する際にMATCHING_QUEUE, PENDING_MATCHESをリセットする関数
        """
        self.matching_queue = {mode: [] for mode in MODE_CONFIG if MODE_CONFIG[mode]["is_pvp"]}
        self.pending_matches = {}
        # ACTIVE_SESSIONS もリセットすべきだが、それは game_logic.py の仕事

    def assign_game_server(self):
        """
        最も負荷の低い（アクティブセッションが少ない）ゲームサーバーを選択する
        この簡易版では、ラウンドロビン（順番）や単純な最小セッション数で選択
        """
        # 注意: SERVER_STATUSはconfig.pyからグローバル変数としてアクセスされる想定
        # または、初期化時にコンストラクタで受け取るべき
        min_load_server = min(SERVER_STATUS, key=lambda x: x["active_sessions"])
        
        # 選択したサーバーのセッション数を増やす（割り当てたため）
        min_load_server["active_sessions"] += 1 
        
        # クライアントに返す接続情報
        return min_load_server["ip"], min_load_server["port"]

    def start_matchmaking(self, user_id, mode):
        """
        ユーザーをマッチングキューに入れ、成立したら接続先を返す
        """
        if mode not in MODE_CONFIG:
            return {"status": "error", "message": f"Invalid game mode: {mode}"}

        mode_info = MODE_CONFIG[mode]
        
        # ★★★ 既存の処理に優先して、成立済みのマッチングがないかチェック ★★★
        if user_id in self.pending_matches:
            return self.pending_matches.pop(user_id) # 成立情報を返し、辞書から削除

        # 1. CPU対戦モードの場合 (PVE)
        if not mode_info["is_pvp"]:
            # CPU対戦は即時成立
            # CPUの人数を max_players - 1 で計算
            num_cpu = mode_info["max_players"] - 1
            cpu_players = [f"CPU_{i+1}" for i in range(num_cpu)]
            
            # ゲームサーバーを確保
            ip, port = self.assign_game_server()

            # 接続情報とマッチングしたプレイヤーリストを返す
            return {
                "status": "matched",
                "server_ip": ip,
                "server_port": port,
                "mode": mode,
                "players": [user_id] + cpu_players # ユーザーとCPU
            }

        # 2. 対人戦モードの場合 (PVP: ffa_2p, ffa_3p, ffa_4p)
        current_queue = self.matching_queue[mode]
        
        # 既にキューにいるかチェック
        if user_id not in [entry["user_id"] for entry in current_queue]:
            current_queue.append({"user_id": user_id, "time": time.time()})
        

        required_players = mode_info["min_players"]

        if len(current_queue) >= required_players:
            # マッチング成立
            matched_entries = current_queue[:required_players]
            del current_queue[:required_players]
            
            matched_players = [entry["user_id"] for entry in matched_entries]

            # ゲームサーバーを確保
            ip, port = self.assign_game_server()

            match_result = {
                "status": "matched",
                "server_ip": ip,
                "server_port": port,
                "mode": mode,
                "players": matched_players
            }
            
            # ★★★ 成立した全員の情報をPENDING_MATCHESに保存 ★★★
            for p_id in matched_players:
                self.pending_matches[p_id] = match_result
            
            # 成立情報のうち、リクエストを送ってきたユーザーの情報を即座に返す
            return self.pending_matches.pop(user_id)
        else:
            # マッチング待ち
            return {"status": "waiting", "mode": mode, "queue_size": len(current_queue), "required": required_players}
        
# 注意: 実際のシステムでは、セッション終了時に "active_sessions" を減らす処理が必要です
# (例: ゲームセッションサービスからS1に終了通知APIをコールさせる)