# lschannel.fun (ASP.NET Core)

Port of lschannel.fun from Tomcat/Java to ASP.NET Core.

## Run locally

```bash
cd /Users/ls/Documents/lschannel.fun_asp
dotnet run
```

Then open:
- http://localhost:8080 (redirects to /en/ or /cn/ by Accept-Language)
- http://localhost:8080/en/ or http://localhost:8080/cn/

For local HTTPS (optional), the app also listens on https://localhost:8443. Trust the dev certificate once with:
`dotnet dev-certs https --trust`

**Note**: In production, nginx handles HTTPS (port 443) and proxies to the app on HTTP (port 8080). The app doesn't need to handle HTTPS directly in production.

## Multimedia files

Copy your media from the Tomcat webapp into `wwwroot/multimedia/`:

- `wwwroot/multimedia/lsLearns/` — MP4 videos for lsLearns tab
- `wwwroot/multimedia/paintings/` — images for Paintings/手绘 tab
- `wwwroot/multimedia/music/` — MP4 videos for Music/音乐 tab

File names are hardcoded in the HTML/JS; add the same files as on the Tomcat site.

## Structure

- `Program.cs` — redirect `/` to `/en/` or `/cn/`, rewrite `/en/` and `/cn/` to `index.html`, static files
- `wwwroot/en/index.html` — English UI (lsLearns, Paintings, Music, About)
- `wwwroot/cn/index.html` — Chinese UI (ls学, 手绘, 音乐, 关于)
- `wwwroot/images/` — avatar and other images
- `wwwroot/multimedia/` — videos and paintings (you copy these in)

## Deploy as a pack (server has .NET 8)

Like deploying a WAR to Tomcat: build one pack, copy to the server, extract and run.

**1. Build the pack** (on your dev machine):

```bash
chmod +x build-pack.sh
./build-pack.sh
```

This produces `LschannelFun-pack.tar.gz`.

**2. Copy to CentOS 8** and run:

```bash
scp LschannelFun-pack.tar.gz user@your-server:/opt/
ssh user@your-server
cd /opt && mkdir -p lschannelfun && tar -xzf LschannelFun-pack.tar.gz -C lschannelfun && cd lschannelfun
ASPNETCORE_URLS=http://0.0.0.0:8080 ./LschannelFun
```

**Note**: Port 8080 is used by default so that nginx can bind to port 80 for HTTPS reverse proxy. If you're not using nginx, you can use port 80: `ASPNETCORE_URLS=http://0.0.0.0:80 ./LschannelFun`

The server must have .NET 8 runtime (or SDK) installed. No need to install the runtime on the server if you use the self-contained build instead: run `./build-deploy.sh` and use the generated `LschannelFun-linux-x64.tar.gz`.

## Set up HTTPS with Nginx and Let's Encrypt

For production HTTPS on `lschannel.fun`, you need to set up Nginx as a reverse proxy with SSL certificates.

**1. Install Nginx and Certbot** (on CentOS/RHEL):

```bash
sudo yum install -y nginx certbot python3-certbot-nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

**2. Get SSL certificate from Let's Encrypt**:

```bash
sudo certbot certonly --nginx -d lschannel.fun
```

If certbot can't automatically configure nginx (common), it will still obtain the certificate. Then proceed to step 3.

**Note**: If you also want to support `www.lschannel.fun`, first add a DNS A record for `www.lschannel.fun` pointing to your server's IP, then run:
```bash
sudo certbot certonly --nginx -d lschannel.fun -d www.lschannel.fun
```

**3. Configure Nginx with SSL** (required after obtaining certificate):

**Option A: Use the setup script** (easiest, works on both Debian/Ubuntu and CentOS/RHEL):

```bash
scp setup-https.sh user@server:/tmp/
ssh user@server
chmod +x /tmp/setup-https.sh
sudo /tmp/setup-https.sh
```

**Option B: Manual configuration**:

**For CentOS/RHEL** (uses `/etc/nginx/conf.d/`):

```bash
scp nginx-lschannel.fun.conf user@server:/tmp/
ssh user@server
sudo cp /tmp/nginx-lschannel.fun.conf /etc/nginx/conf.d/lschannel.fun.conf
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

**For Debian/Ubuntu** (uses `sites-available`/`sites-enabled`):

```bash
scp nginx-lschannel.fun.conf user@server:/tmp/
ssh user@server
sudo cp /tmp/nginx-lschannel.fun.conf /etc/nginx/sites-available/lschannel.fun
sudo mkdir -p /etc/nginx/sites-enabled
sudo ln -s /etc/nginx/sites-available/lschannel.fun /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

**Note**: The nginx config file only includes `lschannel.fun` (without www). If you want to support `www.lschannel.fun`, first add a DNS A record for it, then update the `server_name` directives in the nginx config to include `www.lschannel.fun`.

**4. Stop any process using port 80**:

Before starting nginx, make sure nothing is using port 80. Check what's using it:

```bash
sudo netstat -tlnp | grep :80
# Or
sudo lsof -i:80
```

If your ASP.NET Core app is running on port 80, stop it first:

```bash
# Find and kill the process
sudo lsof -t -i:80 | xargs sudo kill
# Or if that doesn't work:
sudo killall LschannelFun
```

**5. Run ASP.NET Core app on port 8080**:

The deployment scripts are configured to run the app on port 8080 by default (see deployment instructions above). This allows nginx to bind to port 80 for HTTPS reverse proxy.

```bash
ASPNETCORE_URLS=http://0.0.0.0:8080 ./LschannelFun
```

**Important**: The nginx config files (`nginx-lschannel.fun.conf` and `setup-https.sh`) are already configured to proxy to port 8080. If you use a different port, update the `proxy_pass` line in the nginx config.

**Architecture**:
- Nginx listens on ports 80 (HTTP) and 443 (HTTPS)
- Nginx proxies requests to your ASP.NET Core app on port 8080
- Users access `https://lschannel.fun` → Nginx handles SSL → forwards to app on 8080

**5. Firewall configuration**:

Ensure ports 80 and 443 are open:

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

**6. Auto-renewal** (Let's Encrypt certificates expire every 90 days):

Certbot should set up a systemd timer automatically. Verify:

```bash
sudo systemctl status certbot.timer
```

**Troubleshooting HTTPS issues**:

- Check if Nginx is running: `sudo systemctl status nginx`
- Check Nginx error logs: `sudo tail -f /var/log/nginx/error.log`
- Verify SSL certificate: `sudo certbot certificates`
- Test HTTPS connection: `curl -I https://lschannel.fun`
- Ensure DNS points to your server: `dig lschannel.fun`
