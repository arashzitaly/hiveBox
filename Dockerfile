FROM python:3.12-slim
WORKDIR /app
COPY src/app.py .
CMD ["python", "app.py"]
