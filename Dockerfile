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

# Inicializar DB si no existe
RUN python -c "from backend.db.init_db import init_db; init_db()"

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
