# Dockerfile - GeoCongo AI Cloud Run GPU ready, Pure Python GIS
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Installation des dépendances minimales
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ARG DEVICE=cpu
WORKDIR /app

# Installation de PyTorch
RUN if [ "$DEVICE" = "gpu" ] ; then \
    pip3 install --no-cache-dir torch==2.2.1 torchvision==0.17.1 --index-url https://download.pytorch.org/whl/cu121 ; \
    else \
    pip3 install --no-cache-dir torch==2.2.1 torchvision==0.17.1 --index-url https://download.pytorch.org/whl/cpu ; \
    fi

# Requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Code de l'application
COPY ./app /app/app

# Dossiers pour modèles et données montés en volume
RUN mkdir -p /app/models /app/data

# Expose port for Cloud Run (dynamic)
EXPOSE 8080

# Start FastAPI with dynamic port from Cloud Run
CMD ["sh", "-c", "python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
