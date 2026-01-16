# Dockerfile.lite - version sans QGIS pourenvironnements avec réseau restreint
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Installation des dépendances minimales (sans PPA externe)
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

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copie du code uniquement (les modèles seront montés en volume)
COPY ./app /app/app
# Le répertoire models sera monté via 'docker run -v ...'
RUN mkdir -p /app/models /app/data

EXPOSE 8000

# Lancement direct (puisqu'il n'y a pas de QGIS, pas besoin de Xvfb)
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
