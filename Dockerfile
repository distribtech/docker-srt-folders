FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SUBTITLE_BASE_DIR=./data

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3 python3-pip build-essential pkg-config python3-dev \
       ffmpeg \
       libavcodec-dev libavformat-dev libavutil-dev \
       libswresample-dev libswscale-dev libavdevice-dev libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python3 -m pip install --upgrade pip setuptools wheel \
    && python3 -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app.web:create_app()", "--bind", "0.0.0.0:8000", "--workers", "2"]
