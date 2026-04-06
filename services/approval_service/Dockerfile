# Pythonの公式イメージを使用
FROM python:3.9-slim-bullseye
# FROM python:3.9-slim-bookworm # Debian 12がベース(より最新)

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .

# psycopg2をインストールするために必要なシステムライブラリをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    # その他の必要なライブラリがあればここに追加
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# GunicornでFlaskアプリケーションを起動
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]