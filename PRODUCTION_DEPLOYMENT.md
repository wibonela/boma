# BOMA Production Deployment Guide

**Server IP**: 46.62.233.209
**Domain**: getboma.org
**API Subdomain**: api.getboma.org
**Status**: ✅ VPS Deployed and Ready

---

## Infrastructure Overview

### Production Stack
- **Server**: VPS at 46.62.233.209
- **Domain**: getboma.org (main website)
- **API**: api.getboma.org (backend API)
- **Database**: PostgreSQL 16 (local, via Docker)
- **File Storage**: Local filesystem + Nginx
- **Reverse Proxy**: Nginx
- **SSL/TLS**: Let's Encrypt (certbot)
- **Payments**: AzamPay (Tanzania mobile money)

### Architecture
```
Internet
   ↓
Nginx (Port 80/443)
   ↓
FastAPI (Port 8000) → PostgreSQL (Docker)
   ↓                    ↓
Local File Storage    boma_db
```

---

## DNS Configuration

Configure these DNS records at your domain registrar:

```
Type    Name    Value               TTL
A       @       46.62.233.209       3600
A       api     46.62.233.209       3600
CNAME   www     getboma.org         3600
```

**Verification**:
```bash
# Check DNS propagation
dig getboma.org
dig api.getboma.org

# Should return: 46.62.233.209
```

---

## Server Setup

### 1. Initial Server Configuration

```bash
# SSH into server
ssh root@46.62.233.209

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    certbot \
    python3-certbot-nginx \
    docker.io \
    docker-compose

# Create deployment user
adduser boma
usermod -aG sudo boma
usermod -aG docker boma

# Switch to boma user
su - boma
```

### 2. Clone Repository

```bash
# Clone from GitHub
cd /home/boma
git clone https://github.com/YOUR_USERNAME/boma.git
cd boma
```

### 3. Backend Setup

```bash
cd /home/boma/boma/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Set up production environment
cp .env.example .env
nano .env
```

**Production .env Configuration**:
```bash
# Application
APP_NAME=BOMA
ENVIRONMENT=production
DEBUG=False
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=["https://getboma.org","https://www.getboma.org","https://api.getboma.org"]

# Server
HOST=127.0.0.1
PORT=8000

# Database (Local PostgreSQL via Docker)
DATABASE_URL=postgresql+asyncpg://boma_user:boma_password@localhost:5432/boma_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Local File Storage
UPLOAD_DIR=/var/www/boma/uploads
STATIC_URL=/static
MAX_UPLOAD_SIZE_MB=10

# AzamPay (Sandbox - use production credentials when ready)
# Webhook URL: https://api.getboma.org/api/v1/bookings/webhooks/azampay
AZAMPAY_CLIENT_ID=ed3c0530-f27a-4faa-b9f4-fd838418f8de
AZAMPAY_CLIENT_SECRET=EMWixrJKcYrg44CEHK/0neBvGh0rXIZbzhn7BinEr06jzsm+UGLVxzr6LQOkPoUwm2a4CXWxQFo2f7cQMVzOtXCuAMef7buGhBhUAByNHg0QEUSmx+7wuk7N3nSIwBR843Uo7ldpXwQ9YjBuzBR8X/vkbWE5WW7yvcbIiDhipQak/Jjfb/23tmObJBHXpi4wTzaSJADpuyQOAnqQjyyHzdfNKIWWNcux2bj25PjBoq+ZYThbeOlIVD5QFB+mj5WAjmhkomQljAmk7ouOq2+nMa97RSsaomoAkradJ71A4WFBvUIHMJEMLi4Br4PuKkYw47LnPgv1OAvk+2N2LEkDRWVXFwmtRS2bwAd5cmGbHvFv0T9x60RpAXYrZED6aE7AlZRjemeP/v0YB9/17SCDp+RVOu9HyP8vhqnKKvfDaQCImfp+c8FMSttr0rZtmmWS6SlK9QRpbE9tNsyxyYIztlcyYW1YDw2dJ0ubdjWG17dyxHCx5/JGBwDUgp/LLDSAo1g80mlBMyZrxbAG81EIZ2mLrZP/sy7om6cSPKSGILSwdfKwQCMVvJ3lO9Yr8a88qJzNBZNtow5Plmq9BxZIoYte+Kdwts11XLtGKSxNltYpttPKcHyeuKvW2S3uM5jS2sLefds0yeWAV18MbOu1boYqNkJkkI6yS3KcmXHWFWQ=
AZAMPAY_APP_NAME=boma
AZAMPAY_API_URL=https://sandbox.azampay.co.tz
AZAMPAY_WEBHOOK_SECRET=6f4f0b8c7dbe46e29d1a2f4a8d09c5de

# Email (configure when ready)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@getboma.org
SMTP_FROM_NAME=BOMA

# Security
SECRET_KEY=9a028a99452252febeaa7d27d73e879f5b6ec2c790acbe3cf4ed629e1c2241bc
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Regional
DEFAULT_COUNTRY=TZ
DEFAULT_CURRENCY=TZS
DEFAULT_TIMEZONE=Africa/Dar_es_Salaam

# Admin
ADMIN_EMAIL=admin@getboma.org
ADMIN_INITIAL_PASSWORD=CHANGE_THIS_PASSWORD
```

### 4. Database Setup

```bash
# Start PostgreSQL via Docker Compose
cd /home/boma/boma
docker-compose up -d postgres

# Wait for PostgreSQL to start
sleep 5

# Run migrations
cd backend
source venv/bin/activate
alembic upgrade head

# Verify database
docker exec -it boma_postgres psql -U boma_user -d boma_db -c "\dt"
```

### 5. Create Uploads Directory

```bash
# Create uploads directory
sudo mkdir -p /var/www/boma/uploads/{properties,documents,profiles}
sudo chown -R boma:boma /var/www/boma
chmod -R 755 /var/www/boma/uploads
```

### 6. Create Systemd Service

```bash
sudo nano /etc/systemd/system/boma.service
```

**boma.service**:
```ini
[Unit]
Description=BOMA FastAPI Application
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=boma
Group=boma
WorkingDirectory=/home/boma/boma/backend
Environment="PATH=/home/boma/boma/backend/venv/bin"
ExecStart=/home/boma/boma/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/boma/access.log
StandardError=append:/var/log/boma/error.log

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/boma
sudo chown boma:boma /var/log/boma

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable boma
sudo systemctl start boma
sudo systemctl status boma
```

---

## Nginx Configuration

### 1. Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/boma
```

**Production Nginx Config**:
```nginx
# Upstream for FastAPI
upstream boma_backend {
    server 127.0.0.1:8000;
}

# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name getboma.org www.getboma.org api.getboma.org;

    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - Main Website (future)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name getboma.org www.getboma.org;

    # SSL certificates (certbot will add these)
    ssl_certificate /etc/letsencrypt/live/getboma.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/getboma.org/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    # Placeholder for now
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}

# HTTPS - API Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.getboma.org;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/getboma.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/getboma.org/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    client_max_body_size 10M;

    # Static files (uploaded images)
    location /static/ {
        alias /var/www/boma/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin *;
    }

    # API endpoints
    location / {
        proxy_pass http://boma_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Logging
    access_log /var/log/nginx/boma_api_access.log;
    error_log /var/log/nginx/boma_api_error.log;
}
```

### 2. Enable Site and Test

```bash
# Create certbot directory
sudo mkdir -p /var/www/certbot

# Enable site
sudo ln -s /etc/nginx/sites-available/boma /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## SSL Certificate Setup

```bash
# Stop Nginx temporarily
sudo systemctl stop nginx

# Get SSL certificate
sudo certbot certonly --standalone \
    -d getboma.org \
    -d www.getboma.org \
    -d api.getboma.org \
    --email admin@getboma.org \
    --agree-tos \
    --non-interactive

# Start Nginx
sudo systemctl start nginx

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## AzamPay Webhook Configuration

### Configure in AzamPay Dashboard

1. Log in to AzamPay Sandbox: https://developers.azampay.co.tz/
2. Navigate to **Settings** → **Webhooks**
3. Set webhook URL to: `https://api.getboma.org/api/v1/bookings/webhooks/azampay`
4. Webhook secret: `6f4f0b8c7dbe46e29d1a2f4a8d09c5de` (matches .env)
5. Save and test

### Test Webhook

```bash
# Test webhook endpoint
curl -X POST https://api.getboma.org/api/v1/bookings/webhooks/azampay \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

---

## Monitoring & Maintenance

### Check Service Status

```bash
# Backend service
sudo systemctl status boma

# Nginx
sudo systemctl status nginx

# PostgreSQL (Docker)
docker ps | grep postgres

# View logs
sudo journalctl -u boma -f
sudo tail -f /var/log/nginx/boma_api_error.log
```

### Database Backup

```bash
# Manual backup
docker exec boma_postgres pg_dump -U boma_user boma_db > backup_$(date +%Y%m%d).sql

# Automated daily backup (cron)
crontab -e
# Add: 0 2 * * * docker exec boma_postgres pg_dump -U boma_user boma_db > /home/boma/backups/boma_$(date +\%Y\%m\%d).sql
```

### Update Deployment

```bash
# Pull latest code
cd /home/boma/boma
git pull origin master

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Restart service
sudo systemctl restart boma

# Check status
sudo systemctl status boma
```

---

## Firewall Configuration

```bash
# Configure UFW
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable

# Check status
sudo ufw status
```

---

## Testing Checklist

- [ ] DNS resolves getboma.org to 46.62.233.209
- [ ] DNS resolves api.getboma.org to 46.62.233.209
- [ ] HTTPS works on all domains (SSL certificates)
- [ ] API health check: `https://api.getboma.org/health`
- [ ] API docs: `https://api.getboma.org/docs`
- [ ] Static files served: `https://api.getboma.org/static/test.jpg`
- [ ] PostgreSQL running and accessible
- [ ] Backend service running
- [ ] Nginx proxying correctly
- [ ] AzamPay webhook configured
- [ ] Mobile app connects to production API
- [ ] User registration works
- [ ] User login works
- [ ] Property creation works
- [ ] Image upload works
- [ ] Payment flow works

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u boma -n 50
sudo tail -f /var/log/boma/error.log

# Check if port is in use
sudo netstat -tlnp | grep 8000

# Test manually
cd /home/boma/boma/backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Database connection errors
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check connection
docker exec -it boma_postgres psql -U boma_user -d boma_db

# Restart PostgreSQL
docker-compose restart postgres
```

### Nginx errors
```bash
# Check configuration
sudo nginx -t

# View error log
sudo tail -f /var/log/nginx/boma_api_error.log

# Restart Nginx
sudo systemctl restart nginx
```

---

## Production Checklist

- [x] VPS deployed (46.62.233.209)
- [x] DNS configured (getboma.org, api.getboma.org)
- [ ] SSL certificates installed
- [ ] Backend service running
- [ ] PostgreSQL running
- [ ] Nginx configured
- [ ] Firewall configured
- [ ] AzamPay webhook configured
- [ ] Mobile app updated with production URL
- [ ] Database backups automated
- [ ] Monitoring set up
- [ ] Error logging configured

---

**Deployment Status**: Ready for production deployment 🚀
**Next Steps**: Follow this guide to complete SSL setup and go live!
