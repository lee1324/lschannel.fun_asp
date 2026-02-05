using Microsoft.AspNetCore.Http.Features;

var builder = WebApplication.CreateBuilder(args);

builder.Services.Configure<FormOptions>(o =>
{
    o.MultipartBodyLengthLimit = 2L * 1024 * 1024 * 1024; // 2 GB
});

var app = builder.Build();

var env = app.Environment;
var webRoot = Path.Combine(env.ContentRootPath, "wwwroot");

// 1) Redirect root and /index to locale
app.Use(async (context, next) =>
{
    var path = (context.Request.Path.Value ?? "").TrimEnd('/');
    var isRoot = path == "" || path == "/" ||
                 path.Equals("/index", StringComparison.OrdinalIgnoreCase) ||
                 path.Equals("/index.html", StringComparison.OrdinalIgnoreCase);
    if (isRoot)
    {
        var preferZh = context.Request.Headers.AcceptLanguage.Any(h =>
            h?.Contains("zh", StringComparison.OrdinalIgnoreCase) == true);
        context.Response.Redirect(preferZh ? "/cn/" : "/en/", permanent: false);
        return;
    }
    await next();
});

// 2) Serve /en/ and /cn/ by returning the index.html file
app.Use(async (context, next) =>
{
    var path = (context.Request.Path.Value ?? "").TrimEnd('/');
    string? filePath = null;
    if (path == "/en")
        filePath = Path.Combine(webRoot, "en", "index.html");
    else if (path == "/cn")
        filePath = Path.Combine(webRoot, "cn", "index.html");

    if (filePath != null && File.Exists(filePath))
    {
        context.Response.ContentType = "text/html; charset=utf-8";
        await context.Response.SendFileAsync(filePath);
        return;
    }
    await next();
});

// 3) Static files (for /images, /multimedia, /en/index.html direct request, etc.)
app.UseStaticFiles();

app.Run();
