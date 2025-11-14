"""Database script to load scraped job data from CSV into PostgreSQL."""

import csv
import os
import sys
import psycopg2
from psycopg2.extras import execute_values


class JobDatabase:
    def __init__(self, db_config):
        self.config = db_config
        self.conn = None
        self.cursor = None
    
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.config['host'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                port=self.config.get('port', 5432)
            )
            self.cursor = self.conn.cursor()
            print("Successfully connected to PostgreSQL database.")
            return True
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            company VARCHAR(255) NOT NULL,
            location VARCHAR(255),
            date_posted VARCHAR(100),
            summary TEXT,
            job_url VARCHAR(1000) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(title, company)
        );
        CREATE INDEX IF NOT EXISTS idx_job_url ON jobs(job_url);
        CREATE INDEX IF NOT EXISTS idx_title_company ON jobs(title, company);
        """
        try:
            self.cursor.execute(create_table_query)
            self.conn.commit()
            print("Jobs table created/verified successfully.")
            return True
        except psycopg2.Error as e:
            print(f"Error creating table: {e}")
            self.conn.rollback()
            return False
    
    def load_from_csv(self, csv_file='indeed_jobs.csv'):
        if not os.path.exists(csv_file):
            print(f"Error: CSV file '{csv_file}' not found.")
            return []
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                jobs = [{k: row.get(k, '').strip() for k in ['title', 'company', 'location', 'date_posted', 'summary', 'job_url']}
                        for row in csv.DictReader(file)]
            print(f"Loaded {len(jobs)} jobs from {csv_file}")
            return jobs
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return []
    
    def insert_jobs(self, jobs):
        if not jobs:
            print("No jobs to insert.")
            return 0
        insert_query = """INSERT INTO jobs (title, company, location, date_posted, summary, job_url)
                          VALUES %s ON CONFLICT (job_url) DO NOTHING"""
        try:
            values = [(job['title'], job['company'], job['location'], job['date_posted'], job['summary'], job['job_url'])
                      for job in jobs if job.get('job_url') and job['job_url'].strip()]
            if not values:
                print("No valid jobs with URLs to insert.")
                return 0
            try:
                execute_values(self.cursor, insert_query, values, template=None, page_size=100)
                inserted_count = self.cursor.rowcount
                self.conn.commit()
            except psycopg2.IntegrityError:
                self.conn.rollback()
                inserted_count = 0
                for value in values:
                    try:
                        self.cursor.execute("INSERT INTO jobs (title, company, location, date_posted, summary, job_url) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (job_url) DO NOTHING", value)
                        if self.cursor.rowcount > 0:
                            inserted_count += 1
                    except psycopg2.IntegrityError:
                        continue
                self.conn.commit()
            skipped_count = len(values) - inserted_count
            print(f"Successfully inserted {inserted_count} new jobs.")
            if skipped_count > 0:
                print(f"Skipped {skipped_count} duplicate jobs (based on job_url).")
            return inserted_count
        except psycopg2.Error as e:
            print(f"Error inserting jobs: {e}")
            self.conn.rollback()
            return 0
    
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed.")


def main():
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'indeed_jobs'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'abdullah420'),
        'port': int(os.getenv('DB_PORT', 5432))
    }
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'indeed_jobs.csv'
    db = JobDatabase(db_config)
    if not db.connect():
        print("Failed to connect to database. Please check your configuration.")
        sys.exit(1)
    try:
        if not db.create_table():
            print("Failed to create table.")
            sys.exit(1)
        jobs = db.load_from_csv(csv_file)
        if not jobs:
            print("No jobs found in CSV file.")
            sys.exit(1)
        inserted = db.insert_jobs(jobs)
        if inserted > 0:
            print(f"\n✓ Data storage completed successfully!")
            print(f"  Total jobs processed: {len(jobs)}")
            print(f"  New jobs inserted: {inserted}")
        else:
            print("\nNo new jobs were inserted (all may be duplicates).")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
