import hashlib

# 簡易的なユーザーデータストア (本番ではS2のデータサービス経由でDBに接続)
USERS_DB = {
    "user_a": {"password_hash": hashlib.sha256("pass_a".encode()).hexdigest(), "rank": 1500},
    "user_b": {"password_hash": hashlib.sha256("pass_b".encode()).hexdigest(), "rank": 1200},
}

class UserManager:
    """ユーザーの認証、登録、情報取得を扱う"""

    @staticmethod
    def authenticate_user(username, password):
        """
        ユーザー名とパスワードを検証する
        :return: user_id (str) or None
        """
        if username not in USERS_DB:
            return None # ユーザーが見つからない
        
        stored_hash = USERS_DB[username]["password_hash"]
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if stored_hash == input_hash:
            return username # 認証成功
        
        return None # パスワード不一致

    @staticmethod
    def get_user_rank(user_id):
        """
        ユーザーのランク情報を取得する (S2のデータサービスから取得する想定)
        """
        return USERS_DB.get(user_id, {}).get("rank", 1000)

    @staticmethod
    def register_user(username, password):
        """
        ユーザーを登録する (簡易実装)
        :return: True (登録成功) or False (既に存在)
        """
        if username in USERS_DB:
            return False # 既にユーザーが存在
        
        # 簡易的なパスワードハッシュ
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        USERS_DB[username] = {"password_hash": password_hash, "rank": 1000}
        return True