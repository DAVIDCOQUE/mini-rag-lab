FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FASTEMBED_CACHE_PATH=/opt/models/fastembed \
    EASYOCR_MODULE_PATH=/opt/models/easyocr

WORKDIR /app

# Torch CPU explicito y antes que el resto: easyocr lo arrastra, y desde PyPI vendria
# la build con CUDA (~2,5 GB) que en este laboratorio no se usa.
RUN pip install --index-url https://download.pytorch.org/whl/cpu \
    torch==2.14.0 torchvision==0.29.0

COPY requirements.txt .
RUN pip install -r requirements.txt

# Modelos dentro de la imagen. Si no, el primer arranque se va en descargas (~400 MB)
# y /health no responde hasta que terminan, que es lo que tumba el healthcheck.
RUN python -c "from fastembed.rerank.cross_encoder import TextCrossEncoder; TextCrossEncoder(model_name='jinaai/jina-reranker-v2-base-multilingual')" \
 && python -c "import easyocr; easyocr.Reader(['es', 'en'], gpu=False)"

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY evaluation ./evaluation
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
