# Deployment Guide

This guide covers deploying the Edamam Food Database MCP Server for production use.

## Deployment Options

### Option 1: Claude Desktop (Local)

Best for: Personal use with Claude Desktop application

**Setup:**

1. Ensure the server is installed:
   ```bash
   cd /path/to/mcp-edamam-food
   uv sync --extra dev
   ```

2. Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
   ```json
   {
     "mcpServers": {
       "edamam-food": {
         "command": "uv",
         "args": [
           "run",
           "/absolute/path/to/mcp-edamam-food/src/mcp_server.py"
         ],
         "env": {
           "EDAMAM_APP_ID": "your_app_id",
           "EDAMAM_APP_KEY": "your_app_key"
         }
       }
     }
   }
   ```

3. Restart Claude Desktop

**Verification:**
- Open Claude Desktop
- Type: "List available tools"
- Should see: get_food_nutrition, search_food, analyze_food_image

---

### Option 2: Streamable HTTP Server (Remote Hosting)

Best for: Hosting as a service for multiple clients

#### Basic Setup

1. **Clone and Install:**
   ```bash
   git clone https://github.com/edamam/mcp-edamam-food.git
   cd mcp-edamam-food
   uv sync
   ```

2. **Configure Environment:**
   ```bash
   export EDAMAM_APP_ID="your_app_id"
   export EDAMAM_APP_KEY="your_app_key"
   ```

3. **Run Server:**
   ```bash
   uv run src/mcp_server.py
   ```

   Server starts on `http://0.0.0.0:8000/v1/ai/query`

#### Production Setup with systemd

1. **Create systemd service file:**
   ```bash
   sudo nano /etc/systemd/system/edamam-mcp.service
   ```

2. **Service configuration:**
   ```ini
   [Unit]
   Description=Edamam MCP Server
   After=network.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=mcp-user
   Group=mcp-user
   WorkingDirectory=/opt/mcp-edamam-food
   Environment="EDAMAM_APP_ID=your_app_id"
   Environment="EDAMAM_APP_KEY=your_app_key"
   Environment="PYTHONUNBUFFERED=1"
   ExecStart=/usr/local/bin/uv run src/mcp_server.py
   Restart=always
   RestartSec=10
   StandardOutput=journal
   StandardError=journal

   # Security settings
   NoNewPrivileges=true
   PrivateTmp=true
   ProtectSystem=strict
   ProtectHome=true
   ReadWritePaths=/opt/mcp-edamam-food/logs

   [Install]
   WantedBy=multi-user.target
   ```

3. **Create user and directories:**
   ```bash
   sudo useradd -r -s /bin/false mcp-user
   sudo mkdir -p /opt/mcp-edamam-food
   sudo cp -r . /opt/mcp-edamam-food/
   sudo chown -R mcp-user:mcp-user /opt/mcp-edamam-food
   ```

4. **Enable and start service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable edamam-mcp
   sudo systemctl start edamam-mcp
   ```

5. **Check status:**
   ```bash
   sudo systemctl status edamam-mcp
   sudo journalctl -u edamam-mcp -f
   ```

---

### Option 3: Docker Deployment

Best for: Containerized environments, cloud platforms

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.13-slim

   WORKDIR /app

   # Install uv
   RUN pip install uv

   # Copy project files
   COPY pyproject.toml uv.lock ./
   COPY src/ ./src/
   COPY tests/ ./tests/

   # Install dependencies
   RUN uv sync

   # Create logs directory
   RUN mkdir -p logs

   # Expose MCP port
   EXPOSE 8000

   # Run server
   CMD ["uv", "run", "src/mcp_server.py"]
   ```

2. **Create docker-compose.yml:**
   ```yaml
   version: '3.8'

   services:
     edamam-mcp:
       build: .
       ports:
         - "8000:8000"
       environment:
         - EDAMAM_APP_ID=${EDAMAM_APP_ID}
         - EDAMAM_APP_KEY=${EDAMAM_APP_KEY}
       volumes:
         - ./logs:/app/logs
       restart: unless-stopped
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
         interval: 30s
         timeout: 10s
         retries: 3
   ```

3. **Create .env file:**
   ```bash
   EDAMAM_APP_ID=your_app_id
   EDAMAM_APP_KEY=your_app_key
   ```

4. **Build and run:**
   ```bash
   docker-compose up -d
   ```

5. **View logs:**
   ```bash
   docker-compose logs -f
   ```

---

## Reverse Proxy Configuration

### Nginx

For SSL/TLS termination and proxying:

```nginx
server {
    listen 80;
    server_name mcp.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mcp.example.com;

    ssl_certificate /etc/letsencrypt/live/mcp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp.example.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # MCP streamable HTTP settings
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection '';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Streaming-specific: disable buffering
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        chunked_transfer_encoding off;

        # CORS headers (adjust as needed)
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
}
```

### Caddy

Simpler alternative with automatic HTTPS:

```caddyfile
mcp.example.com {
    reverse_proxy localhost:8000 {
        # Streaming-specific settings
        flush_interval -1
        transport http {
            response_header_timeout 0
        }
    }
}
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `EDAMAM_APP_ID` | Edamam API application ID | `abc123` |
| `EDAMAM_APP_KEY` | Edamam API key | `def456...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_HOST` | Server host | `0.0.0.0` |
| `MCP_PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## Monitoring

### Logging

Logs are written to `logs/mcp_requests.log`:

```bash
# Tail logs
tail -f logs/mcp_requests.log

# Search for errors
grep ERROR logs/mcp_requests.log

# Watch API calls
grep "Tool called" logs/mcp_requests.log
```

### Log Rotation

Set up logrotate:

```bash
sudo nano /etc/logrotate.d/edamam-mcp
```

```text
/opt/mcp-edamam-food/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 mcp-user mcp-user
}
```

### Health Checks

Add a health check endpoint (optional enhancement):

```python
# In src/mcp_server.py
@mcp.resource("health")
def health():
    return {"status": "healthy", "version": "1.0.0"}
```

---

## Security Considerations

### 1. API Credentials

**Never commit credentials to git:**
```bash
# .gitignore already includes:
.env
*.key
```

**Use environment variables or secrets management:**
- systemd: Environment files
- Docker: `.env` files or secrets
- Kubernetes: ConfigMaps/Secrets
- Cloud: AWS Secrets Manager, GCP Secret Manager, etc.

### 2. Network Security

- Use HTTPS/TLS in production
- Implement authentication if exposing publicly
- Use firewall rules to restrict access
- Consider VPN for internal-only access

### 3. Rate Limiting

Edamam API has rate limits. Monitor usage:

```python
# Optional: Add rate limiting middleware
from fastmcp import RateLimiter

mcp = FastMCP(
    "edamam-food",
    middleware=[RateLimiter(requests=100, window=60)]
)
```

---

## Performance Tuning

### 1. Concurrent Requests

FastMCP handles concurrent requests well. For high load:

```python
# Increase connection pool in edamam_service.py
async with httpx.AsyncClient(
    timeout=10.0,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
) as client:
    # ...
```

### 2. Caching (Optional)

For frequently requested items:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
async def search_food_cached(query: str):
    return await search_food(query)
```

### 3. Resource Limits

Set appropriate limits in systemd:

```ini
[Service]
LimitNOFILE=65535
MemoryLimit=512M
CPUQuota=200%
```

---

## Backup and Recovery

### Backup

No database to backup, but preserve:

1. **Configuration:**
   ```bash
   tar -czf edamam-mcp-backup.tar.gz \
     /opt/mcp-edamam-food/src/ \
     /opt/mcp-edamam-food/pyproject.toml \
     /etc/systemd/system/edamam-mcp.service
   ```

2. **Logs (optional):**
   ```bash
   tar -czf logs-backup-$(date +%Y%m%d).tar.gz \
     /opt/mcp-edamam-food/logs/
   ```

### Recovery

1. Restore from backup
2. Reinstall dependencies: `uv sync`
3. Restore systemd service
4. Restart: `sudo systemctl restart edamam-mcp`

---

## Troubleshooting

### Server Won't Start

**Check logs:**
```bash
sudo journalctl -u edamam-mcp -n 50
```

**Common issues:**
- Missing environment variables
- Port already in use
- Permissions on logs directory
- uv not in PATH

### Streaming Connection Issues

**Symptoms:** Client can't connect

**Solutions:**
- Check firewall rules
- Verify reverse proxy streaming settings
- Check `proxy_buffering off` in nginx
- Verify CORS headers if cross-origin
- Ensure chunked transfer encoding is properly configured

### High Memory Usage

**Check:**
```bash
ps aux | grep mcp_server
```

**Solutions:**
- Restart service periodically
- Reduce connection pool size
- Clear log files
- Check for memory leaks in custom code

### Edamam API Errors

**Check:**
- API credentials are correct
- Not exceeding rate limits
- Network connectivity to api.edamam.com
- API service status

---

## Scaling

### Horizontal Scaling

Run multiple instances behind a load balancer:

```yaml
# docker-compose.yml
services:
  edamam-mcp-1:
    build: .
    ports: ["8001:8000"]
    # ...

  edamam-mcp-2:
    build: .
    ports: ["8002:8000"]
    # ...

  nginx:
    image: nginx:alpine
    ports: ["80:80"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Vertical Scaling

Increase resources:
- More CPU cores
- More memory
- Faster network

---

## Updates and Maintenance

### Updating the Server

```bash
cd /opt/mcp-edamam-food
git pull origin main
uv sync
sudo systemctl restart edamam-mcp
```

### Maintenance Windows

For zero-downtime updates:
1. Run multiple instances
2. Update one at a time
3. Health check before switching

---

## Support

For deployment issues:
- Check logs first
- Review this guide
- Open GitHub issue
- Check FastMCP documentation
