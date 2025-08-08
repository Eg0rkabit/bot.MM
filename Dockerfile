FROM python:3.11-slim

WORKDIR /app

COPY BotMM/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY BotMM/ .

CMD ["python", "main.py"]
