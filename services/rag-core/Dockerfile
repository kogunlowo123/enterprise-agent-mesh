FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system -e ".[dev]"

COPY src/ src/

ENV PYTHONPATH=/app/src
ENV PORT=8002

EXPOSE 8002

CMD ["uvicorn", "rag_core.main:app", "--host", "0.0.0.0", "--port", "8002"]
