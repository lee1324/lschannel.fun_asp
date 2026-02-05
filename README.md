# lschannel.fun (ASP.NET Core)

Port of lschannel.fun from Tomcat/Java to ASP.NET Core.

## Run locally

```bash
cd /Users/ls/Documents/lschannel.fun_asp
dotnet run
```

Then open:
- http://localhost:80 (redirects to /en/ or /cn/ by Accept-Language)
- http://localhost:80/en/
- http://localhost:80/cn/

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
