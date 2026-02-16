namespace LschannelFun;

/// <summary>
/// Every hour, invalidates the reloadable file cache so db.json and HTML pages are re-read from disk on next request.
/// </summary>
public class ReloadCacheHostedService : BackgroundService
{
    private readonly ReloadableFileCache _cache;
    private readonly ILogger<ReloadCacheHostedService> _logger;
    private static readonly TimeSpan Interval = TimeSpan.FromHours(1);

    public ReloadCacheHostedService(ReloadableFileCache cache, ILogger<ReloadCacheHostedService> logger)
    {
        _cache = cache;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await Task.Delay(Interval, stoppingToken);
        while (!stoppingToken.IsCancellationRequested)
        {
            _cache.InvalidateAll();
            _logger.LogInformation("Reloadable file cache invalidated; db.json and web pages will be reloaded on next request.");
            await Task.Delay(Interval, stoppingToken);
        }
    }
}
