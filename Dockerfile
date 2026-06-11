FROM python:3.11-slim

WORKDIR /app

COPY mcp_server.py .

RUN pip install --no-cache-dir fastapi uvicorn requests pydantic

EXPOSE 8000

CMD ["python", "mcp_server.py"]
