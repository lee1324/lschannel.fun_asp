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
