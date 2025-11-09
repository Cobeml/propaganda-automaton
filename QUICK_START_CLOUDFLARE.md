# Quick Start: Get radio.cobe.dev Live in 10 Minutes

## Checklist - Things YOU Need to Do

### ☐ Step 1: Install cloudflared (2 min)
```bash
cd /home/cobe-liu/Developing/fasthtml
./setup_cloudflare_tunnel.sh install
```

Expected output: `✅ cloudflared installed successfully`

---

### ☐ Step 2: Authenticate with Cloudflare (2 min)
```bash
./setup_cloudflare_tunnel.sh auth
```

**IMPORTANT:** 
- A browser window will open (or you'll get a URL)
- Log in to your Cloudflare account
- Select `cobe.dev` domain when prompted
- Return to terminal when done

Expected output: `✅ Authentication successful!`

---

### ☐ Step 3: Create Tunnel (1 min)
```bash
./setup_cloudflare_tunnel.sh create
```

**Copy the Tunnel ID** shown - you'll need it for Step 4!

Expected output: `✅ Configuration file created`

---

### ☐ Step 4: Route DNS (1 min)
```bash
./setup_cloudflare_tunnel.sh route
```

This creates a CNAME record pointing `radio.cobe.dev` to your tunnel.

Expected output: `✅ DNS routed successfully!`

**Alternative (manual):**
1. Go to https://dash.cloudflare.com
2. Click `cobe.dev`
3. Go to DNS → Records
4. Add CNAME: `radio` → `<tunnel-id>.cfargotunnel.com`

---

### ☐ Step 5: Start Tunnel as Background Service (1 min)
```bash
./setup_cloudflare_tunnel.sh daemon
```

This makes tunnel run automatically on boot.

Expected output: `✅ Tunnel service installed and started!`

---

### ☐ Step 6: Start Your Radio Server (1 min)
```bash
cd /home/cobe-liu/Developing/fasthtml
python radio.py
```

Keep this running (or set up as systemd service later).

---

### ☐ Step 7: Test Your Radio! (1 min)

Open in browser: **https://radio.cobe.dev**

You should see:
- ✅ No SSL warning (Cloudflare provides valid cert)
- ✅ Your radio player page loads
- ✅ Audio streams when you click play

**Other URLs to test:**
- Stream: https://radio.cobe.dev/radio/stream
- API: https://radio.cobe.dev/radio/info
- Admin: https://radio.cobe.dev (will show radio player)

---

### ☐ Step 8: Update Frontend URLs (2 min)

**Edit your .env file:**
```bash
nano .env
```

Add or update:
```env
RADIO_SERVER_URL=https://radio.cobe.dev
```

**Update notebook:**
Edit `fasthtml_radio_player.ipynb`, find the audio element and change:
```python
src="https://radio.cobe.dev/radio/stream"
```

And fetch calls:
```javascript
fetch('https://radio.cobe.dev/radio/info')
```

---

## Verification Checklist

After setup, verify everything works:

- [ ] `curl https://radio.cobe.dev/radio/info` returns JSON
- [ ] Opening https://radio.cobe.dev in browser shows your radio page
- [ ] No SSL certificate warnings
- [ ] Audio plays from any device/network
- [ ] Admin panel can add sponsored messages to public stream

---

## Troubleshooting

### "Connection Timed Out" or "522 Error"
**Fix:** Make sure radio.py is running
```bash
ps aux | grep radio.py
# If not running:
python radio.py
```

### "Can't reach origin server"
**Fix:** Check tunnel is running
```bash
./setup_cloudflare_tunnel.sh status
# Should show "active (running)"
```

### "DNS not found" or "radio.cobe.dev not found"
**Fix:** Wait 2-3 minutes for DNS propagation, then try again
```bash
dig radio.cobe.dev
# Should show CNAME record
```

### Tunnel keeps stopping
**Fix:** Use daemon mode (already done in Step 5)
```bash
./setup_cloudflare_tunnel.sh daemon
```

---

## Useful Commands

**Check tunnel status:**
```bash
./setup_cloudflare_tunnel.sh status
```

**View tunnel logs:**
```bash
./setup_cloudflare_tunnel.sh logs
```

**Restart tunnel:**
```bash
./setup_cloudflare_tunnel.sh restart
```

**Stop tunnel:**
```bash
./setup_cloudflare_tunnel.sh stop
```

---

## What You Just Did

```
Your Computer (radio.py on port 5002)
          ↓
   cloudflared tunnel
          ↓
  Cloudflare Network
          ↓
    radio.cobe.dev (public HTTPS)
          ↓
   Anyone on internet!
```

**Benefits:**
- ✅ No port forwarding needed
- ✅ No router configuration
- ✅ Hidden server IP
- ✅ DDoS protection
- ✅ Free HTTPS certificate
- ✅ Works behind NAT/firewall

---

## Share Your Radio

Send this link to anyone:
**https://radio.cobe.dev**

They can:
- Listen to the stream
- Submit sponsored bids (if on frontend page)
- No special setup needed on their end

---

## Next Steps

1. Keep radio.py running 24/7 (see RADIO_SYSTEMD_SERVICE.md)
2. Update all frontend code to use https://radio.cobe.dev
3. Share the link!
4. Monitor usage in Cloudflare dashboard
5. Set up alerts for tunnel downtime (optional)

---

## Cost

**$0/month** forever with Cloudflare Free plan!

No credit card needed, no surprise bills, unlimited bandwidth.

---

## Need Help?

Run the setup script with no arguments to see all options:
```bash
./setup_cloudflare_tunnel.sh
```

Or read the full guide:
```bash
cat CLOUDFLARE_TUNNEL_SETUP.md
```

