FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv

RUN uv sync --frozen

COPY . .

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "10000"]