FROM python:3.11-slim

# 1. Рабочая директория
WORKDIR /app

# 2. Копируем код
COPY . /app

# 3. Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# 4. Устанавливаем supervisor
RUN apt-get update && apt-get install -y supervisor && \
    mkdir -p /var/log/supervisor

# 5. Копируем конфиг supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 6. (опционально) создаём папку для данных (будет volume)
RUN mkdir -p /app/data

# 7. Открываем нужные порты (например, 8080 для Flask)
EXPOSE 8080

# 8. Запускаем supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]