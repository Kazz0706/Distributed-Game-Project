from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# データベース設定
# Docker Composeから環境変数でDB接続情報を取得
db_user = os.getenv('POSTGRES_USER', 'approval_user')
db_password = os.getenv('POSTGRES_PASSWORD', 'approval_password')
db_name = os.getenv('POSTGRES_DB', 'approval_db')
db_host = os.getenv('POSTGRES_HOST', 'approval_db') # Docker Compose内のサービス名
db_port = os.getenv('POSTGRES_PORT', '5432')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key') # セッション管理用シークレットキー

db = SQLAlchemy(app)

# ユーザーモデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, approved, rejected

    def __repr__(self):
        return f'<User {self.username}>'

# 管理者認証情報 (仮)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'yoshida')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'check_users')

# データベースの初期化
@app.before_request
def create_tables():
    db.create_all()

# ユーザー申請エンドポイント
@app.route('/apply', methods=['POST'])
def apply_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')

    if not username or not email:
        return jsonify({"message": "Username and email are required"}), 400

    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({"message": "User with this username or email already exists or applied"}), 409

    new_user = User(username=username, email=email, status='pending')
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Application submitted successfully", "status": "pending"}), 201

# ユーザーの状態確認エンドポイント (ゲームサービスが利用)
@app.route('/check_status/<username>', methods=['GET'])
def check_user_status(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify({"username": user.username, "status": user.status}), 200

# 管理者ログインページ
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

# 管理者ダッシュボード
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    pending_users = User.query.filter_by(status='pending').all()
    approved_users = User.query.filter_by(status='approved').all()
    rejected_users = User.query.filter_by(status='rejected').all()
    return render_template('admin.html',
                           pending_users=pending_users,
                           approved_users=approved_users,
                           rejected_users=rejected_users)

# ユーザー承認エンドポイント
@app.route('/admin/approve/<int:user_id>', methods=['POST'])
def admin_approve_user(user_id):
    if not session.get('logged_in'):
        return jsonify({"message": "Unauthorized"}), 401
    user = User.query.get(user_id)
    if user:
        user.status = 'approved'
        db.session.commit()
        return jsonify({"message": f"User {user.username} approved"}), 200
    return jsonify({"message": "User not found"}), 404

# ユーザー拒否エンドポイント
@app.route('/admin/reject/<int:user_id>', methods=['POST'])
def admin_reject_user(user_id):
    if not session.get('logged_in'):
        return jsonify({"message": "Unauthorized"}), 401
    user = User.query.get(user_id)
    if user:
        # 拒否されたユーザーはデータベースから削除
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"User {user.username} rejected and deleted"}), 200
    return jsonify({"message": "User not found"}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # アプリ起動時にテーブルを作成
    app.run(host='0.0.0.0', port=5000, debug=True)