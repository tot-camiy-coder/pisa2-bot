FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY backend/ ./backend/
COPY services/ ./services/
COPY dist/ ./dist/
COPY media/ ./media/

RUN mkdir -p media/chat media/chat_attachments media/photos media/profileb media/defaults media/public

EXPOSE 8000/tcp


CMD ["python", "-u", "main.py"]
