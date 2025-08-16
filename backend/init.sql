-- Initialize database schema for Job Scraper
-- Focus: Marketing Junior positions

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS job_scraper CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE job_scraper;

-- Grant privileges to jobuser
GRANT ALL PRIVILEGES ON job_scraper.* TO 'jobuser'@'%';
FLUSH PRIVILEGES;

-- Create companies table
CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    website VARCHAR(500),
    industry VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_companies_name (name),
    INDEX idx_companies_industry (industry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    company_id INT,
    description TEXT NOT NULL,
    location VARCHAR(255),
    url VARCHAR(767) UNIQUE NOT NULL,
    source ENUM('indeed', 'linkedin') NOT NULL,
    job_type ENUM('full-time', 'part-time', 'contract', 'internship'),
    experience_level ENUM('entry', 'junior', 'mid', 'senior'),
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    salary_currency VARCHAR(3) DEFAULT 'VND',
    posted_date DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
    INDEX idx_jobs_experience (experience_level),
    INDEX idx_jobs_title (title),
    INDEX idx_jobs_posted_date (posted_date DESC),
    INDEX idx_jobs_company (company_id),
    INDEX idx_jobs_active (is_active),
    INDEX idx_jobs_location (location),
    INDEX idx_jobs_source (source),
    FULLTEXT idx_jobs_search (title, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;