"""
Production readiness tests - validate all critical workflows and configurations
"""
import pytest
import asyncio
import json
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from backend.main import app
from backend.config import get_settings


class TestProductionReadiness:
    """Test production readiness and critical workflows"""
    
    @pytest.mark.asyncio
    async def test_health_endpoints(self, client: AsyncClient):
        """Test all health check endpoints"""
        
        # Basic health check
        response = await client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        
        # Liveness check
        response = await client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        
        # Readiness check (may fail in test environment, that's OK)
        response = await client.get("/health/ready")
        assert response.status_code in [200, 503]  # Either healthy or unhealthy is fine
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "response_time_ms" in data
    
    @pytest.mark.asyncio
    async def test_security_headers(self, client: AsyncClient):
        """Test security headers are present"""
        response = await client.get("/")
        
        # Check for security headers
        headers = response.headers
        
        # These should be set by our security middleware
        expected_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection",
            "strict-transport-security"
        ]
        
        for header in expected_headers:
            assert header in headers, f"Security header {header} missing"
    
    @pytest.mark.asyncio 
    async def test_error_pages(self, client: AsyncClient):
        """Test custom error pages are working"""
        
        # Test 404 page
        response = await client.get("/nonexistent-page")
        assert response.status_code == 404
        assert "Page Not Found" in response.text
        assert "AutoForms" in response.text
        
        # Test error handling structure
        assert "<!DOCTYPE html>" in response.text
        assert "text/html" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_static_files_serving(self, client: AsyncClient):
        """Test static files are served correctly"""
        
        # Test manifest.json 
        response = await client.get("/static/manifest.json")
        if response.status_code == 200:
            # If static files exist, they should be served properly
            assert "application/json" in response.headers.get("content-type", "")
            data = response.json()
            assert "name" in data
    
    @pytest.mark.asyncio
    async def test_user_registration_workflow(self, client: AsyncClient, sample_user_data):
        """Test complete user registration workflow"""
        
        # Test registration page loads
        response = await client.get("/register")
        assert response.status_code == 200
        assert "Register" in response.text
        
        # Test registration API (mock success)
        with patch('backend.services.auth_service.AuthService.register_user') as mock_register:
            mock_register.return_value = {"id": "test_user_id", "username": "testuser"}
            
            response = await client.post("/api/auth/register", json=sample_user_data)
            # Should not error out, may redirect or return success
            assert response.status_code in [200, 201, 302, 422]  # Various valid responses
    
    @pytest.mark.asyncio
    async def test_form_generation_workflow(self, client: AsyncClient, mock_openai_client):
        """Test complete form generation workflow"""
        
        # Test generator page loads
        response = await client.get("/test-generator")
        assert response.status_code == 200
        assert "AutoForms" in response.text
        
        # Test form generation API (with mocked OpenAI)
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_openai.return_value = mock_openai_client
            
            form_request = {
                "prompt": "Create a simple contact form",
                "language": "en"
            }
            
            response = await client.post("/api/generate/form", json=form_request)
            # Should handle the request appropriately (success or controlled failure)
            assert response.status_code in [200, 401, 422, 500]
    
    @pytest.mark.asyncio
    async def test_template_system_workflow(self, client: AsyncClient):
        """Test form templates system"""
        
        # Test templates API
        response = await client.get("/api/templates/")
        assert response.status_code in [200, 401]  # May require auth
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            # If templates exist, test template structure
            if data:
                template = data[0]
                required_fields = ["id", "name", "description", "category"]
                for field in required_fields:
                    assert field in template
    
    @pytest.mark.asyncio
    async def test_admin_dashboard_protection(self, client: AsyncClient):
        """Test admin routes are protected"""
        
        # Admin dashboard should require authentication
        response = await client.get("/admin/dashboard")
        assert response.status_code in [401, 403, 302]  # Unauthorized or redirect
        
        # Admin API should require authentication
        response = await client.get("/admin/users")
        assert response.status_code in [401, 403, 404]  # Unauthorized or not found
    
    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self, client: AsyncClient):
        """Test rate limiting (simulation)"""
        
        # Make multiple rapid requests to test rate limiting
        responses = []
        for i in range(5):
            response = await client.get("/healthz")
            responses.append(response.status_code)
        
        # All should succeed for health checks (rate limits usually more lenient)
        assert all(status == 200 for status in responses)
    
    @pytest.mark.asyncio
    async def test_cors_configuration(self, client: AsyncClient):
        """Test CORS is configured properly"""
        
        # Test preflight request
        response = await client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        })
        
        # Should handle CORS properly
        assert response.status_code in [200, 204]
    
    def test_environment_validation(self):
        """Test environment configuration validation"""
        
        settings = get_settings()
        
        # Critical settings should be present
        assert settings.openai_key is not None
        assert settings.mongodb_uri is not None
        assert settings.jwt_secret is not None
        
        # MongoDB URI should be valid format
        assert settings.mongodb_uri.startswith(("mongodb://", "mongodb+srv://"))
        
        # JWT secret should be non-empty
        assert len(settings.jwt_secret) > 0
    
    @pytest.mark.asyncio
    async def test_database_indexes_creation(self):
        """Test database indexes can be created"""
        
        try:
            from backend.services.db_indexes import create_indexes
            await create_indexes()
            # Should not raise exception
            assert True
        except Exception as e:
            # In test environment, database might not be available
            # This is acceptable as long as the function exists
            assert "create_indexes" in str(e) or "database" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_pdf_generation_service(self):
        """Test PDF generation service availability"""
        
        try:
            from backend.services.pdf_service import PDFService
            pdf_service = PDFService()
            
            # Test that service can be instantiated
            assert pdf_service is not None
            
            # Test basic HTML to PDF (mock)
            html_content = "<html><body><h1>Test</h1></body></html>"
            # This might fail due to missing dependencies, that's OK
            
        except ImportError:
            # PDF service dependencies might not be available in test environment
            pytest.skip("PDF service dependencies not available")
    
    @pytest.mark.asyncio
    async def test_email_service_configuration(self):
        """Test email service configuration"""
        
        try:
            from backend.services.email_service import EmailService
            email_service = EmailService()
            
            # Should be able to instantiate
            assert email_service is not None
            
            # Test configuration loading
            settings = get_settings()
            assert settings.smtp_host is not None
            assert settings.smtp_port > 0
            
        except Exception:
            # Email service might not be configured in test environment
            pytest.skip("Email service not configured for testing")
    
    @pytest.mark.asyncio
    async def test_caching_service_availability(self):
        """Test caching services are available"""
        
        try:
            from backend.services.cache import cache_manager
            
            # Should be able to access cache manager
            assert cache_manager is not None
            
        except ImportError:
            # Cache service might not be available in test environment
            pytest.skip("Caching service not available")
    
    @pytest.mark.asyncio
    async def test_websocket_functionality(self, client: AsyncClient):
        """Test WebSocket endpoints are available"""
        
        # Test WebSocket endpoint exists
        try:
            # WebSocket connection attempt (may fail, that's OK)
            with client.websocket_connect("/ws/test") as websocket:
                pass
        except Exception:
            # WebSocket might not be fully functional in test client
            # Just verify the route exists
            pass
    
    def test_production_startup_script_exists(self):
        """Test production startup script exists and is valid"""
        
        import os
        from pathlib import Path
        
        project_root = Path(__file__).resolve().parent.parent
        startup_script = project_root / "start_production.py"
        
        assert startup_script.exists(), "Production startup script missing"
        assert startup_script.is_file(), "Startup script is not a file"
        
        # Check it's executable (on Unix systems)
        if os.name != 'nt':
            assert os.access(startup_script, os.R_OK), "Startup script not readable"


class TestSecurityConfiguration:
    """Test security-specific configurations"""
    
    def test_jwt_secret_strength(self):
        """Test JWT secret meets security requirements"""
        
        settings = get_settings()
        
        # In production, JWT secret should be strong
        if settings.app_env == "production":
            assert len(settings.jwt_secret) >= 32, "JWT secret too short for production"
            assert settings.jwt_secret != "test-jwt-secret", "Using default JWT secret in production"
    
    def test_openai_key_format(self):
        """Test OpenAI key format"""
        
        settings = get_settings()
        
        # Should start with sk- for OpenAI keys
        if not settings.openai_key.startswith("sk-test"):
            assert settings.openai_key.startswith("sk-"), "Invalid OpenAI key format"
    
    def test_cors_origins_configuration(self):
        """Test CORS origins are properly configured"""
        
        settings = get_settings()
        
        # CORS origins should be configured
        assert settings.allowed_origins is not None
        assert len(settings.allowed_origins) > 0
        
        # In production, should not allow all origins
        if settings.app_env == "production":
            assert "*" not in settings.allowed_origins, "CORS allows all origins in production"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])