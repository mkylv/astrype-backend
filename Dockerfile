# Astrype backend — FastAPI + Kerykeion (Swiss Ephemeris).
# Render'daki ortamla aynı Python sürümü (3.12).
FROM python:3.12-slim AS build
# pyswisseph C uzantısı derlenirken gcc gerekir; son imaja taşınmaz.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 astrype
COPY --from=build /install /usr/local
WORKDIR /app
COPY app ./app
USER astrype
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"
# Tek işlem: natal/günlük yorum üretimini tekilleştiren görev kayıtları işlem
# belleğinde tutuluyor (routes_chart._INTERP_TASKS, routes_daily._TASKS).
# Birden çok worker'a geçmeden önce bu kayıtlar ortak bir yere taşınmalı.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
