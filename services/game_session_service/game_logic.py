# import json
# import asyncio
# from urllib.parse import urlparse, parse_qs

# # 現在アクティブなセッションを管理 (セッションID -> 接続されているクライアントのセット)
# ACTIVE_SESSIONS = {}

# def is_valid_input(message):
#     """
#     簡易的なチート検証ロジック:
#     - 入力メッセージが想定されたフォーマットかチェック
#     - フレーム番号が急激に飛んでいないか（スキップ）などをチェック可能
#     クライアントからの入力データ構造を安全に検証する
#     期待される構造: {"action": "...", "frame": <int>, "user_id": "..."}
#     """
#     try:
#         data = json.loads(message)
        
#         # ★★★ 必須キーのチェック ★★★
#         required_keys = ["action", "frame", "user_id"]
#         if not all(key in data for key in required_keys):
#             print(f"[S] Validation FAILED: Missing keys in input: {data}")
#             return False
            
#         # ★★★ データ型のチェック ★★★
#         if not isinstance(data["frame"], int) or not isinstance(data["action"], str):
#              print(f"[S] Validation FAILED: Invalid data types.")
#              return False

#         # ... (その他のチート検証ロジックをここに追加) ...
#         return True
        
#     except json.JSONDecodeError:
#         print(f"[S] Validation FAILED: JSON Decode Error.")
#         return False
#     except Exception as e:
#         print(f"[S] Validation FAILED: Unexpected error: {e}")
#         return False

# # ★★★ ゲーム状態を管理する辞書 ★★★
# GAME_STATES = {} # { session_id: { user_id: { x: int, y: int, health: int, state: str }, ... } }

# def initialize_game_state(session_id, player_ids):
#     """セッション開始時に初期状態を作成する"""
#     state = {}
#     for i, p_id in enumerate(player_ids):
#         state[p_id] = {
#             "x": 50 + i * 150, 
#             "y": 400, 
#             "health": 100,      # 体力
#             "state": "idle",    # 状態 (idle, attacking, jumping, hit, dead)
#             "frame": 0          # 最終処理フレーム
#         }
#     GAME_STATES[session_id] = state
#     return state


# # ★★★ 新規追加: 攻撃判定ロジック ★★★
# def check_hit(attacker_state, target_state):
#     """
#     攻撃判定の簡易ロジック
#     - 攻撃者がターゲットの近くにいるか
#     """
#     # 簡易: 攻撃時のX座標がターゲットのX座標に非常に近いか
#     if abs(attacker_state["x"] - target_state["x"]) < 50:
#         return True
#     return False


# async def process_game_input(session_id, input_data):
#     """
#     クライアントからの入力メッセージを処理し、状態を更新、必要ならブロードキャストする
#     """
#     state = GAME_STATES.get(session_id)
#     if not state:
#         return # セッションが存在しない

#     user_id = input_data['user_id']
#     action = input_data['action']
    
#     current_player = state.get(user_id)
#     if not current_player:
#         return

#     # 1. 移動処理 (ローカルで処理済みだが、チート検証のためサーバーでも限界値をチェックすべき)
#     if action == 'move_left':
#         current_player["x"] -= 5 # 簡易的な移動
        
#     elif action == 'move_right':
#         current_player["x"] += 5 # 簡易的な移動
        
#     # 2. 攻撃処理 (サーバー側で判定を行う)
#     elif action == 'attack_punch':
#         # 攻撃状態へ移行
#         current_player["state"] = "attacking"
        
#         # 相手プレイヤーを特定
#         opponent_ids = [p for p in state.keys() if p != user_id]
        
#         for op_id in opponent_ids:
#             opponent_state = state[op_id]
            
#             # 攻撃判定の検証
#             if check_hit(current_player, opponent_state):
#                 damage = 10 
#                 opponent_state["health"] -= damage
#                 opponent_state["state"] = "hit"
#                 print(f"[S] HIT: {user_id} hit {op_id}. Health: {opponent_state['health']}")
                
#                 # 3. 勝敗判定
#                 if opponent_state["health"] <= 0:
#                     opponent_state["state"] = "dead"
#                     # 勝敗が確定したことを全員に通知する特殊なメッセージをブロードキャスト
#                     final_msg = json.dumps({"type": "game_over", "winner": user_id, "loser": op_id, "state": state})
#                     await asyncio.gather(*[ws.send(final_msg) for ws in ACTIVE_SESSIONS[session_id]])
#                     # ★★★ ここでセッションを終了させるロジックが必要 ★★★
#                     return 

#     # 4. 全員に現在の最新状態をブロードキャスト (クライアントはこれを受け取り状態を修正)
#     broadcast_msg = json.dumps({"type": "state_update", "state": state})
#     await asyncio.gather(*[ws.send(broadcast_msg) for ws in ACTIVE_SESSIONS[session_id]])


# async def handle_game_session(websocket, path):
#     """
#     単一のクライアント接続を処理するメインコルーチン
#     """
#     # 接続直後のパス処理を絶対安全にする
#     try:
#         parsed_url = urlparse(path)
#         path_segments = parsed_url.path.split('/')
        
#         # /session/<session_id> 形式であることを確認
#         if len(path_segments) < 3 or path_segments[1] != 'session':
#             print(f"[S] Invalid path format (missing session ID): {path}")
#             await websocket.close(code=1003, reason="Invalid Path Format")
#             return 
            
#         session_id = path_segments[2]
        
#         # クエリパラメータからuser_idを取得
#         query_params = parse_qs(parsed_url.query)
#         user_id = query_params.get('user_id', ['UNKNOWN'])[0]

#         if not session_id:
#             print(f"[S] Session ID is empty for path: {path}")
#             await websocket.close(code=1003, reason="Empty Session ID")
#             return

#         # セッション管理
#         if session_id not in ACTIVE_SESSIONS:
#             ACTIVE_SESSIONS[session_id] = set()

#         # 接続を追加
#         ACTIVE_SESSIONS[session_id].add(websocket)

#         # ★★★ 修正箇所: 接続が完了したユーザーIDを保持する ★★★
#         # WebSocketオブジェクトにuser_idを紐づける（ブロードキャスト時に誰に送るか判別可能にするため）
#         websocket.user_id = user_id 

#         print(f"[S] User connected: {user_id} to session {session_id}. Current players: {len(ACTIVE_SESSIONS[session_id])}")

#         # ★★★ 修正箇所: プレイヤー数が揃ったかチェックし、初期化＆ブロードキャスト ★★★
#         # ffa_2pモードを想定して、2人揃ったら開始
#         if len(ACTIVE_SESSIONS[session_id]) == 2 and session_id not in GAME_STATES:
#             print(f"[S] Session {session_id} is FULL. Starting game.")
            
#             # 接続済みのユーザーIDリストを正確に取得
#             player_ids = [ws.user_id for ws in ACTIVE_SESSIONS[session_id]]
            
#             # 初期化
#             initialize_game_state(session_id, player_ids)
            
#             # 全員に初期状態を通知（これがグレー画面を解消する）
#             initial_state_msg = json.dumps({"type": "state_update", "state": GAME_STATES[session_id]})
#             await asyncio.gather(*[ws.send(initial_state_msg) for ws in ACTIVE_SESSIONS[session_id]])

#         # ここで全員揃うのを待つロジック（オプション）
#         # if len(ACTIVE_SESSIONS[session_id]) < 2:
#         #     # 2人揃うまで何もしない、または待機メッセージを返す
#         #     pass

#         async for message in websocket:
#             # 1. チート検証
#             if not is_valid_input(message):
#                 print(f"[S] Invalid input detected, dropping message: {message}")
#                 continue
                
#             # 2. 入力同期（ブロードキャスト）
#             # 同じセッション内の全プレイヤーにメッセージを転送
#             # 送信元を除く処理も可能だが、ここではシンプルに全員に送る
#             await asyncio.gather(*[
#                 ws.send(message)
#                 for ws in ACTIVE_SESSIONS[session_id]
#                 if ws is not websocket  # 送信元には送らない
#             ])
#         # ★★★ 接続後、現在のゲーム状態を全員に送信 ★★★
#         if session_id in GAME_STATES:
#             # ゲーム状態が既に存在する場合、現在の状態をこの新規接続ユーザーに送信
#             current_state_msg = json.dumps({"type": "state_update", "state": GAME_STATES[session_id]})
#             await websocket.send(current_state_msg)
#         else:
#             # 最初の接続ユーザーの場合、状態を初期化（ここで初期化された状態をブロードキャストすべき）
#              player_ids = [user_id] 
#              initialize_game_state(session_id, player_ids)
#              # WARNING: 最初のユーザーが接続した時点では、まだ対戦相手は接続していない可能性があります。

#         async for message in websocket:
#             input_data = json.loads(message)
            
#             if not is_valid_input(message):
#                 continue
                
#             # ★★★ 入力処理関数へ委譲 ★★★
#             await process_game_input(session_id, input_data)

#     except Exception as e:
#         # ★★★ 致命的なエラーのログ出力とクローズ ★★★
#         print(f"[S] CRITICAL ERROR in session {session_id} for user {user_id}: {e}")
#         # 例外が発生した場合も接続をクリーンに終了させる
#         await websocket.close(code=1011, reason=f"Server Internal Error: {e.__class__.__name__}")

#     finally:
#         # 接続解除処理は必ず実行
#         if session_id in ACTIVE_SESSIONS and websocket in ACTIVE_SESSIONS[session_id]:
#             ACTIVE_SESSIONS[session_id].remove(websocket)
#             print(f"[S] User disconnected: {user_id} from session {session_id}.")
            
#             # セッションに誰もいなくなったらセッション自体を削除
#             if not ACTIVE_SESSIONS[session_id]:
#                 if session_id in GAME_STATES:
#                     del GAME_STATES[session_id]
#                     print(f"[S] Game state for session {session_id} removed.")
#                 # ★★★ セッション終了時の成績更新APIを呼ぶ処理をここに入れる ★★★
#                 # send_final_scores(session_id) 
#                 del ACTIVE_SESSIONS[session_id]
#                 print(f"[S] Session {session_id} ended and removed.")

import json
import asyncio
from urllib.parse import urlparse, parse_qs
import uuid # ゲーム終了ロジックでの問題回避のため追加

# 現在アクティブなセッションを管理 (セッションID -> 接続されているクライアントのセット)
ACTIVE_SESSIONS = {}
# ゲーム状態を管理する辞書
GAME_STATES = {} 

METER_MAX = 100    # ゲージの最大値
METER_GAIN_HIT = 5 # 攻撃がヒットした時のゲージ増加量
RING_OUT_DAMAGE = 100 # ステージ外に出たときのダメージ

# キャンバスサイズ: 640x480 (client/index.htmlに基づき)
CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480
CHARACTER_HEIGHT = 80 # キャラクターの高さを定義

GRAVITY = 4.0      # 重力加速度
JUMP_VELOCITY = -20.0 # ジャンプ初速(負の値で上向き)
JUMP_COUNT_MAX = 3 # ジャンプ回数の最大値

# 浮遊ステージのパラメータ
PLATFORM_WIDTH = CANVAS_WIDTH * 2 / 3 # 約426px
PLATFORM_TOP_Y = CANVAS_HEIGHT * 2 / 3 # 160px (画面上部から2/3)

GROUND_Y = PLATFORM_TOP_Y - CHARACTER_HEIGHT # 160px - 80px = 80px # 着地するY座標を台の高さに設定
STAGE_LEFT_BOUNDARY = (CANVAS_WIDTH - PLATFORM_WIDTH) / 2 # 台の左端 (約107px)
STAGE_RIGHT_BOUNDARY = STAGE_LEFT_BOUNDARY + PLATFORM_WIDTH # 台の右端 (約533px)
RING_OUT_Y = CANVAS_HEIGHT + 50 # 画面下部を大きく超えたらリングアウト (Y座標)

def is_valid_input(message):
    """クライアントからの入力データ構造を安全に検証する"""
    try:
        data = json.loads(message)
        required_keys = ["action", "frame", "user_id"]
        if not all(key in data for key in required_keys):
            return False
        if not isinstance(data["frame"], int) or not isinstance(data["action"], str):
             return False
        return True
    except:
        return False

def initialize_game_state(session_id, player_ids):
    """セッション開始時に初期状態を作成する"""
    state = {}
    for i, p_id in enumerate(player_ids):
        state[p_id] = {
            "x": STAGE_LEFT_BOUNDARY + 50 + i * 150, # ★修正: 初期位置を台の上にする
            "y": GROUND_Y,     # 地面Y座標
            "health": 500,      
            "state": "idle",   
            "frame": 0,           
            "vy": 0.0,         # Y軸速度(垂直)
            "vx": 0.0,         # X軸速度 (水平、ノックバック用) ★初期化
            "on_ground": True, # 接地フラグ
            "meter": 0,        # 必殺技ゲージ
            "facing": "right", # キャラクターの向き
            "jumps_remaining": JUMP_COUNT_MAX, # 残りジャンプ回数
            "vx_input": 0.0, # 入力によるX速度 (ノックバックと分離)
            "attack_type": "none" # 攻撃の種類を追跡
        }
    GAME_STATES[session_id] = state
    return state

def check_hit(attacker_state, target_state, attack_type="punch"):
    """攻撃判定の簡易ロジックとダメージ計算"""
    
    # X軸での距離を計算
    distance_x = abs(attacker_state["x"] - target_state["x"])

    # 攻撃範囲と基本ダメージを技の種類に応じて設定
    if attack_type == "attack_forward":
        max_range = 70
        base_damage = 10
    elif attack_type == "attack_super": # 必殺技
        max_range = 150          # 範囲が伸びる
        base_damage = 30         # 基礎ダメージが高い
    elif attack_type == "attack_up": # 上攻撃 (Y座標も考慮すべきだが、簡易化)
        max_range = 50
        base_damage = 20
    elif attack_type == "attack_down": # 下攻撃の定義
        max_range = 30
        base_damage = 30 # ダメージを高く設定
    else: # 他の攻撃 (attack_down など)
        max_range = 5
        base_damage = 100
    
    # Y軸での距離（ジャンプ中の攻撃は簡易的に常にヒットと見なす）
    if target_state["y"] != GROUND_Y:
        pass # 簡易化のためジャンプ中でも攻撃は当たる
    
    # 攻撃範囲内の場合のみ
    if distance_x < max_range:
        # 距離が近いほどダメージが高い (距離MaxRangeで0、距離0でBaseDamage)
        damage = base_damage * (1 - (distance_x / max_range)) 
        
        # 反発処理のための速度ベクトル（ここでは攻撃者とターゲットの間のX軸速度を設定）
        knockback_speed = 20  # 反発速度
        knockback_direction = 1 if attacker_state["x"] < target_state["x"] else -1
        
        return {
            "is_hit": True, 
            "damage": max(1, int(damage)), # 最低ダメージを1とする
            "knockback_vx": knockback_speed * knockback_direction # X軸の反発速度
        }
    return {"is_hit": False, "damage": 0, "knockback_vx": 0}


async def process_game_input(session_id, input_data):
    """クライアントからの入力メッセージを処理し、状態を更新、必要ならブロードキャストする"""
    state = GAME_STATES.get(session_id)
    if not state: return

    user_id = input_data['user_id']
    action = input_data['action']
    current_player = state.get(user_id)
    if not current_player: return
    # # ★★★ 修正箇所: 物理演算の直前で、移動入力がない場合のidle状態への移行を処理 ★★★
    # if current_player["on_ground"] and current_player["vx_input"] == 0.0 and current_player["state"] == "running":
    #     current_player["state"] = "idle" # 地面についていて入力がなければアイドルに戻す

    # 攻撃中、被弾中は他のアクションを無視
    if current_player["state"] in ["attacking", "hit"]:
        if action not in ['stop_move']: # 停止入力だけは受け付ける
            pass

    # --- 状態をリセットする処理の代替 (移動と攻撃の分離) ---
    current_action_is_move = False

    # 1. 移動・ジャンプ・向きの処理
    if action == 'move_left':
        current_player["facing"] = "left"   # 向きを更新
        current_player["vx_input"] = -10.0   # 入力速度を設定
        current_player["state"] = "running" # 移動中は状態を "running" にする
        current_action_is_move = True
        # ★追加: ノックバック解除ロジック (反対方向の入力を優先) ★
        if current_player.get("vx", 0.0) > 0.0: # 現在右に飛んでいるなら
             current_player["vx"] = 0.0 # ノックバックを即座に停止
    elif action == 'move_right':
        current_player["facing"] = "right"
        current_player["vx_input"] = 10.0
        current_player["state"] = "running"
        current_action_is_move = True
        # ★追加: ノックバック解除ロジック (反対方向の入力を優先) ★
        if current_player.get("vx", 0.0) < 0.0: # 現在左に飛んでいるなら
             current_player["vx"] = 0.0 # ノックバックを即座に停止
    elif action == 'stop_move': # ★ 停止入力の処理 ★
        current_player["vx_input"] = 0.0
        if current_player.get("on_ground", False):
            current_player["state"] = "idle"
    elif action == 'jump' and current_player.get("jumps_remaining", 0) > 0: # 残りジャンプ回数をチェック
        current_player["state"] = "jumping" # ジャンプ中は状態を "jumping" に
        current_player["vy"] = JUMP_VELOCITY # 上昇速度を設定
        current_player["on_ground"] = False # 接地解除 
        current_player["jumps_remaining"] -= 1  # ジャンプ回数を消費

    # 2. 攻撃処理 
    if action in ['attack_forward', 'attack_up', 'attack_down', 'attack_super']:
        attack_type = action # 入力アクション名そのものをattack_typeとして使用
        
        # 攻撃中の入力を受け付けない
        if current_player["state"] == "attacking": return 
        
        # 必殺技のゲージチェック
        if attack_type == 'attack_super':
            if current_player["meter"] < METER_MAX:return #ゲージ不足
            current_player["meter"] = 0 

        # 攻撃開始状態の設定 (この状態がクライアントに送られ、描画が開始される)
        current_player["state"] = "attacking"
        current_player["attack_type"] = attack_type
        current_player["vx_input"] = 0.0 # 攻撃中は移動を無効化

        # --- 攻撃判定 (入力時の判定を維持) ---
        opponent_ids = [p for p in state.keys() if p != user_id]
        for op_id in opponent_ids:
            opponent_state = state[op_id]
            # check_hit が辞書を返す、攻撃タイプを渡す
            # check_hit の attack_type は 'attack_forward' などの文字列
            hit_result = check_hit(current_player, opponent_state, attack_type) 
                
            if hit_result["is_hit"]:
                # ゲージの増加
                current_player["meter"] = min(METER_MAX, current_player["meter"] + METER_GAIN_HIT)
                opponent_state["health"] -= hit_result["damage"]
                opponent_state["state"] = "hit"
                # 反発処理
                opponent_state["vx"] = hit_result["knockback_vx"] 
                
                # 勝敗判定
                if opponent_state["health"] <= 0:
                    opponent_state["state"] = "dead"
                    final_msg = json.dumps({"type": "game_over", "winner": user_id, "loser": op_id, "state": state})
                    
                    # 全員に終了メッセージをブロードキャスト
                    await asyncio.gather(*[ws.send(final_msg) for ws in ACTIVE_SESSIONS.get(session_id, set())])
                    
                        # ★★★ サーバー側でのセッション終了処理をキューに入れる ★★★
                        # ループが終了してからクリーンアップ処理を行うために、非同期タスクとして実行
                    asyncio.create_task(cleanup_session_after_game(session_id))
                    return 
                pass
        
    # ★★★ 3. 物理演算の適用（関数外に分離しても良いが、ここでは入力処理の一部として実行） ★★★
    for p_id, p_state in state.items():
        # A:重力適用
        if not p_state.get("on_ground", True): # on_groundの安全な取得
            p_state["vy"] += GRAVITY
        
        # # ノックバック速度は徐々に減衰させる (地面についていなければ)
        # if not p_state.get("on_ground", False) and abs(p_state.get("vx", 0.0)) > 0.5:
        #      p_state["vx"] *= 0.95 # 空中で徐々に減速 (5%減衰)

        # ★修正: ノックバック減衰と停止 (入力がない場合のみ減衰) ★
        # 入力があってもノックバック中は減衰させる方が自然だが、ここではバグ回避のため減衰を続行
        if abs(p_state.get("vx", 0.0)) > 0.5:
             p_state["vx"] *= 0.95 # 空中で徐々に減速 (5%減衰)
        elif abs(p_state.get("vx", 0.0)) <= 0.5:
             p_state["vx"] = 0.0 # 速度がほぼなくなったら停止
        
        # 最終X軸速度: 入力速度 + ノックバック速度
        # final_vx = p_state["vx_input"] + p_state.get("vx", 0.0) 
        # ノックバックが効いている場合、入力速度は無視される（ノックバック中は制御不能とする）
        final_vx = 0.0
        if abs(p_state.get("vx", 0.0)) > 0.0:
            # ノックバックが効いている間は、入力速度を完全に無視
            final_vx = p_state.get("vx", 0.0)
        else:
            # ノックバックが止まったら、入力速度を適用
            final_vx = p_state["vx_input"]
        
        # --- B. 位置の更新 ---
        p_state["y"] += p_state["vy"]
        p_state["x"] += final_vx # 最終X軸速度を適用

        # --- C. 着地・場外判定 ---
        is_on_platform = (
            p_state["y"] >= GROUND_Y and 
            p_state["x"] > STAGE_LEFT_BOUNDARY and 
            p_state["x"] < STAGE_RIGHT_BOUNDARY
        )
        
        # 1. 台に着地
        if is_on_platform:
            p_state["y"] = GROUND_Y
            p_state["vy"] = 0.0
            p_state["on_ground"] = True
            p_state["vx"] = 0.0 # 着地したらノックバック速度をリセット
            p_state["jumps_remaining"] = JUMP_COUNT_MAX # ジャンプ回数をリセット
            p_state["state"] = "idle" # 着地したら idle に戻す

            # 着地時に攻撃/ヒット状態をリセット (重要)
            if p_state["state"] in ["attacking", "hit"]:
                 p_state["state"] = "idle"
                 p_state["attack_type"] = "none" # 攻撃タイプをリセット
        
        # 2. 台から落ちた or 空中にいる
        elif p_state["y"] < GROUND_Y:
            p_state["on_ground"] = False
            
        # 3. 台の真下でX座標が台の範囲外に外れた
        elif p_state["y"] == GROUND_Y and (p_state["x"] <= STAGE_LEFT_BOUNDARY or p_state["x"] >= STAGE_RIGHT_BOUNDARY):
             p_state["on_ground"] = False # 強制的に空中状態へ移行し、自由落下開始

        # 4. リングアウト判定 (画面外に出たらゲームオーバー)
        is_ring_out = (p_state["y"] > RING_OUT_Y or p_state["y"] < -50 or p_state["x"] < -30 or p_state["x"] > CANVAS_WIDTH + 30)

        if is_ring_out and p_state["health"] > 0:
            p_state["health"] -= RING_OUT_DAMAGE
            print(f"[S] RING OUT: {p_id} fell off the stage. Health: {p_state['health']}")
            
            # HPが0以下になった場合の勝敗判定
            if p_state["health"] <= 0:
                p_state["state"] = "dead"
                # 相手プレイヤーを勝者として特定 (簡易化のため、生きている方を探す)
                winner_id = [p for p in state.keys() if p != p_id and state[p]["health"] > 0]
                final_msg = json.dumps({"type": "game_over", "winner": winner_id[0] if winner_id else "NONE", "loser": p_id, "state": state})
                await asyncio.gather(*[ws.send(final_msg) for ws in ACTIVE_SESSIONS.get(session_id, set())])
                asyncio.create_task(cleanup_session_after_game(session_id))
                return # 処理を中断
        
        # 5. 状態リセット（アニメーション用）
        # 地面についているかつ移動入力を受けていない かつ 攻撃中/被弾中でないなら idle
        if p_state.get("on_ground", False) and p_state["vx_input"] == 0.0 and p_state["state"] not in ["attacking", "hit"]:
             p_state["state"] = "idle"
        # 空中にいるなら jumping にする (攻撃中/被弾中は除く)
        elif not p_state.get("on_ground", False) and p_state["state"] not in ["attacking", "hit"]:
             p_state["state"] = "jumping"
        # ★★★ 修正箇所: 攻撃/ヒット状態はサーバーで状態をロックする ★★★
        # 攻撃状態に入ったフレームでは、他の状態に上書きされないようにする
        if p_state["state"] == "attacking":
            # 攻撃開始フレームで設定された attacking 状態を維持
            pass 
        elif p_state["state"] == "hit":
            # 被弾状態も維持
            pass

        # # 着地判定後の状態遷移 (ここでidleに戻す)
        # if p_state.get("on_ground", False) and p_state["state"] == "idle" and p_state["vx_input"] != 0.0:
        #     p_state["state"] = "running" # 地面で入力があるのにidleならrunningにする
            
        # if p_state.get("on_ground", False) and p_state["state"] == "running" and p_state["vx_input"] == 0.0 and p_state["attack_frame"] == 0:
        #      p_state["state"] = "idle" # 地面で、走っていて、入力がなければidleにする
             
        # if not p_state.get("on_ground", False) and p_state["state"] != "attacking" and p_state["state"] != "hit":
        #      p_state["state"] = "jumping" # 空中にいるなら jumping にする

    # 6. 全員に現在の最新状態をブロードキャスト (ゲームオーバーでない場合)
    broadcast_msg = json.dumps({"type": "state_update", "state": state})
    await asyncio.gather(*[ws.send(broadcast_msg) for ws in ACTIVE_SESSIONS.get(session_id, set())])


# 新規追加: ゲーム終了後のクリーンアップ関数
async def cleanup_session_after_game(session_id):
    """ゲームオーバー後に少し待ってからセッションを安全にクリーンアップする"""
    await asyncio.sleep(2) # 2秒待って、クライアントが終了メッセージを受け取るのを保証
    
    if session_id in ACTIVE_SESSIONS:
        # 接続をすべて強制的にクローズ
        await asyncio.gather(*[ws.close() for ws in ACTIVE_SESSIONS[session_id]])
    
    # この後の finally ブロックで ACTIVE_SESSIONS と GAME_STATES が削除されます


async def handle_game_session(websocket, path):
    user_id = "UNKNOWN"
    session_id = str(uuid.uuid4()) # とりあえず仮のID
    
    try:
        parsed_url = urlparse(path)
        path_segments = parsed_url.path.split('/')
        
        if len(path_segments) < 3 or path_segments[1] != 'session':
            await websocket.close(code=1003, reason="Invalid Path Format")
            return 
            
        session_id = path_segments[2]
        query_params = parse_qs(parsed_url.query)
        user_id = query_params.get('user_id', ['UNKNOWN'])[0]

        if not session_id:
            await websocket.close(code=1003, reason="Empty Session ID")
            return

        if session_id not in ACTIVE_SESSIONS:
            ACTIVE_SESSIONS[session_id] = set()

        # 接続を追加
        ACTIVE_SESSIONS[session_id].add(websocket)
        websocket.user_id = user_id 

        print(f"[S] User connected: {user_id} to session {session_id}. Current players: {len(ACTIVE_SESSIONS[session_id])}")

        # 1. 2人揃ったら初期化＆ブロードキャスト
        if len(ACTIVE_SESSIONS[session_id]) == 2 and session_id not in GAME_STATES:
            print(f"[S] Session {session_id} is FULL. Starting game.")
            
            player_ids = [ws.user_id for ws in ACTIVE_SESSIONS[session_id]]
            initialize_game_state(session_id, player_ids)
            
            initial_state_msg = json.dumps({"type": "state_update", "state": GAME_STATES[session_id]})
            await asyncio.gather(*[ws.send(initial_state_msg) for ws in ACTIVE_SESSIONS[session_id]])

        # 2. メッセージループ (全ての通信処理のメインループ)
        async for message in websocket:
            input_data = json.loads(message)
            
            if not is_valid_input(message):
                continue
                
            await process_game_input(session_id, input_data)


    except Exception as e:
        print(f"[S] CRITICAL ERROR in session {session_id} for user {user_id}: {e}")
        # 例外が発生した場合も接続をクリーンに終了させる
        await websocket.close(code=1011, reason=f"Server Internal Error: {e.__class__.__name__}")

    finally:
        # 接続解除処理は必ず実行
        if session_id in ACTIVE_SESSIONS:
            if websocket in ACTIVE_SESSIONS[session_id]:
                ACTIVE_SESSIONS[session_id].remove(websocket)
                print(f"[S] User disconnected: {user_id} from session {session_id}.")
            
            # セッションに誰もいなくなったらセッション自体とゲーム状態を削除
            if not ACTIVE_SESSIONS[session_id]:
                if session_id in GAME_STATES:
                    del GAME_STATES[session_id]
                    print(f"[S] Game state for session {session_id} removed.")
                
                del ACTIVE_SESSIONS[session_id]
                print(f"[S] Session {session_id} ended and removed.")