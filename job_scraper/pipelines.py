import json
import sqlite3
import csv
import re
from datetime import datetime
from itemadapter import ItemAdapter


class JobScraperPipeline:
    """
    Pipeline to store scraped jobs in SQLite database
    """
    
    def __init__(self):
        self.conn = None
        self.cur = None
    
    def open_spider(self, spider):
        """Called when spider opens - create database connection"""
        self.conn = sqlite3.connect('jobs.db')
        self.cur = self.conn.cursor()
        
        # Create table if it doesn't exist
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                company TEXT,
                location TEXT,
                sector TEXT,
                description TEXT,
                salary TEXT,
                contract_type TEXT,
                posted_date TEXT,
                source_website TEXT,
                job_url TEXT UNIQUE,
                scraped_at TEXT
            )
        ''')
        self.conn.commit()
    
    def close_spider(self, spider):
        """Called when spider closes - close database connection"""
        self.conn.close()
    
    def process_item(self, item, spider):
        """Process each scraped item"""
        adapter = ItemAdapter(item)
        
        # Add timestamp when scraped
        adapter['scraped_at'] = datetime.now().isoformat()
        
        try:
            # Insert or ignore if URL already exists (avoid duplicates)
            self.cur.execute('''
                INSERT OR IGNORE INTO jobs (
                    title, company, location, sector, description, 
                    salary, contract_type, posted_date, source_website, 
                    job_url, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                adapter.get('title'),
                adapter.get('company'),
                adapter.get('location'),
                adapter.get('sector'),
                adapter.get('description'),
                adapter.get('salary'),
                adapter.get('contract_type'),
                adapter.get('posted_date'),
                adapter.get('source_website'),
                adapter.get('job_url'),
                adapter.get('scraped_at')
            ))
            self.conn.commit()
            
        except sqlite3.Error as e:
            spider.logger.error(f"Database error: {e}")
        
        return item


class JsonWriterPipeline:
    """
    Pipeline to write scraped items to a JSON file
    """
    
    def open_spider(self, spider):
        self.file = open('jobs.json', 'w', encoding='utf-8')
        self.file.write('[')
        self.first_item = True
    
    def close_spider(self, spider):
        self.file.write(']')
        self.file.close()
    
    def process_item(self, item, spider):
        if not self.first_item:
            self.file.write(',\n')
        else:
            self.first_item = False
        
        line = json.dumps(dict(item), ensure_ascii=False, indent=2)
        self.file.write(line)
        return item


class MLDataCleaningPipeline:
    """
    Pipeline to clean and preprocess data for ML training
    - Normalizes text fields
    - Removes extra whitespace
    - Standardizes formatting
    - Extracts structured information
    """
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Clean text fields
        for field in ['title', 'company', 'location', 'sector', 'description', 'contract_type']:
            if adapter.get(field):
                # Remove extra whitespace
                text = str(adapter[field])
                text = ' '.join(text.split())
                # Remove special characters but keep accents
                text = re.sub(r'[^\w\s\-/.,éèêëàâäôöùûüçîï]', '', text, flags=re.UNICODE)
                adapter[field] = text.strip()
        
        # Normalize location
        if adapter.get('location'):
            location = adapter['location']
            # Common Tunisia locations
            location_map = {
                'Tunis': 'Tunis',
                'Ariana': 'Ariana',
                'Ben Arous': 'Ben Arous',
                'Manouba': 'Manouba',
                'Sfax': 'Sfax',
                'Sousse': 'Sousse',
                'Monastir': 'Monastir',
                'Nabeul': 'Nabeul',
                'Bizerte': 'Bizerte',
            }
            for key, value in location_map.items():
                if key.lower() in location.lower():
                    adapter['location'] = value
                    break
        
        # Normalize contract type
        if adapter.get('contract_type'):
            contract = adapter['contract_type'].upper()
            if 'CDI' in contract:
                adapter['contract_type'] = 'CDI'
            elif 'CDD' in contract:
                adapter['contract_type'] = 'CDD'
            elif 'STAGE' in contract or 'PFE' in contract:
                adapter['contract_type'] = 'Stage/PFE'
            elif 'SIVP' in contract:
                adapter['contract_type'] = 'SIVP'
            elif 'FREELANCE' in contract:
                adapter['contract_type'] = 'Freelance'
        
        # Extract salary information if in description
        if adapter.get('description') and not adapter.get('salary'):
            salary_pattern = r'(\d+)\s*[-à]\s*(\d+)\s*(?:TND|DT|dinars?)'
            match = re.search(salary_pattern, adapter['description'], re.IGNORECASE)
            if match:
                adapter['salary'] = f"{match.group(1)}-{match.group(2)} TND"
        
        return item


class CSVExportPipeline:
    """
    Pipeline to export data to CSV format optimized for ML training
    """
    
    def open_spider(self, spider):
        self.file = open('keejob_ml_dataset.csv', 'w', encoding='utf-8', newline='')
        self.writer = csv.DictWriter(
            self.file,
            fieldnames=[
                'title', 'company', 'location', 'sector', 'description',
                'contract_type', 'salary', 'posted_date', 'job_url', 'source_website'
            ],
            extrasaction='ignore'
        )
        self.writer.writeheader()
        spider.logger.info("✅ CSV file created: keejob_ml_dataset.csv")
    
    def close_spider(self, spider):
        self.file.close()
        spider.logger.info("✅ CSV file closed")
    
    def process_item(self, item, spider):
        self.writer.writerow(ItemAdapter(item).asdict())
        return item