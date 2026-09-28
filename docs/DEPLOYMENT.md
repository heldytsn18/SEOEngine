# BorneoFlash SEO Engine — Deployment Guide

> **Version:** 2.0.0
> **Terakhir diperbarui:** September 2026

---

## Daftar Isi

1. [Prasyarat](#prasyarat)
2. [Deployment Development (Lokal)](#deployment-development-lokal)
3. [Deployment Production (VPS)](#deployment-production-vps)
4. [Systemd Service](#systemd-service)
5. [Reverse Proxy — Nginx](#reverse-proxy--nginx)
6. [Reverse Proxy — Caddy](#reverse-proxy--caddy)
7. [Docker (Opsional)](#docker-opsional)
8. [Environment Variables](#environment-variables)
9. [Health Check & Monitoring](#health-check--monitoring)
10. [Troubleshooting Deployment](#troubleshooting-deployment)

---

## Prasyarat

| Komponen | Minimum | Rekomendasi |
|---|---|---|
| OS | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04 LTS |
| Python | 3.10 | 3.10+ |
| RAM | 512 MB | 1 GB+ |
| Disk | 200 MB | 500 MB+ |
| Port | 8000 (default) | Di balik reverse proxy |

---

## Deployment Development (Lokal)

```bash
# Buat virtual environment
py -3.10 -m venv .venv

# Aktifkan (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Aktifkan (Linux/macOS)
source .venv/bin/activate

# Install dependensi
pip install -r requirements.txt

# Konfigurasi
cp .env.example .env
# Edit .env → isi NINEROUTER_API_KEY

# Jalankan (auto-reload aktif)
python main.py
```

Server: `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`

---

## Deployment Production (VPS)

### 1. Setup Server

```bash
# Update sistem
sudo apt update && sudo apt upgrade -y

# Install Python dan dependensi sistem
sudo apt install -y python3.10 python3.10-venv python3-pip git

# Buat direktori aplikasi
sudo mkdir -p /opt/SEOEngine
sudo chown $USER:$USER /opt/SEOEngine
```

### 2. Deploy Kode

```bash
# Clone repository
cd /opt
git clone <repository-url> SEOEngine
cd SEOEngine

# Buat virtual environment
python3.10 -m venv .venv
source .venv/bin/activate

# Install dependensi
pip install -r requirements.txt
```

### 3. Konfigurasi Environment

```bash
cp .env.example .env
nano .env
```

Isi variabel:
```
NINEROUTER_URL=https://api.ninerouter.com/v1/chat/completions
NINEROUTER_API_KEY=sk-your-api-key-here
```

### 4. Test Manual

```bash
source .venv/bin/activate
gunicorn app.main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Di terminal lain:
curl http://localhost:8000/health
```

### 5. Hitung Jumlah Worker

Formula: `workers = (2 × CPU_CORES) + 1`

| CPU Cores | Workers |
|---|---|
| 1 | 3 |
| 2 | 5 |
| 4 | 9 |

```bash
# Cek jumlah core
nproc

# Jalankan dengan worker optimal
gunicorn app.main:app -w $(( 2 * $(nproc) + 1 )) -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Systemd Service

Buat file `/etc/systemd/system/seoengine.service`:

```ini
[Unit]
Description=BorneoFlash SEO Engine Microservice
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/SEOEngine
Environment="PATH=/opt/SEOEngine/.venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/opt/SEOEngine/.venv/bin/gunicorn app.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/seoengine/access.log \
    --error-logfile /var/log/seoengine/error.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Aktifkan Service

```bash
# Buat direktori log
sudo mkdir -p /var/log/seoengine
sudo chown www-data:www-data /var/log/seoengine

# Set ownership
sudo chown -R www-data:www-data /opt/SEOEngine

# Reload dan aktifkan
sudo systemctl daemon-reload
sudo systemctl enable seoengine
sudo systemctl start seoengine

# Cek status
sudo systemctl status seoengine

# Lihat log
sudo journalctl -u seoengine -f
```

### Perintah Berguna

```bash
sudo systemctl restart seoengine     # Restart service
sudo systemctl stop seoengine        # Stop service
sudo systemctl status seoengine      # Cek status
sudo journalctl -u seoengine -n 50   # 50 baris log terakhir
```

---

## Reverse Proxy — Nginx

### Install Nginx

```bash
sudo apt install -y nginx
```

### Konfigurasi Site

Buat file `/etc/nginx/sites-available/seoengine`:

```nginx
server {
    listen 80;
    server_name seo-engine.example.com;

    # Redirect HTTP ke HTTPS (setelah SSL diatur)
    # return 301 https://$host$request_uri;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout untuk request ke 9Router AI (bisa lama)
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }

    # Rate limiting (opsional)
    # limit_req zone=seoengine burst=20 nodelay;
}
```

### Aktifkan Site

```bash
sudo ln -s /etc/nginx/sites-available/seoengine /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL dengan Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d seo-engine.example.com
```

---

## Reverse Proxy — Caddy

Alternatif lebih sederhana dari Nginx dengan auto-HTTPS.

### Caddyfile

```
seo-engine.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

---

## Docker (Opsional)

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Build & Run

```bash
docker build -t seoengine .
docker run -d -p 8000:8000 --env-file .env --name seoengine seoengine
```

---

## Environment Variables

| Variabel | Deskripsi | Wajib | Default |
|---|---|---|---|
| `NINEROUTER_URL` | Endpoint API 9Router | ❌ | `https://api.ninerouter.com/v1/chat/completions` |
| `NINEROUTER_API_KEY` | API key 9Router | ❌ (tapi wajib untuk fitur AI) | — |

> **Catatan keamanan:** Jangan commit `.env` ke repository. File sudah termasuk di `.gitignore`.

---

## Health Check & Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8000/health
# Response: {"status":"ok","components":{"pysastrawi":"ready","fastapi":"ready","newspaper4k":"ready"}}
```

### Monitoring dengan Cron

Tambahkan ke crontab untuk monitoring sederhana:

```bash
# Cek setiap 5 menit, restart jika down
*/5 * * * * curl -sf http://localhost:8000/health || sudo systemctl restart seoengine
```

### Log Rotation

Buat file `/etc/logrotate.d/seoengine`:

```
/var/log/seoengine/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 640 www-data www-data
    postrotate
        systemctl reload seoengine > /dev/null 2>&1 || true
    endscript
}
```

---

## Troubleshooting Deployment

| Gejala | Penyebab | Solusi |
|---|---|---|
| `502 Bad Gateway` (Nginx) | Gunicorn belum jalan / port salah | `sudo systemctl status seoengine`, pastikan bind port sesuai |
| `Permission denied` | Ownership file salah | `sudo chown -R www-data:www-data /opt/SEOEngine` |
| `ModuleNotFoundError` | Virtual env tidak terdeteksi | Pastikan `PATH` di systemd service mengarah ke `.venv/bin` |
| Service gagal start | `.env` tidak terbaca | Pastikan `WorkingDirectory` benar di systemd unit |
| 9Router timeout | Network / firewall blocking | Pastikan port 443 outbound terbuka, cek `NINEROUTER_URL` |
| Response lambat | Worker terlalu sedikit | Tambah `-w` sesuai formula `2 × CPU + 1` |
