"""
Integration tests for API endpoints
"""
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from fastapi import status


class TestAuthenticationEndpoints:
    """Test authentication-related endpoints"""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient, sample_user_data):
        """Test successful user registration"""
        response = await client.post("/register", data=sample_user_data)
        assert response.status_code == status.HTTP_200_OK
        # Check that user was created in the mocked database
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client: AsyncClient, sample_user_data, mock_db):
        """Test registration with duplicate email"""
        # First registration
        await client.post("/register", data=sample_user_data)
        
        # Second registration with same email should fail
        response = await client.post("/register", data=sample_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, sample_user_data, mock_db):
        """Test successful login"""
        # Register user first
        await client.post("/register", data=sample_user_data)
        
        # Test login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = await client.post("/login", data=login_data)
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials"""
        login_data = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        response = await client.post("/login", data=login_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_forgot_password_success(self, client: AsyncClient, sample_user_data, mock_db):
        """Test forgot password functionality"""
        # Register user first
        await client.post("/register", data=sample_user_data)
        
        # Test forgot password
        response = await client.post("/forgot-password", data={"email": sample_user_data["email"]})
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_forgot_password_invalid_email(self, client: AsyncClient):
        """Test forgot password with invalid email"""
        response = await client.post("/forgot-password", data={"email": "invalid@example.com"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestFormGenerationEndpoints:
    """Test form generation endpoints"""
    
    @pytest.mark.asyncio
    async def test_demo_generate_success(self, client: AsyncClient):
        """Test demo form generation"""
        with patch('backend.services.form_generator.generate_html_only') as mock_generate:
            mock_generate.return_value = "<html><body><h1>Test Form</h1></body></html>"
            
            response = await client.post("/api/demo-generate", data={"prompt": "Create a contact form"})
            assert response.status_code == status.HTTP_200_OK
            assert "Test Form" in response.text
    
    @pytest.mark.asyncio
    async def test_demo_generate_hebrew_request(self, client: AsyncClient):
        """Test demo generation with Hebrew request"""
        with patch('backend.services.form_generator.generate_html_only') as mock_generate:
            mock_generate.return_value = "<html><body><div>שיר אהבה</div></body></html>"
            
            response = await client.post("/api/demo-generate", data={"prompt": "כתוב שיר אהבה"})
            assert response.status_code == status.HTTP_200_OK
            assert "שיר אהבה" in response.text
    
    @pytest.mark.asyncio
    async def test_demo_generate_empty_prompt(self, client: AsyncClient):
        """Test demo generation with empty prompt"""
        response = await client.post("/api/demo-generate", data={"prompt": ""})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_generate_authenticated_user(self, client: AsyncClient, auth_headers):
        """Test form generation for authenticated user"""
        with patch('backend.services.form_generator.generate_html_only') as mock_generate:
            with patch('backend.deps.get_current_user') as mock_user:
                mock_user.return_value = {"id": "user123", "email": "test@example.com"}
                mock_generate.return_value = "<html><body><h1>User Form</h1></body></html>"
                
                response = await client.post(
                    "/api/generate",
                    data={"prompt": "Create a registration form"},
                    headers=auth_headers()
                )
                assert response.status_code == status.HTTP_200_OK
                assert "User Form" in response.text
    
    @pytest.mark.asyncio
    async def test_generate_unauthenticated_user(self, client: AsyncClient):
        """Test form generation for unauthenticated user"""
        response = await client.post("/api/generate", data={"prompt": "Create a form"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestFormManagementEndpoints:
    """Test form management endpoints"""
    
    @pytest.mark.asyncio
    async def test_save_form_success(self, client: AsyncClient, auth_headers, sample_form_data):
        """Test saving a form"""
        with patch('backend.deps.get_current_user') as mock_user:
            mock_user.return_value = {"id": "user123", "email": "test@example.com"}
            
            response = await client.post(
                "/api/save-form",
                data=sample_form_data,
                headers=auth_headers()
            )
            assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_get_user_forms(self, client: AsyncClient, auth_headers, mock_db):
        """Test retrieving user forms"""
        with patch('backend.deps.get_current_user') as mock_user:
            mock_user.return_value = {"id": "user123", "email": "test@example.com"}
            
            # Mock some forms in the database
            mock_db.forms.find.return_value.to_list = MagicMock(return_value=[
                {"title": "Form 1", "html": "<html>Form 1</html>"},
                {"title": "Form 2", "html": "<html>Form 2</html>"}
            ])
            
            response = await client.get("/api/forms", headers=auth_headers())
            assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_delete_form_success(self, client: AsyncClient, auth_headers):
        """Test deleting a form"""
        with patch('backend.deps.get_current_user') as mock_user:
            mock_user.return_value = {"id": "user123", "email": "test@example.com"}
            
            form_id = "507f1f77bcf86cd799439011"
            response = await client.delete(f"/api/forms/{form_id}", headers=auth_headers())
            assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_get_form_by_id(self, client: AsyncClient, auth_headers, mock_db):
        """Test retrieving a specific form"""
        with patch('backend.deps.get_current_user') as mock_user:
            mock_user.return_value = {"id": "user123", "email": "test@example.com"}
            
            form_id = "507f1f77bcf86cd799439011"
            mock_db.forms.find_one.return_value = {
                "_id": form_id,
                "title": "Test Form",
                "html": "<html>Test</html>",
                "user_id": "user123"
            }
            
            response = await client.get(f"/api/forms/{form_id}", headers=auth_headers())
            assert response.status_code == status.HTTP_200_OK


class TestDownloadEndpoints:
    """Test download functionality endpoints"""
    
    @pytest.mark.asyncio
    async def test_download_pdf_success(self, client: AsyncClient):
        """Test PDF download success"""
        with patch('backend.services.pdf_service.html_to_pdf_file') as mock_pdf:
            mock_pdf.return_value = "/tmp/test.pdf"
            
            with patch('fastapi.responses.FileResponse') as mock_file_response:
                mock_file_response.return_value = MagicMock()
                
                response = await client.post(
                    "/api/download-pdf",
                    data={
                        "html": "<html><body>Test content</body></html>",
                        "title": "Test Form"
                    }
                )
                assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_download_pdf_fallback_to_text(self, client: AsyncClient):
        """Test PDF download fallback to text"""
        with patch('backend.services.pdf_service.html_to_pdf_file') as mock_pdf:
            mock_pdf.side_effect = ImportError("WeasyPrint not installed")
            
            with patch('backend.services.pdf_service.html_to_text_file') as mock_text:
                mock_text.return_value = "/tmp/test.txt"
                
                with patch('fastapi.responses.FileResponse') as mock_file_response:
                    mock_file_response.return_value = MagicMock()
                    
                    response = await client.post(
                        "/api/download-pdf",
                        data={
                            "html": "<html><body>Test content</body></html>",
                            "title": "Test Form"
                        }
                    )
                    assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_download_text_success(self, client: AsyncClient):
        """Test text download success"""
        with patch('backend.services.pdf_service.html_to_text_file') as mock_text:
            mock_text.return_value = "/tmp/test.txt"
            
            with patch('fastapi.responses.FileResponse') as mock_file_response:
                mock_file_response.return_value = MagicMock()
                
                response = await client.post(
                    "/api/download-text",
                    data={
                        "html": "<html><body>Test content</body></html>",
                        "title": "Test Content"
                    }
                )
                assert response.status_code == status.HTTP_200_OK


class TestChatEndpoints:
    """Test chat functionality endpoints"""
    
    @pytest.mark.asyncio
    async def test_chat_with_form_success(self, client: AsyncClient, auth_headers):
        """Test chat with form functionality"""
        with patch('backend.deps.get_current_user') as mock_user:
            with patch('backend.services.form_generator.chat_with_gpt') as mock_chat:
                mock_user.return_value = {"id": "user123", "email": "test@example.com"}
                mock_chat.return_value = "<html><body><h1>Updated Form</h1></body></html>"
                
                form_id = "507f1f77bcf86cd799439011"
                response = await client.post(
                    f"/api/forms/{form_id}/chat",
                    data={
                        "question": "Add a phone number field",
                        "html": "<html><body><h1>Original Form</h1></body></html>"
                    },
                    headers=auth_headers()
                )
                assert response.status_code == status.HTTP_200_OK
                assert "Updated Form" in response.text
    
    @pytest.mark.asyncio
    async def test_chat_with_form_timeout(self, client: AsyncClient, auth_headers):
        """Test chat with form timeout handling"""
        with patch('backend.deps.get_current_user') as mock_user:
            with patch('backend.services.form_generator.chat_with_gpt') as mock_chat:
                mock_user.return_value = {"id": "user123", "email": "test@example.com"}
                mock_chat.return_value = "<p style='color: red;'>⏱️ Chat request timed out.</p>"
                
                form_id = "507f1f77bcf86cd799439011"
                response = await client.post(
                    f"/api/forms/{form_id}/chat",
                    data={
                        "question": "Add a complex feature",
                        "html": "<html><body><h1>Form</h1></body></html>"
                    },
                    headers=auth_headers()
                )
                assert response.status_code == status.HTTP_200_OK
                assert "timed out" in response.text


class TestErrorHandling:
    """Test error handling across endpoints"""
    
    @pytest.mark.asyncio
    async def test_invalid_form_id(self, client: AsyncClient, auth_headers):
        """Test handling of invalid form ID"""
        with patch('backend.deps.get_current_user') as mock_user:
            mock_user.return_value = {"id": "user123", "email": "test@example.com"}
            
            response = await client.get("/api/forms/invalid_id", headers=auth_headers())
            assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient):
        """Test handling of missing required fields"""
        response = await client.post("/api/demo-generate", data={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, client: AsyncClient, auth_headers):
        """Test handling of database connection errors"""
        with patch('backend.deps.get_current_user') as mock_user:
            with patch('backend.deps.get_db') as mock_db:
                mock_user.return_value = {"id": "user123", "email": "test@example.com"}
                mock_db.side_effect = Exception("Database connection failed")
                
                response = await client.get("/api/forms", headers=auth_headers())
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR