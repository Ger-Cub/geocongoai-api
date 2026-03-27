FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y python3-pip libgdal-dev gdal-bin && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip3 install --no-cache-dir torch==2.4.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu124
RUN pip3 install --no-cache-dir fastapi uvicorn rasterio google-cloud-storage transformers ultralytics "numpy<2.0" safetensors

COPY server.py /app/server.py

# AIP_HEALTH_ROUTE, AIP_PREDICT_ROUTE, AIP_STORAGE_URI, MODEL_TYPE will be provided by Vertex AI.
# PORT is set by default by Vertex AI to 8080.
ENV PORT=8080
EXPOSE $PORT

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
