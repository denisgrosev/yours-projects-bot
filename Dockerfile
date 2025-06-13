FROM python:3.12.4-slim

RUN apt-get update && apt-get install -y libreoffice

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# По умолчанию пусть запускает bot.py (или поменяй на yookassa_webhook.py)
CMD ["python", "bot.py"]
