FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Skopje

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    default-jre-headless \
    tzdata \
    ghostscript \
    libglib2.0-0 \
    libgl1 \
    ca-certificates \
    && ln -snf /usr/share/zoneinfo/Europe/Skopje /etc/localtime \
    && echo Europe/Skopje > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
