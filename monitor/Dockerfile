FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir fastapi uvicorn requests openai python-dotenv aiohttp

CMD ["uvicorn", "monitor:app", "--host", "0.0.0.0", "--port", "5001", "--reload"]
