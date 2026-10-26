FROM python:3.12-slim

WORKDIR /app
COPY backend_files/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY backend_files/app.py backend_files/superkart_model.joblib ./

EXPOSE 7860
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "60", "app:app"]
