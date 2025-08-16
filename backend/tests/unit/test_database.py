"""
Unit tests for database endpoints
"""
import pytest


class TestDatabaseEndpoints:
    """Test database management endpoints"""
    
    def test_database_stats_empty(self, client):
        """Test database stats with empty database"""
        response = client.get("/api/database/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["jobs"]["total"] == 0
        assert data["jobs"]["active"] == 0
        assert data["jobs"]["junior_level"] == 0
        assert data["companies"]["total"] == 0
    
    def test_database_stats_with_data(self, client, sample_job):
        """Test database stats with sample data"""
        response = client.get("/api/database/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["jobs"]["total"] == 1
        assert data["jobs"]["active"] == 1
        assert data["jobs"]["junior_level"] == 1
        assert data["companies"]["total"] == 1
        assert data["jobs"]["by_source"]["indeed"] == 1
        assert data["jobs"]["by_source"]["linkedin"] == 0
    
    def test_initialize_database(self, client):
        """Test database initialization endpoint"""
        response = client.post("/api/database/init")
        assert response.status_code == 200
        
        data = response.json()
        assert "Database initialized" in data["message"]
        assert data["companies_created"] == 3
        assert data["jobs_created"] == 2
        
        # Verify data was created
        stats_response = client.get("/api/database/stats")
        stats = stats_response.json()
        assert stats["jobs"]["total"] == 2
        assert stats["companies"]["total"] == 3
    
    def test_initialize_database_already_has_data(self, client, sample_job):
        """Test initialization when database already has data"""
        response = client.post("/api/database/init")
        assert response.status_code == 200
        
        data = response.json()
        assert "already contains data" in data["message"]
        assert data["job_count"] == 1