# Cloudflare Tunnel Setup Guide for radio.cobe.dev

## What You'll Get

After following this guide, your radio will be accessible at:
- **https://radio.cobe.dev** (public, stable URL)
- Automatic HTTPS (no self-signed cert warnings)
- No port forwarding needed
- Unlimited bandwidth (free!)

---

## Prerequisites

- ✅ Domain: `cobe.dev` (you own this)
- ✅ Cloudflare account (free)
- ✅ Domain DNS managed by Cloudflare

---

## Step 1: Add Domain to Cloudflare (If Not Already)

**⚠️ YOU NEED TO DO THIS:**

1. Go to https://dash.cloudflare.com
2. Log in to your Cloudflare account
3. If `cobe.dev` is not already there, click **"Add Site"**
4. Enter `cobe.dev` and click **Continue**
5. Choose **Free plan** → Continue
6. Cloudflare will show you nameservers (e.g., `brad.ns.cloudflare.com`)
7. Go to your domain registrar (where you bought cobe.dev)
8. Update nameservers to Cloudflare's nameservers
9. Wait for DNS to propagate (can take 24 hours, usually ~1 hour)

**Check if ready:**
```bash
dig cobe.dev NS
# Should show Cloudflare nameservers
```

---

## Step 2: Install Cloudflared

Run this on your server:

```bash
cd /home/cobe-liu/Developing/fasthtml
./setup_cloudflare_tunnel.sh install
```

This will:
- Download cloudflared
- Install it to `/usr/local/bin/`
- Verify installation

---

## Step 3: Authenticate with Cloudflare

**⚠️ YOU NEED TO DO THIS:**

```bash
cloudflared tunnel login
```

This will:
1. Open a browser window (or show you a URL to open)
2. Ask you to log in to Cloudflare
3. Ask you to select your domain (`cobe.dev`)
4. Download a cert file to `~/.cloudflared/cert.pem`

**If it doesn't open browser automatically:**
- Copy the URL shown in terminal
- Open it in a browser
- Complete authentication

---

## Step 4: Create the Tunnel

Run this script:

```bash
cd /home/cobe-liu/Developing/fasthtml
./setup_cloudflare_tunnel.sh create
```

This will:
- Create tunnel named `radio-stream`
- Save tunnel ID and credentials
- Show you the tunnel ID

**Save the tunnel ID** - you'll need it!

---

## Step 5: Configure the Tunnel

The script will create `~/.cloudflared/config.yml` automatically with:

```yaml
tunnel: <your-tunnel-id>
credentials-file: /home/cobe-liu/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: radio.cobe.dev
    service: https://localhost:5002
    originRequest:
      noTLSVerify: true  # Because we use self-signed cert locally
  - service: http_status:404
```

---

## Step 6: Route DNS to Tunnel

**⚠️ YOU NEED TO DO THIS:**

```bash
cloudflared tunnel route dns radio-stream radio.cobe.dev
```

This creates a CNAME record in Cloudflare DNS pointing `radio.cobe.dev` to your tunnel.

**Or do it manually:**
1. Go to https://dash.cloudflare.com
2. Click on `cobe.dev` domain
3. Go to **DNS** → **Records**
4. Click **Add record**
5. Type: `CNAME`
6. Name: `radio`
7. Target: `<tunnel-id>.cfargotunnel.com`
8. Proxy status: **Proxied** (orange cloud)
9. Click **Save**

---

## Step 7: Start the Tunnel

**Option A: Foreground (for testing)**
```bash
cd /home/cobe-liu/Developing/fasthtml
./setup_cloudflare_tunnel.sh start
```

**Option B: Background (daemon)**
```bash
cd /home/cobe-liu/Developing/fasthtml
./setup_cloudflare_tunnel.sh daemon
```

This will:
- Create a systemd service
- Start tunnel automatically on boot
- Run in background

---

## Step 8: Start Your Radio Server

In another terminal:
```bash
cd /home/cobe-liu/Developing/fasthtml
python radio.py
```

---

## Step 9: Test It!

Open in your browser:
- **https://radio.cobe.dev** (your radio player page)
- **https://radio.cobe.dev/radio/stream** (direct audio stream)
- **https://radio.cobe.dev/radio/info** (API endpoint)

---

## Managing the Tunnel

### Check Status
```bash
./setup_cloudflare_tunnel.sh status
```

### View Logs
```bash
./setup_cloudflare_tunnel.sh logs
```

### Stop Tunnel
```bash
./setup_cloudflare_tunnel.sh stop
```

### Restart Tunnel
```bash
./setup_cloudflare_tunnel.sh restart
```

---

## Updating Frontend URLs

After tunnel is working, update your frontend to use the public URL.

**In `fasthtml_radio_player.ipynb`**, find the radio controls cell and update:

```python
Audio(
    id="radio-stream",
    src="https://radio.cobe.dev/radio/stream",  # Update this!
    preload="none"
)
```

And in the JavaScript:
```javascript
const response = await fetch('https://radio.cobe.dev/radio/info');
```

---

## Updating Admin Panel

**In `admin.py`**, update the `.env` file:

```env
RADIO_SERVER_URL=https://radio.cobe.dev
```

Now when you approve bids, it will add to the public radio stream!

---

## Troubleshooting

### "tunnel credentials file doesn't exist"
**Fix:** Run Step 3 again (authenticate)

### "no such host: radio.cobe.dev"
**Fix:** DNS not configured. Check Step 6, wait a few minutes for DNS propagation

### "522 Connection Timed Out"
**Fix:** Make sure radio.py is running on port 5002

### "can't reach origin server"
**Fix:** 
1. Check radio.py is running: `ps aux | grep radio.py`
2. Check tunnel is running: `./setup_cloudflare_tunnel.sh status`
3. Check local server works: `curl -k https://localhost:5002/radio/info`

### Tunnel keeps disconnecting
**Fix:** Use daemon mode (Step 7, Option B) for persistent connection

---

## Security Notes

- ✅ Cloudflare provides DDoS protection
- ✅ Traffic is encrypted (HTTPS)
- ✅ Your server's IP is hidden
- ✅ Rate limiting available in Cloudflare dashboard
- ⚠️ Admin panel still local only (http://localhost:5001)

---

## What Happens Behind the Scenes

```
User's Browser
      ↓
   (HTTPS)
      ↓
Cloudflare Edge Server (radio.cobe.dev)
      ↓
  (Encrypted Tunnel)
      ↓
Your Computer (localhost:5002)
      ↓
Radio Python Server
```

No ports need to be opened on your router!

---

## Cost

**$0/month** - Completely free with Cloudflare Free plan!

- Unlimited bandwidth
- Unlimited concurrent connections
- DDoS protection included
- 99.9% uptime

---

## Next Steps After Setup

1. Update frontend to use `https://radio.cobe.dev`
2. Share the link with friends
3. Test from different devices/networks
4. Set tunnel to auto-start (daemon mode)
5. Keep radio.py running (or set up systemd service)

---

## Keeping Radio Running 24/7

Want radio to run even when you're not logged in? See `RADIO_SYSTEMD_SERVICE.md` for setting up radio.py as a system service.

