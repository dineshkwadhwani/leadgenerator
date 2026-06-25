# LeadGenerator Web App Deployment Guide (EC2 / Any Linux Server)

This guide explains how to deploy the Tracksoft LeadGenerator web app on a fresh server.

## 1. What Gets Deployed

- Flask backend: `webapp/app.py`
- UI: `webapp/templates/index.html`
- Background scraper worker: `webapp/worker.py`
- Existing scraper engine: `selenium_scraper.py` (project root)

Default app port: `5001`

## 2. Prerequisites

- Linux server with sudo access (EC2 Ubuntu preferred)
- Public network access (or reverse proxy)
- Git installed
- Python 3.10+ (tested with Python 3.12)
- Chrome browser installed on server (required by Selenium)

## 3. Server Setup (Ubuntu EC2)

Run these commands once on a new machine.

```bash
sudo apt update
sudo apt install -y git curl python3 python3-pip python3-venv unzip

# Install Google Chrome (required for Selenium)
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

## 4. Clone Project

```bash
cd ~
git clone <YOUR_GITHUB_REPO_URL> leadgenerator
cd leadgenerator
```

## 5. Create Virtual Environment + Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r webapp/requirements.txt -r requirements_selenium.txt
```

If `python3 -m venv .venv` fails with `ensurepip is not available`, install venv package and retry:

```bash
sudo apt install -y python3-venv
python3 -m venv .venv
```

## 6. Configure Environment Variables

Create `webapp/.env`:

```bash
cd ~/leadgenerator/webapp
cat > .env << 'EOF'
RESEND_KEY=<YOUR_RESEND_API_KEY>
RESEND_FROM=noreply@tracksoftsolutions.com
PORT=5001
EOF
```

Important:
- Use your own `RESEND_KEY`.
- Do not commit real secrets to git.

## 7. Open Network Port

### EC2 Security Group
Add inbound rule on the security group attached to your instance:
- Type: `Custom TCP`
- Port: `5001`
- Source: `0.0.0.0/0` (or your office IP for restricted access)

### OS Firewall (if enabled)

```bash
sudo ufw status
sudo ufw allow 5001/tcp
```

## 8. Start Application

### Option A: Foreground (simple)

```bash
cd ~/leadgenerator/webapp
./run.sh
```

You should see:
- `Running on http://127.0.0.1:5001`
- `Running on http://<private-ip>:5001`

### Option B: Background (survives SSH close)

```bash
cd ~/leadgenerator/webapp
nohup ./run.sh > server.log 2>&1 &
disown
```

Check status:

```bash
pgrep -af "python app.py|run.sh"
tail -n 100 ~/leadgenerator/webapp/server.log
```

## 9. Verify Deployment

On server:

```bash
curl -I http://127.0.0.1:5001
```

Expected: `HTTP/1.1 200 OK`

From browser:

```text
http://<PUBLIC_IP>:5001
```

Get public IP from server:

```bash
curl http://checkip.amazonaws.com
```

## 10. Update Deployment (after new commits)

```bash
cd ~/leadgenerator
git pull origin main
source .venv/bin/activate
pip install -r webapp/requirements.txt -r requirements_selenium.txt
```

Restart app (if running with nohup):

```bash
pkill -f "python app.py" || true
cd ~/leadgenerator/webapp
nohup ./run.sh > server.log 2>&1 &
disown
```

## 11. Troubleshooting

### A) Browser says connection refused / page not loading

1. Confirm app is running:
```bash
pgrep -af "python app.py|run.sh"
```
2. Confirm local response:
```bash
curl -I http://127.0.0.1:5001
```
3. Confirm security group has port `5001` open.
4. Confirm firewall allows `5001/tcp`.

### B) `No matching distribution found for resend>=4.7.0`

Use project version in `webapp/requirements.txt` (`resend>=2.32.0`) and run:

```bash
git pull origin main
pip install -r webapp/requirements.txt -r requirements_selenium.txt
```

### C) Background run exits immediately

Check logs:

```bash
tail -n 120 ~/leadgenerator/webapp/server.log
```

Also verify you used:

```bash
nohup ./run.sh > server.log 2>&1 &
```

(`./run.sh` is required)

## 12. Optional Hardening (Recommended for Production)

- Put app behind Nginx reverse proxy on ports 80/443.
- Add HTTPS with Let's Encrypt.
- Convert Flask dev server to Gunicorn + systemd service.
- Restrict Security Group source to known IPs.
- Move secrets to AWS SSM Parameter Store or Secrets Manager.

---

If deploying on non-Ubuntu Linux:
- Install equivalent packages (`python3`, `python3-venv`, `pip`, `git`, `curl`, Chrome).
- Use your distro's firewall commands to allow `5001/tcp`.
- Keep the same app commands and folder structure.
