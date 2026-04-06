# from flask import Flask, request, jsonify
# from matcher import start_matchmaking
# from user_manager import UserManager
# from flask_cors import CORS # 開発中のCORS対応のため追加
# # from user_manager import authenticate_user # 認証処理を想定

# app = Flask(__name__)
# CORS(app) # 開発環境でクライアントとサーバーが異なるポートで動く場合に必要

# @app.route('/', methods=['GET'])
# def index():
#     """ルートパスへのアクセス確認用エンドポイント"""
#     # 実際にはクライアントコードの配信は行わないが、疎通確認のためメッセージを返す
#     return jsonify({"service_status": "Auth and Match Service is Running", "version": "1.0"}), 200

# # 仮のログインAPI
# @app.route('/login', methods=['POST'])
# def login():
#     username = request.json.get('username')
#     password = request.json.get('password')
    
#     user_id = UserManager.authenticate_user(username, password)
    
#     if user_id:
#         # 認証成功。実際にはここでセッショントークンやJWTを発行
#         return jsonify({"success": True, "user_id": user_id}), 200
#     return jsonify({"success": False, "message": "Invalid username or password"}), 401

# # マッチング開始API
# @app.route('/match', methods=['POST'])
# def match():
#     # ユーザーIDと選択されたモードをクライアントから受け取る
#     user_id = request.json.get('user_id') 
#     mode = request.json.get('mode') # 例: "1v1", "2v2", "cpu"
    
#     if not user_id or not mode:
#         return jsonify({"message": "user_id and mode are required"}), 400
    
#     # 実際にはここでユーザーの認証トークンを検証
#     # if not is_valid_session(user_id, request.headers.get('Authorization')):
#     #     return jsonify({"message": "Session expired"}), 401
    
#     match_result = start_matchmaking(user_id, mode)
    
#     return jsonify(match_result), 200

# if __name__ == '__main__':
#     # 起動前にマッチング状態をクリア
#     from matcher import reset_matcher_state
#     reset_matcher_state()
#     # 開発環境のため簡易的に実行　# GunicornやuWSGIを利用する予定
#     # 本番ではS1のIPで、HTTPSを有効にして実行
#     app.run(host='0.0.0.0', port=5000)




from flask import Flask, request, jsonify
from user_manager import UserManager
from matcher import Matcher
import requests # requestsライブラリを追加
import os

app = Flask(__name__)
user_manager = UserManager()
matcher = Matcher()


# approval_service のURL
# 環境変数から取得するか、直接指定。
# S1のauth_match_serviceからはS2のNginxを通してアクセスするので、ホストのIPと公開ポートを指定する。
# S1のauth_match_serviceのdocker-compose.ymlで環境変数として設定しているはずなので、
# ここではそれを読み込む形が望ましい。
APPROVAL_SERVICE_URL = os.environ.get("APPROVAL_SERVICE_URL", "http://192.168.200.103:5001/approval")
# もし環境変数を使っていない場合は、以下のように直接指定
# APPROVAL_SERVICE_URL = "http://192.168.200.103:5001/approval"

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email') # 申請のためにemailも取得

    if not username or not password or not email:
        return jsonify({"message": "Username, password, and email are required"}), 400

    # まずapproval_serviceに申請を出す
    try:
        response = requests.post(f"{APPROVAL_SERVICE_URL}/apply", json={"username": username, "email": email})
        response_data = response.json()
        if response.status_code == 201: # 申請成功
            # 認証サービス独自のユーザー登録（パスワード管理）は別途行うか、
            # approval_serviceに統合することも検討する
            # 現状は一旦、申請成功したら仮登録とする
            if user_manager.register_user(username, password):
                return jsonify({"message": "User application submitted and account created. Awaiting approval."}), 201
            else:
                # approval_serviceには申請できたが、auth_match_serviceで登録失敗した場合
                return jsonify({"message": "Application submitted, but failed to create auth account (username taken?)"}), 409
        elif response.status_code == 409: # 既に申請済みまたは登録済み
            return jsonify({"message": response_data.get("message", "User already applied or exists")}), 409
        else:
            return jsonify({"message": "Failed to submit application to approval service", "details": response_data}), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"message": "Could not connect to approval service"}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if user_manager.authenticate_user(username, password):
        # 認証成功後、approval_serviceでユーザーのステータスを確認
        try:
            response = requests.get(f"{APPROVAL_SERVICE_URL}/check_status/{username}")
            response_data = response.json()
            if response.status_code == 200:
                user_status = response_data.get('status')
                if user_status == 'approved':
                    return jsonify({"message": "Login successful", "token": "dummy_token"}), 200
                elif user_status == 'pending':
                    return jsonify({"message": "Your account is pending approval. Please wait for an administrator to approve it."}), 403
                elif user_status == 'rejected':
                    return jsonify({"message": "Your account has been rejected. Please contact support."}), 403
                else: # Unknown status
                    return jsonify({"message": "User status is unknown. Please contact support."}), 403
            else:
                return jsonify({"message": "Could not retrieve user status from approval service", "details": response_data}), 500
        except requests.exceptions.ConnectionError:
            return jsonify({"message": "Could not connect to approval service"}), 500
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/match', methods=['POST'])
def match():
    data = request.get_json()
    user_id = data.get('user_id')
    mode = data.get('mode') # モードも必要

    if not user_id or not mode:
        return jsonify({"message": "user_id and mode are required"}), 400

    match_result = matcher.start_matchmaking(user_id, mode) # <-- ここを修正

    if match_result["status"] == "matched":
        return jsonify(match_result), 200
    elif match_result["status"] == "waiting":
        return jsonify(match_result), 202
    else: # "error" の場合
        return jsonify(match_result), 400

# /game_session_info のルートは、matcher.py に現在それに該当するメソッドがないため、
# 現状では機能しません。もしセッション情報を取得したい場合は、
# matcher.pyにget_session_infoなどのメソッドを追加する必要があります。
# または、このルート自体がゲームセッションサービスに移動すべきかもしれません。
# 一旦、このルートはコメントアウトするか、エラーを返すようにします。

# @app.route('/game_session_info/<session_id>', methods=['GET'])
# def game_session_info(session_id):
#     # ゲームセッション情報の取得 (既存のまま)
#     info = matcher.get_session_info(session_id)
#     if info:
#         return jsonify(info), 200
#     return jsonify({"message": "Session not found"}), 404
#     # 現在のMatcherクラスには、汎用的なget_session_infoメソッドがありません。
#     # もし必要であれば、Matcherクラスにセッション管理ロジックを追加する必要があります。
#     return jsonify({"message": "This endpoint is not yet implemented or moved to game session service"}), 501


if __name__ == '__main__':
    # 起動前にマッチング状態をクリア (Matcherクラスのメソッドを呼び出す)
    matcher.reset_matcher_state() # <-- ここを修正
    app.run(host='0.0.0.0', port=5000)