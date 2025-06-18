# 使用官方 Python 3.10 精简镜像
FROM python:3.10-slim-bullseye

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 设置时区并安装依赖（包含中文字体）
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        fonts-wqy-zenhei && \
    rm -rf /var/lib/apt/lists/*

# 安装应用依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY . .

# 开放端口
EXPOSE 5001

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# 启动命令
CMD ["uvicorn", "monitor:app", "--host", "0.0.0.0", "--port", "5001"]
