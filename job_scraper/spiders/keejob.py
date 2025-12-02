import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from job_scraper.items import JobItem
from datetime import datetime
import time


class KeejobSpider(scrapy.Spider):
    """
    Scrapy spider for Keejob using Selenium to handle JavaScript and Cloudflare
    Scrapes ALL pages (76+) from the website
    """
    name = "keejob"
    allowed_domains = ["keejob.com", "www.keejob.com"]
    start_urls = ["https://www.keejob.com/offres-emploi/?page=1"]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,  # Only 1 at a time since we're using Selenium
        'FEED_URI': 'keejob_all_jobs.csv',
    }
    
    # Track current page and max pages
    current_page = 1
    
    def __init__(self, max_pages=80, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow setting max_pages from command line: scrapy crawl keejob -a max_pages=5
        self.max_pages = int(max_pages)
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize driver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Override webdriver detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.logger.info("✅ Selenium WebDriver initialized for Keejob spider")
    
    def parse(self, response):
        """
        Use Selenium to load and parse the page
        Scrapes current page and follows pagination to next page
        """
        self.driver.get(response.url)
        time.sleep(5)  # Wait for page and Cloudflare to load
        
        self.logger.info(f"✅ Page {self.current_page} loaded: {self.driver.title}")
        
        # Wait for job listings to appear
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
            )
        except:
            self.logger.warning(f"⚠️ Timeout waiting for job listings on page {self.current_page}")
            return
        
        # Scroll to load more jobs on the current page
        self.logger.info(f"📜 Scrolling page {self.current_page} to load all jobs...")
        previous_height = 0
        max_scrolls = 5  # Reduced scrolls since we're paginating
        
        for i in range(max_scrolls):
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for new jobs to load
            
            # Calculate new scroll height and compare with previous
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Count current jobs
            current_jobs = len(self.driver.find_elements(By.CSS_SELECTOR, "article"))
            
            # If we've reached the bottom (no new content loaded), stop
            if new_height == previous_height:
                break
            
            previous_height = new_height
        
        # Find all job articles on this page
        job_articles = self.driver.find_elements(By.CSS_SELECTOR, "article")
        self.logger.info(f"📋 Page {self.current_page}: Found {len(job_articles)} job listings")
        
        for idx, article in enumerate(job_articles, 1):
            try:
                item = JobItem()
                
                # Extract job title (h2 tag)
                try:
                    title_elem = article.find_element(By.CSS_SELECTOR, "h2")
                    item['title'] = title_elem.text.strip()
                except:
                    self.logger.warning(f"Job {idx}: No title found, skipping")
                    continue
                
                # Extract company name
                try:
                    company_elem = article.find_element(By.CSS_SELECTOR, "p.text-sm")
                    item['company'] = company_elem.text.strip()
                except:
                    item['company'] = "N/A"
                
                # Extract tags (sector and contract type)
                try:
                    tags = article.find_elements(By.CSS_SELECTOR, "span.inline-flex.items-center")
                    if tags:
                        # First tag is usually sector/industry
                        item['sector'] = tags[0].text.strip() if len(tags) > 0 else None
                        # Second tag is contract type (CDI, CDD, Stage, etc.)
                        item['contract_type'] = tags[1].text.strip() if len(tags) > 1 else None
                except:
                    item['sector'] = None
                    item['contract_type'] = None
                
                # Extract description
                try:
                    desc_elem = article.find_element(By.CSS_SELECTOR, "div.mb-3")
                    item['description'] = desc_elem.text.strip()
                except:
                    item['description'] = "No description available"
                
                # Extract location and date
                try:
                    bottom_info = article.find_element(By.CSS_SELECTOR, "div.flex.flex-wrap.items-center.text-sm")
                    info_text = bottom_info.text
                    item['location'] = info_text.split('•')[0].strip() if '•' in info_text else "Tunisia"
                    item['posted_date'] = info_text.split('•')[1].strip() if '•' in info_text else datetime.now().strftime('%d/%m/%Y')
                except:
                    item['location'] = "Tunisia"
                    item['posted_date'] = datetime.now().strftime('%d/%m/%Y')
                
                # Get job URL
                try:
                    link = article.find_element(By.CSS_SELECTOR, "a")
                    item['job_url'] = link.get_attribute('href')
                except:
                    item['job_url'] = response.url
                
                item['salary'] = None
                item['source_website'] = "keejob.com"
                
                # Clean and yield
                item = self.clean_item(item)
                if item:
                    yield item
                
            except Exception as e:
                self.logger.error(f"Error scraping job {idx}: {e}")
                continue
        
        # Follow pagination to next page
        if self.current_page < self.max_pages:
            self.current_page += 1
            next_url = f"https://www.keejob.com/offres-emploi/?page={self.current_page}"
            self.logger.info(f"🔄 Moving to page {self.current_page}: {next_url}")
            yield scrapy.Request(next_url, callback=self.parse, dont_filter=True)
        else:
            self.logger.info(f"✅ Reached max pages ({self.max_pages}). Scraping complete!")
    
    def clean_item(self, item):
        """Clean and validate item data"""
        # Strip whitespace from all text fields
        for field in item.fields:
            if item.get(field) and isinstance(item[field], str):
                item[field] = ' '.join(item[field].split()).strip()
        
        # Validate required fields
        if not item.get('title'):
            return None
        
        # Set defaults for empty fields
        if not item.get('company'):
            item['company'] = 'N/A'
        if not item.get('location'):
            item['location'] = 'Tunisia'
        if not item.get('description'):
            item['description'] = 'No description available'
        
        return item
    
    def closed(self, reason):
        """Close Selenium driver when spider closes"""
        self.driver.quit()
        self.logger.info("✅ Selenium WebDriver closed")