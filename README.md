# Stock Investment Agent

This project provides a set of Docker services for running the stock investment
analysis demo locally.

## Running locally

Use `docker-compose` to build and start all services:

```bash
docker-compose up --build
```

The following services will be available:

- **app** – main Gradio interface on [http://localhost:7860](http://localhost:7860)
- **monitor** – API backend on [http://localhost:5001](http://localhost:5001)
- **kline** – K-line analysis service on [http://localhost:10000](http://localhost:10000)

The previous Render deployment is no longer required; the `kline` container is
built from `flow/k_line_analysis/` and exposed on port `10000`.
