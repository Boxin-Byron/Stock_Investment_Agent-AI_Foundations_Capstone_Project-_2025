FROM python:3.10-slim
WORKDIR /app

# 删除官方 debian.sources，避免官方源被读取
RUN rm -f /etc/apt/sources.list.d/debian.sources

# 新建 sources.list 覆盖官方源为清华源
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware\n\
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware\n\
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib non-free non-free-firmware\n\
deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" > /etc/apt/sources.list

# 安装网络工具
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    iputils-ping \
    dnsutils \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir -r requirements.txt

COPY . .
# 创建持久化数据目录
RUN mkdir -p /data && chmod 777 /data

# 禁用 Python 缓冲
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
CMD ["uvicorn", "monitor:app", "--host", "0.0.0.0", "--port", "5001", "--reload"]
