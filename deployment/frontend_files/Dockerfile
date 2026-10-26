FROM python:3.12-slim

WORKDIR /app
COPY frontend_files/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY frontend_files/app.py .

EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
