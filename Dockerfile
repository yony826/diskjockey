FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
# chromaprint 用于音频指纹识别
# ffmpeg 用于支持更多音频格式（包括 WMA）的解码
RUN apt-get update && apt-get install -y \
    libchromaprint-dev \
    fpcalc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY diskjockey_nas.py .

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 验证 fpcalc 安装
RUN fpcalc --version || echo "警告: fpcalc 未正确安装"

# 运行脚本
CMD ["python", "diskjockey_nas.py"]

