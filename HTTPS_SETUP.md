# HTTPS Setup Guide for Video Quest

Mobile browsers require **HTTPS (secure connections)** to access device cameras. This guide provides several options to enable HTTPS for your Video Quest application.

## Why HTTPS is Required

Modern web browsers enforce security policies that require HTTPS for accessing sensitive device features like:
- Camera
- Microphone
- Geolocation
- Notifications

While `http://localhost` works on desktop browsers, mobile devices on the local network need HTTPS.

## Quick Workaround: Manual Entry

The QR scan page now includes a **Manual Entry** option. Users can:
1. Click "Scan QR Code"
2. Scroll down to "Manual Entry"
3. Enter the video ID number (1, 2, 3, etc.)
4. Click "Go to Video"

This bypasses the camera entirely and works without HTTPS.

---

## Option 1: Self-Signed Certificate (Recommended for LAN)

### Step 1: Generate SSL Certificate

Create a self-signed certificate for your local network:

```bash
# Install OpenSSL (if not already installed)
# Windows: Download from https://slproweb.com/products/Win32OpenSSL.html
# Mac: brew install openssl
# Linux: sudo apt-get install openssl

# Generate certificate (replace YOUR_SERVER_IP with actual IP)
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=YOUR_SERVER_IP"
```

Example:
```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=192.168.1.100"
```

### Step 2: Update Flask App for HTTPS

Edit `app/app.py` and change the last line:

```python
# Change from:
app.run(host='0.0.0.0', port=8080, debug=False)

# To:
app.run(host='0.0.0.0', port=8080, debug=False,
        ssl_context=('cert.pem', 'key.pem'))
```

### Step 3: Copy Certificates to Container

Update `docker-compose.yml`:

```yaml
services:
  video-quest:
    build: .
    container_name: video-quest
    ports:
      - "8080:8080"
    volumes:
      - ./app/database.db:/app/database.db
      - ./app/videos:/app/videos
      - ./cert.pem:/app/cert.pem        # Add this
      - ./key.pem:/app/key.pem          # Add this
    restart: always
```

### Step 4: Trust Certificate on Mobile

**iOS:**
1. Visit `https://YOUR_IP:8080` in Safari
2. Tap "Show Details" → "Visit This Website"
3. Confirm the security warning

**Android:**
1. Visit `https://YOUR_IP:8080` in Chrome
2. Click "Advanced" → "Proceed to YOUR_IP (unsafe)"

**Note**: You'll need to accept the security warning since it's self-signed.

### Step 5: Rebuild and Restart

```bash
docker-compose down
docker-compose up -d --build
```

Access via: `https://YOUR_IP:8080`

---

## Option 2: Reverse Proxy with Caddy (Automatic HTTPS)

Caddy automatically manages HTTPS certificates.

### Step 1: Create Caddyfile

```bash
# Create Caddyfile
cat > Caddyfile << 'EOF'
your-domain.local {
    reverse_proxy video-quest:8080
    tls internal
}
EOF
```

### Step 2: Update docker-compose.yml

```yaml
version: '3.8'

services:
  video-quest:
    build: .
    container_name: video-quest
    volumes:
      - ./app/database.db:/app/database.db
      - ./app/videos:/app/videos
    restart: always

  caddy:
    image: caddy:latest
    container_name: video-quest-caddy
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - video-quest
    restart: always

volumes:
  caddy_data:
  caddy_config:
```

### Step 3: Start Services

```bash
docker-compose up -d
```

Access via: `https://your-domain.local`

---

## Option 3: ngrok Tunnel (Internet Access)

ngrok creates a public HTTPS URL that tunnels to your local server.

### Step 1: Install ngrok

Download from: https://ngrok.com/download

Or install via package manager:
```bash
# Windows (chocolatey)
choco install ngrok

# Mac
brew install ngrok

# Linux
snap install ngrok
```

### Step 2: Sign Up and Authenticate

1. Create free account at https://ngrok.com
2. Get your authtoken
3. Authenticate:
```bash
ngrok authtoken YOUR_AUTH_TOKEN
```

### Step 3: Start Tunnel

```bash
ngrok http 8080
```

You'll get a public HTTPS URL like:
```
https://abc123.ngrok.io
```

### Step 4: Access Application

Use the ngrok URL on any device:
```
https://abc123.ngrok.io
```

**Pros:**
- Works from anywhere (not just LAN)
- Real HTTPS certificate
- No certificate warnings

**Cons:**
- Requires internet connection
- URL changes each time (unless paid plan)
- Third-party service

---

## Option 4: Nginx Reverse Proxy

### Step 1: Generate Certificate

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout nginx-key.pem -out nginx-cert.pem -days 365 \
  -subj "/CN=192.168.1.100"
```

### Step 2: Create nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    server {
        listen 443 ssl;
        server_name 192.168.1.100;

        ssl_certificate /etc/nginx/cert.pem;
        ssl_certificate_key /etc/nginx/key.pem;

        location / {
            proxy_pass http://video-quest:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        return 301 https://$host$request_uri;
    }
}
```

### Step 3: Update docker-compose.yml

```yaml
version: '3.8'

services:
  video-quest:
    build: .
    container_name: video-quest
    volumes:
      - ./app/database.db:/app/database.db
      - ./app/videos:/app/videos
    restart: always

  nginx:
    image: nginx:alpine
    container_name: video-quest-nginx
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx-cert.pem:/etc/nginx/cert.pem:ro
      - ./nginx-key.pem:/etc/nginx/key.pem:ro
    depends_on:
      - video-quest
    restart: always
```

### Step 4: Start Services

```bash
docker-compose up -d
```

Access via: `https://YOUR_IP`

---

## Comparison of Options

| Option | Complexity | Cost | Best For |
|--------|-----------|------|----------|
| **Manual Entry** | None | Free | Quick workaround, no QR scanning |
| **Self-Signed Cert** | Low | Free | LAN-only, accept security warnings |
| **Caddy** | Medium | Free | LAN with automatic cert management |
| **ngrok** | Low | Free* | Internet access, demo/testing |
| **Nginx** | Medium | Free | Full control, production-like |

*ngrok free tier has limitations

---

## Recommended Approach

### For Testing/Development:
Use **Manual Entry** - no setup required

### For LAN Events (Escape Room, Conference):
Use **Self-Signed Certificate** - simple and works offline

### For Internet Access:
Use **ngrok** - easiest public HTTPS

### For Production Deployment:
Use **Caddy** or **Nginx** with proper certificates

---

## Troubleshooting

### "NET::ERR_CERT_AUTHORITY_INVALID"

This is expected with self-signed certificates. On mobile:
- iOS: Tap "Show Details" → "visit this website"
- Android: Click "Advanced" → "Proceed to [site]"

### Camera Still Not Working

1. **Check browser permissions**: Settings → Site Settings → Camera
2. **Try Chrome**: Best camera API support
3. **Use Manual Entry**: Works without camera access
4. **Check HTTPS**: URL must show 🔒 padlock icon

### Certificate Errors After IP Change

Regenerate certificate with new IP address:
```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=NEW_IP_ADDRESS"
```

---

## Security Notes

### Self-Signed Certificates
- **Safe for LAN use**: No security risk on trusted local network
- **Not for production**: Use proper CA-signed certificates for internet-facing sites
- **Expires**: Regenerate after expiration (default 365 days)

### ngrok
- **Secure tunnel**: End-to-end encrypted
- **Public URL**: Anyone with URL can access
- **Rate limits**: Free tier has limits

---

## Additional Resources

- [Let's Encrypt](https://letsencrypt.org/) - Free CA certificates
- [mkcert](https://github.com/FiloSottile/mkcert) - Local CA for development
- [Caddy Documentation](https://caddyserver.com/docs/)
- [ngrok Documentation](https://ngrok.com/docs)

---

## Quick Reference

### Get Your IP Address

**Windows:**
```cmd
ipconfig
```

**Mac/Linux:**
```bash
ifconfig
# or
ip addr show
```

### Test HTTPS

```bash
curl -k https://YOUR_IP:8080
```

### View Certificate Details

**OpenSSL:**
```bash
openssl x509 -in cert.pem -text -noout
```

**Browser:**
Click the padlock icon → Certificate information

---

For questions or issues, see the main README.md or SETUP_GUIDE.md.
