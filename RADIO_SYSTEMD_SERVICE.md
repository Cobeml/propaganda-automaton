# Running Radio 24/7 as a System Service

Once your Cloudflare Tunnel is set up, you'll want your radio to run all the time, even when you're not logged in.

## Quick Setup

Run this helper script:

```bash
cd /home/cobe-liu/Developing/fasthtml
./setup_radio_service.sh install
```

## What This Does

Creates a systemd service that:
- ✅ Starts radio.py automatically on boot
- ✅ Restarts if it crashes
- ✅ Runs in background
- ✅ Logs to journald

## Manual Setup (if you prefer)

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/radio.service
```

Paste this:

```ini
[Unit]
Description=Radio Streaming Server
After=network.target
Wants=cloudflared.service

[Service]
Type=simple
User=cobe-liu
WorkingDirectory=/home/cobe-liu/Developing/fasthtml
Environment="PATH=/home/cobe-liu/Developing/fasthtml/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/cobe-liu/Developing/fasthtml/.venv/bin/python radio.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable (auto-start on boot)
sudo systemctl enable radio.service

# Start now
sudo systemctl start radio.service

# Check status
sudo systemctl status radio.service
```

## Managing the Service

### Check Status
```bash
sudo systemctl status radio.service
```

### View Logs
```bash
sudo journalctl -u radio.service -f
```

### Stop Service
```bash
sudo systemctl stop radio.service
```

### Restart Service
```bash
sudo systemctl restart radio.service
```

### Disable Auto-Start
```bash
sudo systemctl disable radio.service
```

## Verification

After starting, check it's working:

```bash
# Should show "active (running)"
sudo systemctl status radio.service

# Should return JSON
curl -k https://localhost:5002/radio/info

# Should be accessible publicly
curl https://radio.cobe.dev/radio/info
```

## Troubleshooting

### Service fails to start

**Check logs:**
```bash
sudo journalctl -u radio.service -n 50
```

**Common issues:**
- Wrong Python path → Check `.venv/bin/python` exists
- Permission errors → Service runs as `cobe-liu` user
- Port already in use → Check if radio.py running elsewhere

### Radio works locally but not via radio.cobe.dev

**Check tunnel:**
```bash
sudo systemctl status cloudflared
```

Both services should be running:
- `radio.service` ✅
- `cloudflared.service` ✅

## Complete Setup (Both Services)

To have everything run on boot:

```bash
# Install radio service
./setup_radio_service.sh install

# Both should be enabled and running
sudo systemctl status radio.service
sudo systemctl status cloudflared.service
```

Now your radio streams 24/7 at **https://radio.cobe.dev** 🎉

## Reboot Test

Reboot your computer to test:

```bash
sudo reboot
```

After reboot:
1. Wait 1-2 minutes
2. Open https://radio.cobe.dev
3. Should work without any manual intervention!

## Monitoring

### Check both services are running:
```bash
systemctl is-active radio.service cloudflared.service
```

Should output:
```
active
active
```

### View combined logs:
```bash
sudo journalctl -u radio.service -u cloudflared.service -f
```

## Resource Usage

Radio streaming is lightweight:

```bash
# Check CPU/Memory usage
systemctl status radio.service
```

Typical usage:
- CPU: ~5-10% (when streaming)
- RAM: ~100-200 MB
- Bandwidth: Depends on listeners (each listener ~128 kbps)

## Updating the Code

When you update your code:

```bash
# Stop service
sudo systemctl stop radio.service

# Pull/edit your code
git pull  # or edit files

# Restart service
sudo systemctl restart radio.service

# Check it's running
sudo systemctl status radio.service
```

## Logs Location

All logs go to systemd journal:

```bash
# Recent logs
sudo journalctl -u radio.service -n 100

# Today's logs
sudo journalctl -u radio.service --since today

# Follow live
sudo journalctl -u radio.service -f
```

## Admin Panel

The admin panel (`admin.py`) is separate and runs on demand:

```bash
python admin.py
```

Access at: http://localhost:5001

Don't make admin.py a service - keep it manual for security.

