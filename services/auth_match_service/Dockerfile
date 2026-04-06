FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]

# 環境変数 FLASK_APP=app.py が必要だが、docker-composeで設定可