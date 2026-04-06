from flask import Flask, request, jsonify
import psycopg2 # PostgreSQLを想定
import os

app = Flask(__name__)

# DB接続設定（環境変数から読み込むことを推奨）
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "game_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "password")

def get_db_connection():
    """DB接続を返すヘルパー関数"""
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

@app.route('/scores', methods=['POST'])
def update_scores():
    """
    ゲームセッションサービスから成績更新を受け付けるAPI
    :JSON: {"mode": "ffa_4p", "match_id": "...", "results": [{"user_id": "...", "rank": 1, "score": 100}]}
    """
    data = request.json
    if not data or 'results' not in data:
        return jsonify({"message": "Invalid data"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. 各プレイヤーの成績を保存
        for result in data['results']:
            # スコアテーブルへの挿入/更新処理をここに記述
            cur.execute(
                """INSERT INTO match_results (user_id, mode, rank, score, match_id, created_at) 
                   VALUES (%s, %s, %s, %s, %s, NOW())""",
                (result['user_id'], data['mode'], result['rank'], result['score'], data['match_id'])
            )
            
            # 2. ユーザーの総合ランキングを更新するロジック（例: Eloレーティング更新など）
            # cur.execute("UPDATE users SET rank = calculate_new_rank(...) WHERE user_id = %s", (result['user_id'],))
        
        conn.commit()
        return jsonify({"success": True, "message": "Scores updated successfully"}), 200

    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500
    finally:
        if conn: conn.close()

# @app.route('/ranking', methods=['GET'])
# def get_ranking():
#     """ランキング情報を取得するAPI（S1の認証サービスが呼び出す）"""
#     # DBからトップNのプレイヤーを取得しJSONで返す
#     pass

if __name__ == '__main__':
    # S2の専用ポートで実行
    app.run(host='0.0.0.0', port=5001)