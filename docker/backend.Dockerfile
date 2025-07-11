# 后端服务 Dockerfile - API 代理服务（无需GPU）
FROM python:3.10-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 安装系统依赖（包含图像处理库）
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    python3-dev \
    libmagic1 \
    libmagic-dev \
    libopencv-dev \
    libopencv-core-dev \
    libopencv-imgcodecs-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libatlas-base-dev \
    libblas-dev \
    liblapack-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip install --upgrade pip

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY requirements.txt .
COPY packages.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY stablediffusion-infinity/ ./stablediffusion-infinity/
COPY run.py .

# 创建必要的目录
RUN mkdir -p /app/static \
    && mkdir -p /app/stablediffusion-infinity/local_storage/gallery \
    && mkdir -p /app/stablediffusion-infinity/local_storage/uploads \
    && mkdir -p /app/stablediffusion-infinity/local_storage/timelapse

# 设置数据库（先清理再创建）
RUN if [ -f "schema.sql" ]; then \
        rm -f rooms.db && \
        python -c "import sqlite3; db = sqlite3.connect('rooms.db'); db.executescript(open('schema.sql').read()); db.commit(); db.close(); print('数据库初始化完成')"; \
    fi

# 暴露端口
EXPOSE 7860

# 设置启动命令
WORKDIR /app
CMD ["python", "stablediffusion-infinity/app.py"] 