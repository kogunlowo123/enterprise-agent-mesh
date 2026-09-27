FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system -e ".[dev]"

COPY src/ src/

ENV PYTHONPATH=/app/src
ENV PORT=8001

EXPOSE 8001

CMD ["uvicorn", "agent_runtime.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
