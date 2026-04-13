FROM python:3.12-slim

WORKDIR /app

# Deps del sistema (BeautifulSoup / lxml)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

EXPOSE 8000

CMD ["bash", "startup.sh"]
