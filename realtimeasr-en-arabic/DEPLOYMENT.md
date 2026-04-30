# Deployment guide

## Quick start

### 1. Clone

```bash
git clone <repository-url>
cd realtime-en-arabic
```

### 2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Environment variables

Create `.env` at the repository root and set at least `SPEECHMATICS_API_KEY`:

```bash
# Example: copy from a template if your team provides one, then edit.
nano .env
```

### 4. Run services

**Development:**

```bash
# Terminal 1: backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8010 --reload

# Terminal 2: frontend
cd frontend
python -m http.server -b 0.0.0.0 8765
```

Open: `http://localhost:8765`

**Production:** see `README.md` for systemd, Nginx, HTTPS, and firewall steps.

## Important configuration

### Required environment variables

- `SPEECHMATICS_API_KEY`: Speechmatics API key (required)
- `SPEECHMATICS_URL`: Speechmatics WebSocket URL (default: `wss://eu2.rt.speechmatics.com/v2`)
- `HOST`: bind address (default: `0.0.0.0`)
- `PORT`: HTTP port (default: `8010`)

### Frontend / WebSocket

If the API runs on another host, set the WebSocket base URL via `frontend/js/app.js` (`window.REALTIME_WS_BASE`, meta tag, or `realtimeWsBase` query). Example:

```javascript
// See getConfiguredWebSocketBaseUrl() in app.js
window.REALTIME_WS_BASE = 'wss://your-backend-domain.com';
```

## Production checklist

- [ ] HTTPS enabled (required for microphone access in the browser)
- [ ] Secrets in environment variables (no API keys in the repo)
- [ ] Nginx (or similar) reverse proxy configured
- [ ] systemd (or similar) for automatic backend restarts
- [ ] Firewall rules reviewed
- [ ] Log rotation configured
- [ ] Monitoring and alerting as needed

## Testing

### Health check

```bash
curl http://localhost:8010/health
# expect: {"status":"healthy"}
```

### WebSocket

Open DevTools on the frontend, click **Start speaking**, and verify:

1. WebSocket connects successfully.
2. Microphone permission is granted.
3. Partial/final transcripts appear.

## Troubleshooting

### Backend will not start

```bash
# Check port usage (Linux)
netstat -tulpn | grep 8010

# More verbose logs
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8010 --log-level debug
```

### WebSocket failures

1. Confirm the backend process is running.
2. Review firewall rules.
3. Validate Nginx proxy headers and timeouts if used.
4. Check the browser console for errors.

### Microphone issues

- Production must use HTTPS.
- Review browser permission settings for the site.
- Try a private window to rule out extensions.

## Contact

- Technical support: [your-email]
- Main documentation: `README.md`
