FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y python3-pip libgdal-dev gdal-bin && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip3 install --no-cache-dir torch==2.2.1 torchvision==0.17.1 --index-url https://download.pytorch.org/whl/cu121
RUN pip3 install --no-cache-dir fastapi uvicorn transformers rasterio google-cloud-storage

COPY server.py /app/server.py

# Vertex AI utilise la variable AIP_HTTP_PORT (généralement 8080)
ENV PORT=8080
EXPOSE $PORT

CMD ["sh", "-c", "python3 -m uvicorn server:app --host 0.0.0.0 --port $PORT"]