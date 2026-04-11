# Important Commands

Quick operational commands for SeatSeeker on EC2.

Release note: Turnstile CAPTCHA is disabled for the v1 prototype release (`TURNSTILE_ENABLED=false`).

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
echo; echo "== Subscription POST check (CAPTCHA disabled for v1, expect 201) =="; \
curl -sS -i -X POST http://127.0.0.1:5000/api/subscriptions \
  -H "Content-Type: application/json" \
  -d '{"email":"healthcheck@example.com","crns":["12345"]}' | sed -n '1,18p'; \
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

## 9) Check sent notification history (SQLite)

```bash
APP_DIR=/home/ubuntu/SeatSeeker-UC-Merced-Course-Availability-Notifier/main
sqlite3 "$APP_DIR/database.db" "SELECT COUNT(*) AS sent_count FROM sent_notifications;"
sqlite3 -header -column "$APP_DIR/database.db" \
  "SELECT id,email,crn,sent_at,source FROM sent_notifications ORDER BY sent_at DESC LIMIT 30;"
```
