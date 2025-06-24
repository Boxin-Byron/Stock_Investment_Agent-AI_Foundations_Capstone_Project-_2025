# app/Dockerfile

FROM python:3.10-slim

WORKDIR /app
ENV TZ=Asia/Shanghai

# 安装系统依赖和中文字体
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    fonts-noto-cjk \
    libgl1-mesa-glx \
    libxrender1 \
    unzip \
    gcc \
    g++ \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 创建中文字体目录
RUN mkdir -p /usr/share/fonts/custom

# 复制本地字体到容器中
COPY ./fonts /usr/share/fonts/custom/

# 设置权限并更新字体缓存
RUN chmod -R 755 /usr/share/fonts/custom && \
    fc-cache -fv

# 提前设置matplotlib会使用的目录
RUN mkdir -p /usr/share/fonts/chinese && \
    mkdir -p ~/.cache/matplotlib
    
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860


# 禁用缓冲以提高日志实时性
ENV PYTHONUNBUFFERED=1
CMD ["python", "app.py"]
