FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY handlers/ ./handlers/
COPY utils/ ./utils/
COPY database/ ./database/
COPY media/ ./media/

EXPOSE 8000/tcp


CMD ["python", "-u", "main.py"]
