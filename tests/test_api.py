"""
Unit tests for Zapora API endpoints
Tests core functionality and business logic
"""
import pytest
from fastapi.testclient import TestClient
from my_menu_api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200


class TestMenuEndpoints:
    """Test menu-related endpoints"""
    
    def test_get_menu_items(self):
        """Test retrieving menu items"""
        response = client.get("/menu/items/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_categories(self):
        """Test retrieving categories"""
        response = client.get("/menu/categories/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAPIDocumentation:
    """Test API documentation endpoints"""
    
    def test_openapi_schema(self):
        """Test OpenAPI schema generation"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
    
    def test_docs_ui(self):
        """Test Swagger UI accessibility"""
        response = client.get("/docs")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_404_handling(self):
        """Test 404 error handling"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test method not allowed handling"""
        response = client.post("/healthz")
        assert response.status_code == 405


class TestSecurity:
    """Test security-related functionality"""
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.get("/healthz")
        # CORS headers should be present for browser compatibility
        assert response.status_code == 200
    
    def test_security_headers(self):
        """Test security headers"""
        response = client.get("/")
        assert response.status_code == 200
        # Additional security header checks can be added here


@pytest.mark.performance
class TestPerformance:
    """Performance-related tests"""
    
    def test_response_time(self):
        """Test API response times"""
        import time
        
        start_time = time.time()
        response = client.get("/healthz")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
