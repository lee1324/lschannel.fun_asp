# lschannel.fun (ASP.NET Core)

Port of lschannel.fun from Tomcat/Java to ASP.NET Core.

## Run locally

```bash
cd /Users/ls/Documents/lschannel.fun_asp
dotnet run
```

Then open:
- http://localhost:80 or https://localhost:443 (redirects to /en/ or /cn/ by Accept-Language)
- http://localhost:80/en/ or https://localhost:443/en/
- http://localhost:80/cn/ or https://localhost:443/cn/

HTTPS uses the ASP.NET Core dev certificate. Trust it once with:
`dotnet dev-certs https --trust`

Binding to port 443 (and 80) on macOS/Linux often requires elevated privileges (e.g. `sudo dotnet run`).

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
ASPNETCORE_URLS=http://0.0.0.0:80 ./LschannelFun
```

Or with a specific port: `ASPNETCORE_URLS=http://0.0.0.0:8080 ./LschannelFun`

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

**Option A: Use the setup script** (easiest):

```bash
scp setup-https.sh user@server:/tmp/
ssh user@server
chmod +x /tmp/setup-https.sh
sudo /tmp/setup-https.sh
```

**Option B: Manual configuration**:

Copy `nginx-lschannel.fun.conf` to your server:

```bash
scp nginx-lschannel.fun.conf user@server:/tmp/
ssh user@server
sudo cp /tmp/nginx-lschannel.fun.conf /etc/nginx/sites-available/lschannel.fun
sudo ln -s /etc/nginx/sites-available/lschannel.fun /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

**Note**: The nginx config file only includes `lschannel.fun` (without www). If you want to support `www.lschannel.fun`, first add a DNS A record for it, then update the `server_name` directives in the nginx config to include `www.lschannel.fun`.

**4. Ensure ASP.NET Core app is running on HTTP (port 80)**:

The app should run on HTTP (port 80) as shown in the deployment instructions. Nginx will handle HTTPS (port 443) and proxy requests to the app.

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
