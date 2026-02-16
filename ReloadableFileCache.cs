using System.Collections.Concurrent;

namespace LschannelFun;

/// <summary>
/// In-memory cache for db.json and key HTML pages. Call InvalidateAll() to force reload from disk on next request.
/// </summary>
public class ReloadableFileCache
{
    private readonly string _webRoot;
    private readonly ConcurrentDictionary<string, (byte[] Content, string ContentType)> _cache = new();

    public ReloadableFileCache(string webRoot)
    {
        _webRoot = webRoot ?? throw new ArgumentNullException(nameof(webRoot));
    }

    /// <summary>
    /// Gets content from cache or loads from disk. relativePath is under wwwroot, e.g. "en/index.html" or "multimedia/lsLearns/en/db.json".
    /// </summary>
    public (byte[] Content, string ContentType)? GetOrLoad(string relativePath)
    {
        var key = relativePath.Replace('\\', '/').TrimStart('/');
        var fullPath = Path.Combine(_webRoot, key);
        if (!File.Exists(fullPath))
            return null;

        return _cache.GetOrAdd(key, _ =>
        {
            var bytes = File.ReadAllBytes(fullPath);
            var contentType = GetContentType(key);
            return (bytes, contentType);
        });
    }

    public void InvalidateAll()
    {
        _cache.Clear();
    }

    private static string GetContentType(string path)
    {
        return Path.GetExtension(path).ToLowerInvariant() switch
        {
            ".json" => "application/json; charset=utf-8",
            ".html" => "text/html; charset=utf-8",
            _ => "application/octet-stream"
        };
    }
}
