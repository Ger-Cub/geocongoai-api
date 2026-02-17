# Dockerfile - GeoCongo AI Cloud Run GPU ready, Pure Python GIS
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Installation des dépendances minimales
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ARG DEVICE=cpu
WORKDIR /app

# Requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

# Code de l'application
COPY ./app /app/app

# Dossiers pour modèles et données montés en volume
RUN mkdir -p /app/models /app/data

# Expose port for Cloud Run (dynamic)
EXPOSE 8080

# Start FastAPI with dynamic port from Cloud Run
CMD ["sh", "-c", "python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
