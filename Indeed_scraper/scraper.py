"""Indeed Job Scraper - Scrapes job listings by position and location, saves to CSV."""

import csv
import logging
import os
import platform
import random
import subprocess
import sys
import time
import zipfile
from typing import List, Dict, Optional
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(message)s")


class IndeedScraper:
    BASE_URL = "https://pk.indeed.com"
    DATE_MAP = {"today": "1", "3days": "3", "7days": "7", "any": ""}

    def __init__(self, position: str, location: str, date_filter: str = "today",
                 use_selenium: bool = False, proxy: Optional[str] = None):
        self.position, self.location, self.date_filter = position, location, date_filter
        self.jobs: List[Dict[str, str]] = []
        self.proxy = proxy
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        })
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.driver = self._init_selenium() if self.use_selenium else None

    def _init_selenium(self):
        opts = Options()
        for arg in ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled", "--log-level=3",
                    "--disable-logging", "--disable-gpu-logging", "--silent", "--disable-extensions"]:
            opts.add_argument(arg)
        opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        opts.add_experimental_option('useAutomationExtension', False)
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if platform.system() == "Windows" and platform.machine().endswith("64"):
            driver_path = self._download_correct_driver()
        else:
            try:
                driver_path = ChromeDriverManager().install()
            except OSError as e:
                if "WinError 193" in str(e) or "not a valid Win32 application" in str(e):
                    logging.warning("Architecture mismatch detected. Downloading correct driver...")
                    driver_path = self._download_correct_driver()
                else:
                    raise
        
        service = Service(driver_path)
        service.log_path = "NUL" if platform.system() == "Windows" else "/dev/null"
        return webdriver.Chrome(service=service, options=opts)
    
    def _download_correct_driver(self) -> str:
        chrome_version = None
        try:
            result = subprocess.run(['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'version' in line.lower():
                        parts = line.split()
                        if len(parts) >= 3:
                            chrome_version = parts[-1]
                            break
        except Exception:
            pass
        
        if not chrome_version:
            try:
                response = requests.get('https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json', timeout=10)
                if response.status_code == 200:
                    chrome_version = response.json()['channels']['Stable']['version']
            except Exception:
                chrome_version = "142.0.7444.162"
        
        driver_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/win64/chromedriver-win64.zip"
        cache_dir = os.path.join(os.path.expanduser("~"), ".wdm", "drivers", "chromedriver", "win64", chrome_version)
        os.makedirs(cache_dir, exist_ok=True)
        driver_path = os.path.join(cache_dir, "chromedriver.exe")
        
        if not os.path.exists(driver_path):
            logging.info(f"Downloading ChromeDriver {chrome_version} for win64...")
            try:
                response = requests.get(driver_url, timeout=30)
                response.raise_for_status()
                zip_path = os.path.join(cache_dir, "chromedriver.zip")
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(cache_dir)
                for root, dirs, files in os.walk(cache_dir):
                    if "chromedriver.exe" in files:
                        extracted_path = os.path.join(root, "chromedriver.exe")
                        if extracted_path != driver_path:
                            if os.path.exists(driver_path):
                                os.remove(driver_path)
                            os.rename(extracted_path, driver_path)
                        break
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                logging.info(f"ChromeDriver downloaded to {driver_path}")
            except Exception as e:
                logging.error(f"Failed to download driver: {e}")
                raise
        return driver_path

    def _build_url(self, start: int = 0) -> str:
        params = {"q": self.position, "l": self.location, "start": start,
                  "fromage": self.DATE_MAP.get(self.date_filter, "")}
        return f"{self.BASE_URL}/jobs?{urlencode({k: v for k, v in params.items() if v})}"

    def _fetch_html(self, url: str) -> Optional[BeautifulSoup]:
        try:
            if self.use_selenium:
                self.driver.get(url)
                time.sleep(random.uniform(3, 5))
                try:
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".job_seen_beacon, [data-jk], .jobCard")))
                except Exception:
                    time.sleep(2)
                for scroll_pos in [("document.body.scrollHeight / 3", 0.5, 1), ("document.body.scrollHeight", 1, 2), ("0", 0.5, 1)]:
                    self.driver.execute_script(f"window.scrollTo(0, {scroll_pos[0]});")
                    time.sleep(random.uniform(scroll_pos[1], scroll_pos[2]))
                return BeautifulSoup(self.driver.page_source, "html.parser")
            time.sleep(random.uniform(2, 4))
            r = self.session.get(url, timeout=15, allow_redirects=True)
            if r.status_code == 403:
                logging.warning("Blocked by Indeed. Try --selenium or proxy.")
                return None
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            logging.error(f"Request failed: {e}")
            return None

    def _parse_jobs(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        if not soup:
            return []
        job_cards = (soup.select(".job_seen_beacon") or soup.select("[data-jk]") or 
                     soup.select("div[data-jk]") or soup.select(".jobCard"))
        jobs = []
        for card in job_cards:
            try:
                title_elem = (card.select_one("h2.jobTitle a") or card.select_one("h2.jobTitle span") or
                              card.select_one("a[data-jk]") or card.select_one("h2 a") or card.select_one("a.jobTitle"))
                if not title_elem:
                    continue
                job_id = card.get("data-jk") or title_elem.get("data-jk") or ""
                job_url = f"{self.BASE_URL}/viewjob?jk={job_id}" if job_id else (urljoin(self.BASE_URL, title_elem.get("href", "")) if title_elem.get("href") else "")
                title = title_elem.get_text(strip=True)
                if not title:
                    continue
                company_elem = (card.select_one(".companyName") or card.select_one("[data-testid='company-name']") or
                                card.select_one(".company_location .companyName"))
                location_elem = (card.select_one(".companyLocation") or card.select_one("[data-testid='text-location']") or
                                 card.select_one(".company_location"))
                date_elem = (card.select_one(".date") or card.select_one(".result-footer .date") or
                             card.select_one("[data-testid='myJobsStateDate']") or card.select_one(".result-link-bar .date") or
                             card.select_one("span.date"))
                summary_elem = (card.select_one(".job-snippet") or card.select_one(".summary") or
                                card.select_one("[data-testid='job-snippet']") or card.select_one(".summary ul") or
                                card.select_one("div.job-snippet"))
                jobs.append({
                    "title": title,
                    "company": company_elem.get_text(strip=True) if company_elem else "N/A",
                    "location": location_elem.get_text(strip=True) if location_elem else "N/A",
                    "date_posted": date_elem.get_text(strip=True) if date_elem else "N/A",
                    "summary": summary_elem.get_text(strip=True, separator=" ") if summary_elem else "N/A",
                    "job_url": job_url
                })
            except Exception as e:
                logging.debug(f"Error parsing job card: {e}")
                continue
        return jobs

    def _filter_relevant_jobs(self, jobs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not jobs:
            return []
        position_keywords = [word.lower() for word in self.position.split() 
                            if word.lower() not in {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"}]
        if not position_keywords:
            return jobs
        logging.info(f"Found {len(jobs)} jobs before filtering. Sample titles:")
        for i, job in enumerate(jobs[:5]):
            logging.info(f"  {i+1}. {job.get('title', 'N/A')} - {job.get('location', 'N/A')}")
        filtered_jobs = []
        location_lower = self.location.lower()
        for job in jobs:
            title_lower = job.get("title", "").lower()
            job_location = job.get("location", "").lower()
            location_match = True
            if self.location and self.location.lower() != "any":
                location_keywords = [kw for kw in location_lower.split() if len(kw) > 2]
                if location_keywords:
                    location_match = any(kw in job_location for kw in location_keywords)
            if len(position_keywords) == 1:
                if position_keywords[0] in title_lower and location_match:
                    filtered_jobs.append(job)
            else:
                primary_keyword = position_keywords[0]
                has_primary = primary_keyword in title_lower
                matches = sum(1 for keyword in position_keywords if keyword in title_lower)
                if (has_primary or matches >= 2) and location_match:
                    filtered_jobs.append(job)
        return filtered_jobs

    def scrape(self, max_pages: int = 3) -> List[Dict[str, str]]:
        logging.info(f"Scraping '{self.position}' in '{self.location}' ({self.date_filter})...")
        for start in range(0, max_pages * 10, 10):
            url = self._build_url(start)
            page_num = start // 10 + 1
            logging.info(f"Fetching page {page_num}...")
            logging.info(f"Search URL: {url}")
            soup = self._fetch_html(url)
            if not soup:
                logging.warning(f"No content received for page {page_num}. Stopping.")
                break
            page_jobs = self._parse_jobs(soup)
            if not page_jobs:
                logging.warning(f"No jobs found on page {page_num}. Stopping.")
                break
            filtered_jobs = self._filter_relevant_jobs(page_jobs)
            if filtered_jobs:
                self.jobs.extend(filtered_jobs)
                logging.info(f"Page {page_num}: +{len(filtered_jobs)} relevant jobs (Total: {len(self.jobs)})")
                if len(filtered_jobs) < len(page_jobs):
                    logging.info(f"  (Filtered out {len(page_jobs) - len(filtered_jobs)} non-matching jobs)")
            else:
                logging.warning(f"No relevant jobs found on page {page_num}. All {len(page_jobs)} jobs were filtered out.")
                break
            if start < (max_pages - 1) * 10:
                time.sleep(random.uniform(3, 6))
        if self.driver:
            self.driver.quit()
        if not self.jobs:
            logging.warning("No jobs found. The site may be blocking requests or the search returned no results.")
        else:
            logging.info(f"Total jobs scraped: {len(self.jobs)}")
        return self.jobs

    def save_to_csv(self, filename: str = "indeed_jobs.csv"):
        if not self.jobs:
            logging.warning("No jobs to save.")
            return
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.jobs[0].keys())
            writer.writeheader()
            writer.writerows(self.jobs)
        logging.info(f"Saved {len(self.jobs)} jobs to {filename}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python scraper.py <position> <location> [date_filter] [--selenium] [--proxy PROXY_URL]")
        sys.exit(1)
    position, location = sys.argv[1], sys.argv[2]
    date_filter = "today"
    use_selenium = "--selenium" in sys.argv
    proxy = None
    if "--proxy" in sys.argv:
        idx = sys.argv.index("--proxy")
        if idx + 1 < len(sys.argv):
            proxy = sys.argv[idx + 1]
    for arg in sys.argv[3:]:
        if arg not in ["--selenium", "--proxy"] and not arg.startswith("http"):
            date_filter = arg
    scraper = IndeedScraper(position, location, date_filter, use_selenium, proxy)
    scraper.scrape()
    scraper.save_to_csv()


if __name__ == "__main__":
    main()
