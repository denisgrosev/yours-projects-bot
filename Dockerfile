FROM python:3.11-slim

# 1. Рабочая директория
WORKDIR /app

# 2. Устанавливаем зависимости: LibreOffice, Supervisor, и создаём нужные папки
RUN apt-get update && \
    apt-get install -y libreoffice supervisor && \
    mkdir -p /var/log/supervisor /app/data && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Копируем requirements.txt и устанавливаем python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем весь остальной код
COPY . .

# 5. Копируем конфиг supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 6. Открываем порт (пример: 8080 для Flask, меняй если нужен другой)
EXPOSE 8080

# 7. Запуск supervisor (он запустит и бота, и вебхук)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
