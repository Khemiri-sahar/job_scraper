import scrapy
from job_scraper.items import JobItem
from datetime import datetime
import re


class TanitjobsSpider(scrapy.Spider):
    name = "tanitjobs"
    allowed_domains = ["tanitjobs.com", "www.tanitjobs.com"]
    start_urls = ["https://www.tanitjobs.com/jobs"]
    
    # Custom settings to avoid being blocked
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
    }
    
    def parse(self, response):
        """
        Parse the main job listings page
        """
        # Extract all job listings using the actual structure
        job_listings = response.css('article.listing-item')
        
        self.logger.info(f"Found {len(job_listings)} job listings on page")
        
        for job in job_listings:
            # Extract job URL from the link
            job_url = job.css('div.media-right a.link::attr(href)').get()
            
            if job_url:
                # Make URL absolute if it's relative
                job_url = response.urljoin(job_url)
                
                # Extract basic info from listing
                title = job.css('div.media-heading.listing-item__title::text').get()
                date = job.css('div.listing-item__date::text').get()
                
                # Follow the link to get full job details
                yield response.follow(
                    job_url, 
                    callback=self.parse_job_details,
                    meta={'title': title, 'date': date}
                )
        
        # Follow pagination links
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            self.logger.info(f"Following next page: {next_page}")
            yield response.follow(next_page, callback=self.parse)
    
    def parse_job_details(self, response):
        """
        Parse individual job detail page
        """
        item = JobItem()
        
        # Get title from meta or from page
        item['title'] = response.meta.get('title') or response.css('h1::text, h2.job-title::text').get()
        
        # Extract company - look for company name patterns
        item['company'] = response.css('span.company-name::text, div.company::text, a.company-link::text').get()
        
        # Extract location
        item['location'] = response.css('span.location::text, div.location::text, i.fa-map-marker + span::text').get()
        
        # Extract sector/category
        item['sector'] = response.css('span.category::text, div.sector::text, span.job-category::text').get()
        
        # Extract description - get all text from description div
        description_parts = response.css('div.job-description *::text, div.description *::text, div.content-body *::text').getall()
        item['description'] = ' '.join([text.strip() for text in description_parts if text.strip()]).strip()
        
        # Extract salary
        item['salary'] = response.css('span.salary::text, div.salary::text, i.fa-money + span::text').get()
        
        # Extract contract type
        item['contract_type'] = response.css('span.contract-type::text, span.type::text, span.job-type::text').get()
        
        # Get date from meta or from page
        item['posted_date'] = response.meta.get('date') or response.css('span.date::text, time::text, span.posted-date::text').get()
        
        item['source_website'] = "tanitjobs.com"
        item['job_url'] = response.url
        
        # Clean up extracted data
        item = self.clean_item(item)
        
        yield item
    
    def clean_item(self, item):
        """
        Clean and normalize extracted data
        """
        # Strip whitespace from all text fields
        for field in item.fields:
            if item.get(field):
                if isinstance(item[field], str):
                    item[field] = item[field].strip()
                    # Remove multiple spaces and newlines
                    item[field] = ' '.join(item[field].split())
        
        # Clean up date format if needed
        if item.get('posted_date'):
            # Remove extra text like "Publié le" or similar
            date_str = item['posted_date']
            # Try to extract just the date part (dd/mm/yyyy format)
            date_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', date_str)
            if date_match:
                item['posted_date'] = date_match.group()
        
        # Set defaults for empty fields
        if not item.get('title'):
            item['title'] = 'N/A'
        if not item.get('company'):
            item['company'] = 'N/A'
        if not item.get('location'):
            item['location'] = 'Tunisia'
        if not item.get('description'):
            item['description'] = 'No description available'
        if not item.get('posted_date'):
            item['posted_date'] = datetime.now().strftime('%d/%m/%Y')
        
        return item