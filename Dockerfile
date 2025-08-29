# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 先只複製 requirements.txt，讓快取命中
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再複製程式碼
COPY . .

# 用 gunicorn 跑 Flask；Cloud Run 會注入 $PORT
CMD exec gunicorn --bind :${PORT:-8080} --workers 2 --threads 4 --timeout 60 app:app
