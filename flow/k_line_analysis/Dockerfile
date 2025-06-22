FROM python:3.10-slim

WORKDIR /app

# 切换为国内源并安装基础工具
RUN sed -i 's@http://deb.debian.org/debian@https://mirrors.ustc.edu.cn/debian@g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        build-essential \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY . .

# 确保temp目录存在
RUN mkdir -p ./temp

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py", "--mode", "api"]
