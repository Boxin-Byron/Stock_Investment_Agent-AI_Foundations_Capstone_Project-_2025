FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir gradio pandas matplotlib requests python-dotenv

CMD ["python", "app.py"]
