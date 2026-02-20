# Python 3.11 をベースにする
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /code

# ライブラリのインストール
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# コード類をコンテナにコピー
COPY ./app /code/app

# サーバー起動コマンド
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]