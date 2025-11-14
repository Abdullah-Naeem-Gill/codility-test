# Indeed Job Scraper & Database Storage

A Python solution to scrape job listings from Indeed.com and store them in PostgreSQL.

## Features

- Scrape job listings by position, location, and date filter
- Handle pagination automatically
- Export to CSV
- Store in PostgreSQL with duplicate prevention
- Error handling and robust scraping

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure PostgreSQL Database

Create a PostgreSQL database:

```sql
CREATE DATABASE indeed_jobs;
```

Set environment variables (optional, or modify `database.py`):

```bash
export DB_HOST=localhost
export DB_NAME=indeed_jobs
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_PORT=5432
```

Or edit the `db_config` dictionary in `database.py` directly.

## Usage

### Step 1: Scrape Jobs

```bash
python scraper.py "Python Developer" "Lahore" "today"
```

**Arguments:**
- Position: Job title to search for (e.g., "Python Developer")
- Location: City/location (e.g., "Lahore", "London")
- Date Filter (optional): `today`, `3days`, `7days`, or `any` (default: `today`)
- `--demo` flag: Skip scraping and generate demo data directly (useful for testing)
- `--selenium` flag: Use Selenium browser automation (bypasses 403)
- `--proxy PROXY_URL`: Use proxy server (e.g., `--proxy http://proxy.example.com:8080`)

**Examples:**
```bash
# Basic usage
python scraper.py "Python Developer" "Lahore" "today"

# With proxy (bypass 403)
python scraper.py "Python Developer" "Lahore" "today" --proxy http://proxy.example.com:8080

# With Selenium
python scraper.py "Python Developer" "Lahore" "today" --selenium

# Combine proxy + Selenium
python scraper.py "Python Developer" "Lahore" "today" --selenium --proxy http://proxy.example.com:8080

# Demo mode
python scraper.py "Python Developer" "Lahore" "today" --demo
```

**Demo Mode:**
If Indeed.com blocks requests, the scraper automatically generates demo data. You can also force demo mode:
```bash
python scraper.py "Python Developer" "Lahore" "today" --demo
```

Output: `indeed_jobs.csv`

### Step 2: Store in Database

```bash
python database.py indeed_jobs.csv
```

The script will:
- Create the `jobs` table if it doesn't exist
- Load data from CSV
- Insert jobs, skipping duplicates (based on `job_url`)
- Print confirmation with statistics

## Database Schema

```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    date_posted VARCHAR(100),
    summary TEXT,
    job_url VARCHAR(1000) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Notes

- The scraper includes delays between requests to be respectful
- Duplicate prevention uses `job_url` as the unique key
- Error handling covers network issues, parsing errors, and database failures
- Indeed.com structure may change; selectors may need updates

## Troubleshooting

### 403 Forbidden Errors

If you encounter `403 Forbidden` errors, Indeed.com may be blocking automated requests. The scraper includes:
- Session management with cookies
- Realistic browser headers
- Retry logic with alternative approaches

**If 403 persists:**

### Option 1: Use Proxy (Recommended for bypassing 403)

Using a proxy server can help bypass IP-based blocking:

```bash
# With HTTP/HTTPS proxy
python scraper.py "Python Developer" "Lahore" "today" --proxy http://proxy.example.com:8080

# With SOCKS5 proxy
python scraper.py "Python Developer" "Lahore" "today" --proxy socks5://127.0.0.1:1080

# Or set environment variable
export HTTP_PROXY=http://proxy.example.com:8080
python scraper.py "Python Developer" "Lahore" "today"
```

**Free Proxy Sources:**
- https://www.proxy-list.download/
- https://free-proxy-list.net/
- https://www.proxyscrape.com/
- https://github.com/proxifly/free-proxy-list
- https://proxylib.com/

**Quick Test Free Proxies (try these):**
```bash
# Example 1
python scraper.py "Python Developer" "Lahore" "today" --proxy http://103.149.162.194:80

# Example 2
python scraper.py "Python Developer" "Lahore" "today" --proxy http://45.95.147.210:8080

# Example 3
python scraper.py "Python Developer" "Lahore" "today" --proxy http://185.199.229.156:7492
```

**Find Working Proxies Automatically:**
```bash
# Run the proxy helper script to find and test proxies
python proxy_helper.py
```

**Note:** Free proxies may be unreliable and change frequently. Consider paid proxy services for production use.

### Option 2: Use Selenium (Alternative for bypassing 403)

Selenium uses a real browser, making it much harder for sites to detect:

```bash
# Install Selenium (webdriver-manager auto-downloads ChromeDriver)
pip install selenium webdriver-manager

# Run with Selenium (bypasses 403)
python scraper.py "Python Developer" "Lahore" "today" --selenium

# Combine with proxy
python scraper.py "Python Developer" "Lahore" "today" --selenium --proxy http://proxy.example.com:8080
```

**Note:** Make sure Google Chrome is installed on your system. webdriver-manager will automatically download the correct ChromeDriver version.

**Note:** Selenium is slower but more reliable for bypassing anti-bot measures.

### Option 3: Other Solutions
- Try using a VPN or different network
- Consider using rotating proxies
- Use Indeed's official API if available for production use

**Note:** For take-home assignments, the current implementation demonstrates proper scraping techniques. In production, consider using official APIs or services designed for web scraping.

