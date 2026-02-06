#!/usr/bin/env bash
# Setup script for HTTPS on lschannel.fun
# Run this on your remote server after obtaining the certificate

set -e

echo "Setting up Nginx configuration for lschannel.fun..."

# Create nginx config file
sudo tee /etc/nginx/sites-available/lschannel.fun > /dev/null <<'EOF'
# HTTP server - redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name lschannel.fun;

    # Redirect all HTTP traffic to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name lschannel.fun;

    # SSL certificate configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/lschannel.fun/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lschannel.fun/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection keep-alive;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_cache_bypass $http_upgrade;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # Increase body size limit for large file uploads/downloads
    client_max_body_size 2G;

    # Proxy all requests to ASP.NET Core app (running on port 80)
    location / {
        proxy_pass http://127.0.0.1:80;
    }
}
EOF

# Create symlink if it doesn't exist
if [ ! -L /etc/nginx/sites-enabled/lschannel.fun ]; then
    sudo ln -s /etc/nginx/sites-available/lschannel.fun /etc/nginx/sites-enabled/lschannel.fun
fi

# Test nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Reload nginx
echo "Reloading Nginx..."
sudo systemctl reload nginx

echo ""
echo "✓ HTTPS setup complete!"
echo "Test it: curl -I https://lschannel.fun"
echo ""
echo "Note: Make sure your ASP.NET Core app is running on port 80:"
echo "  ASPNETCORE_URLS=http://0.0.0.0:80 ./LschannelFun"
