using Microsoft.AspNetCore.Http.Features;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

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

// 3) Manager: serve manager.html
app.MapGet("/manager", async (HttpContext context) =>
{
    var managerPath = Path.Combine(webRoot, "manager.html");
    if (File.Exists(managerPath))
    {
        context.Response.ContentType = "text/html; charset=utf-8";
        await context.Response.SendFileAsync(managerPath);
    }
    else
        context.Response.StatusCode = 404;
});

// 4) Manager API: login
app.MapPost("/api/manager/login", async (HttpContext context) =>
{
    var body = await new StreamReader(context.Request.Body).ReadToEndAsync();
    var login = JsonSerializer.Deserialize<JsonElement>(body);
    var username = login.GetProperty("username").GetString();
    var password = login.GetProperty("password").GetString();
    if (username == "ls" && password == "132435")
    {
        var token = Convert.ToBase64String(SHA256.HashData(Encoding.UTF8.GetBytes($"ls:{DateTime.UtcNow:yyyyMMdd}")));
        return Results.Json(new { success = true, token });
    }
    return Results.Json(new { success = false, error = "Invalid credentials" });
});

// 5) Manager API: verify token
app.MapGet("/api/manager/verify", (HttpContext context) =>
{
    var auth = context.Request.Headers.Authorization.ToString();
    if (auth.StartsWith("Bearer "))
    {
        var token = auth.Substring(7);
        var expected = Convert.ToBase64String(SHA256.HashData(Encoding.UTF8.GetBytes($"ls:{DateTime.UtcNow:yyyyMMdd}")));
        return Results.Json(new { valid = token == expected });
    }
    return Results.Json(new { valid = false });
});

// 6) Manager API: refresh data
app.MapPost("/api/manager/refresh/{type}", async (HttpContext context, string type) =>
{
    var auth = context.Request.Headers.Authorization.ToString();
    if (!auth.StartsWith("Bearer "))
        return Results.Json(new { success = false, error = "Unauthorized" }, statusCode: 401);
    var token = auth.Substring(7);
    var expected = Convert.ToBase64String(SHA256.HashData(Encoding.UTF8.GetBytes($"ls:{DateTime.UtcNow:yyyyMMdd}")));
    if (token != expected)
        return Results.Json(new { success = false, error = "Invalid token" }, statusCode: 401);
    try
    {
        if (type == "lsLearns" || type == "music")
        {
            var folder = Path.Combine(webRoot, "multimedia", type);
            var videosDir = Path.Combine(folder, "videos");
            var dbPath = Path.Combine(folder, "db.json");
            if (!Directory.Exists(videosDir))
                return Results.Json(new { success = false, error = "Videos folder not found" });
            var existingDb = new Dictionary<string, JsonElement>();
            if (File.Exists(dbPath))
            {
                try
                {
                    var existingJson = await File.ReadAllTextAsync(dbPath);
                    var existing = JsonSerializer.Deserialize<JsonElement>(existingJson);
                    if (existing.TryGetProperty("list", out var listProp))
                        foreach (var item in listProp.EnumerateArray())
                            if (item.TryGetProperty("filename", out var fn))
                                existingDb[fn.GetString() ?? ""] = item;
                }
                catch { }
            }
            var list = new List<object>();
            foreach (var mp4 in Directory.GetFiles(videosDir, "*.MP4").Concat(Directory.GetFiles(videosDir, "*.mp4")).OrderBy(f => f))
            {
                var fi = new FileInfo(mp4);
                var filename = fi.Name;
                var title = Path.GetFileNameWithoutExtension(filename);
                var durationSec = 0;
                var durationDisplay = "00:00";
                if (existingDb.TryGetValue(filename, out var existing))
                {
                    if (existing.TryGetProperty("durationInSeconds", out var ds) && int.TryParse(ds.GetString(), out var sec))
                        durationSec = sec;
                    if (existing.TryGetProperty("durationDisplay", out var dd))
                        durationDisplay = dd.GetString() ?? "00:00";
                    if (existing.TryGetProperty("title", out var t))
                        title = t.GetString() ?? title;
                }
                else
                {
                    try
                    {
                        using var proc = System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                        {
                            FileName = "ffprobe",
                            Arguments = $"-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{mp4}\"",
                            RedirectStandardOutput = true,
                            UseShellExecute = false
                        });
                        if (proc != null)
                        {
                            var output = await proc.StandardOutput.ReadToEndAsync();
                            await proc.WaitForExitAsync();
                            if (proc.ExitCode == 0 && double.TryParse(output.Trim(), out var sec))
                            {
                                durationSec = (int)Math.Round(sec);
                                var m = durationSec / 60;
                                var s = durationSec % 60;
                                durationDisplay = $"{m:D2}:{s:D2}";
                            }
                        }
                    }
                    catch { }
                }
                list.Add(new { filename, title, durationInSeconds = durationSec.ToString(), durationDisplay });
            }
            var db = new { notes = "title and filename are different, because title could contain newlines while filename does not, and filename contains postfix but title does not", hints = "display durationInSeconds in format of xx:xx, like 90secs should be displayed as 01:30", list };
            await File.WriteAllTextAsync(dbPath, JsonSerializer.Serialize(db, new JsonSerializerOptions { WriteIndented = true, Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping }));
            return Results.Json(new { success = true, message = $"Refreshed {list.Count} entries" });
        }
        else if (type == "downloads")
        {
            var downloadsDir = Path.Combine(webRoot, "multimedia", "downloads");
            var dbPath = Path.Combine(downloadsDir, "db.json");
            if (!Directory.Exists(downloadsDir))
                return Results.Json(new { success = false, error = "Downloads folder not found" });
            var list = new List<object>();
            foreach (var file in Directory.GetFiles(downloadsDir).Where(f => !Path.GetFileName(f).StartsWith(".")).OrderBy(f => f))
            {
                var fi = new FileInfo(file);
                var sizeMB = (fi.Length / (1024.0 * 1024.0)).ToString("F2");
                list.Add(new { filename = fi.Name, sizeMB });
            }
            var db = new { notes = "Downloads folder - files available for download", list };
            await File.WriteAllTextAsync(dbPath, JsonSerializer.Serialize(db, new JsonSerializerOptions { WriteIndented = true }));
            return Results.Json(new { success = true, message = $"Refreshed {list.Count} entries" });
        }
        return Results.Json(new { success = false, error = "Unknown type" });
    }
    catch (Exception ex)
    {
        return Results.Json(new { success = false, error = ex.Message });
    }
});

// 7) API: list files in multimedia/downloads for the Download tab
app.MapGet("/api/downloads", () =>
{
    var downloadsDir = Path.Combine(webRoot, "multimedia", "downloads");
    if (!Directory.Exists(downloadsDir))
        return Results.Json(Array.Empty<object>());
    var files = Directory.GetFiles(downloadsDir)
        .Select(f => new FileInfo(f))
        .Where(fi => !fi.Name.StartsWith(".", StringComparison.Ordinal))
        .OrderBy(fi => fi.Name)
        .Select(fi => new { name = fi.Name, size = fi.Length })
        .ToArray();
    return Results.Json(files);
});

// 4) Static files (for /images, /multimedia, /en/index.html direct request, etc.)
app.UseStaticFiles();

app.Run();
