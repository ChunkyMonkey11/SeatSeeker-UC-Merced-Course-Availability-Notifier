# Important Commands

Quick operational commands for SeatSeeker on EC2.

## 0) Set app directory

```bash
APP_DIR=/home/ubuntu/SeatSeeker-UC-Merced-Course-Availability-Notifier/main
```

## 1) One-shot health check pack

```bash
APP_DIR=/home/ubuntu/SeatSeeker-UC-Merced-Course-Availability-Notifier/main; \
echo "== Services =="; \
sudo systemctl status seatseeker-dashboard --no-pager | sed -n '1,8p'; \
sudo systemctl status seatseeker-scheduler --no-pager | sed -n '1,8p'; \
echo; echo "== Local API =="; \
curl -sS -i http://127.0.0.1:5000/api/health | sed -n '1,12p'; \
echo; echo "== CAPTCHA enforcement check (expect 400) =="; \
curl -sS -i -X POST http://127.0.0.1:5000/api/subscriptions \
  -H "Content-Type: application/json" \
  -d '{"email":"healthcheck@example.com","crns":["12345"]}' | sed -n '1,14p'; \
echo; echo "== Listening ports =="; \
sudo ss -ltnp | grep -E ':5000|:80|:443' || true
```

## 2) Restart services

```bash
sudo systemctl restart seatseeker-dashboard
sudo systemctl restart seatseeker-scheduler
```

## 3) Follow logs

```bash
sudo journalctl -u seatseeker-dashboard -f
sudo journalctl -u seatseeker-scheduler -f
```

## 4) Check Turnstile env values

```bash
APP_DIR=/home/ubuntu/SeatSeeker-UC-Merced-Course-Availability-Notifier/main
sudo grep -nE "^TURNSTILE_(ENABLED|SITE_KEY|SECRET_KEY)=" "$APP_DIR/.env"
```

## 5) Update dependencies in venv

```bash
APP_DIR=/home/ubuntu/SeatSeeker-UC-Merced-Course-Availability-Notifier/main
VENV="$APP_DIR/venv"
"$VENV/bin/pip" install -r "$APP_DIR/requirements.txt"
```

## 6) SSH from local machine

```bash
ssh -i /Users/revant/Downloads/seatseeker-key.pem ubuntu@18.220.124.10
```

## 7) Find your current public IP (local machine)

```bash
curl https://api.ipify.org
```

## 8) Safe deploy (tests must pass before restart)

Run this on EC2 from the repo root:

```bash
cd /home/ubuntu/SeatSeeker-UC-Merced-Course-Availability-Notifier
./deploy/scripts/safe_deploy.sh main
```
