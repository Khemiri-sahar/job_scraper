BOT_NAME = "job_scraper"

SPIDER_MODULES = ["job_scraper.spiders"]
NEWSPIDER_MODULE = "job_scraper.spiders"

ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 16

# Configure a delay for requests 
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True 
CONCURRENT_REQUESTS_PER_DOMAIN = 4


# Disable cookies 
COOKIES_ENABLED = True

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    "job_scraper.middlewares.JobScraperSpiderMiddleware": 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "job_scraper.middlewares.JobScraperDownloaderMiddleware": 543,
}

# Configure item pipelines (lower numbers = higher priority)
ITEM_PIPELINES = {
    "job_scraper.pipelines.MLDataCleaningPipeline": 100,  # Clean data first
    "job_scraper.pipelines.JobScraperPipeline": 200,      # Save to database
    "job_scraper.pipelines.CSVExportPipeline": 300,       # Export to CSV for ML
    # "job_scraper.pipelines.JsonWriterPipeline": 400,    # Optional JSON export
}

# Enable and configure the AutoThrottle extension 
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 3
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"