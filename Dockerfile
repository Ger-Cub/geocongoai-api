FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Installation des dépendances système (GDAL, OpenCV, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    gdal-bin \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /workspace

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Patch terratorch for SENTINEL2_ALL_SOFTCON bug
RUN sed -i "s/ResNet50_Weights.SENTINEL2_ALL_SOFTCON/ResNet50_Weights.SENTINEL2_ALL_MOCO/g" \
    $(python3 -c "import terratorch; import os; print(os.path.join(os.path.dirname(terratorch.__file__), 'models/backbones/torchgeo_resnet.py'))")

# Copie du code
COPY . .

ENV PORT=8080
EXPOSE 8080

# Utilisation de uvicorn avec l'application GeoCongo
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "3600"]