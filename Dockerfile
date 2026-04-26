FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

RUN useradd --no-create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

ENV HOST=0.0.0.0

CMD ["python", "-m", "src.app"]
