"""
Unit tests for health check endpoints
"""
import pytest
from datetime import datetime


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client):
        """Test basic health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "job-scraper-api"
    
    def test_database_health_check(self, client):
        """Test database health check endpoint"""
        response = client.get("/api/health/db")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "timestamp" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "Welcome to Job Scraper API" in data["message"]
        assert data["version"] == "0.1.0"
        assert data["docs"] == "/docs"
        assert data["health"] == "/api/health"
        assert data["database_stats"] == "/api/database/stats"