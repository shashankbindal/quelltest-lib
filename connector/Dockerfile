# Build from repo root: docker build -f connector/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

COPY connector/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy connector as a package so imports like `from connector.X` resolve
COPY connector/ ./connector/

ENV ENVIRONMENT=production
ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "connector.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
