FROM python:2.7-slim

# Debian buster (base for python:2.7-slim) is EOL and has moved to archive.debian.org
RUN sed -i \
        -e 's|deb.debian.org/debian |archive.debian.org/debian |g' \
        -e 's|security.debian.org/debian-security |archive.debian.org/debian-security |g' \
        -e '/buster-updates/d' \
        /etc/apt/sources.list \
    && echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until \
    && apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
