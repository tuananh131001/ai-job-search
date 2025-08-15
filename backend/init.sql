-- Create database if not exists
CREATE DATABASE IF NOT EXISTS job_scraper;
USE job_scraper;

-- Grant privileges to jobuser
GRANT ALL PRIVILEGES ON job_scraper.* TO 'jobuser'@'%';
FLUSH PRIVILEGES;