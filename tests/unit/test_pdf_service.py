"""
Unit tests for PDF service
"""
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from backend.services.pdf_service import (
    html_to_pdf_file,
    html_to_text_file,
    cleanup_file_after_delay
)


class TestPDFService:
    """Test PDF service functionality"""
    
    @patch('backend.services.pdf_service.WEASYPRINT_AVAILABLE', True)
    @patch('backend.services.pdf_service.HTML')
    def test_html_to_pdf_file_success(self, mock_html_class):
        """Test successful PDF generation"""
        mock_html = MagicMock()
        mock_html_class.return_value = mock_html
        
        # Mock the PDF generation
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
            mock_file = MagicMock()
            mock_file.name = "/tmp/test.pdf"
            mock_tempfile.return_value.__enter__.return_value = mock_file
            
            result = html_to_pdf_file("<html><body>Test</body></html>")
            
            assert result == "/tmp/test.pdf"
            mock_html.write_pdf.assert_called_once_with("/tmp/test.pdf")
    
    @patch('backend.services.pdf_service.WEASYPRINT_AVAILABLE', False)
    def test_html_to_pdf_file_weasyprint_unavailable(self):
        """Test PDF generation when WeasyPrint is unavailable"""
        with pytest.raises(ImportError) as exc_info:
            html_to_pdf_file("<html><body>Test</body></html>")
        
        assert "WeasyPrint is not installed" in str(exc_info.value)
    
    def test_html_to_text_file_success(self):
        """Test successful text file generation"""
        html_content = """
        <html>
            <body>
                <h1>Test Title</h1>
                <p>Test paragraph with <strong>bold</strong> text.</p>
                <div>Another section</div>
            </body>
        </html>
        """
        
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
            mock_file = MagicMock()
            mock_file.name = "/tmp/test.txt"
            mock_tempfile.return_value.__enter__.return_value = mock_file
            
            result = html_to_text_file(html_content, "Test Document")
            
            assert result == "/tmp/test.txt"
            # Check that write was called
            mock_file.write.assert_called()
    
    def test_html_to_text_file_hebrew_content(self):
        """Test text file generation with Hebrew content"""
        hebrew_html = """
        <div style="direction: rtl;">
            <h1>שיר אהבה</h1>
            <p>זהו שיר יפה באהבה</p>
        </div>
        """
        
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
            mock_file = MagicMock()
            mock_file.name = "/tmp/hebrew_test.txt"
            mock_tempfile.return_value.__enter__.return_value = mock_file
            
            result = html_to_text_file(hebrew_html, "Hebrew Song")
            
            assert result == "/tmp/hebrew_test.txt"
            # Verify UTF-8 encoding was used
            mock_tempfile.assert_called_with(
                delete=False, 
                suffix=".txt", 
                mode='w', 
                encoding='utf-8'
            )
    
    def test_html_to_text_file_removes_html_tags(self):
        """Test that HTML tags are properly removed"""
        html_with_tags = """
        <html>
            <body>
                <h1>Title</h1>
                <p>Paragraph with <a href="link">link</a> and <em>emphasis</em>.</p>
                <script>alert('should be removed');</script>
            </body>
        </html>
        """
        
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
            mock_file = MagicMock()
            mock_file.name = "/tmp/clean_test.txt"
            mock_tempfile.return_value.__enter__.return_value = mock_file
            
            result = html_to_text_file(html_with_tags, "Clean Test")
            
            # Get the content that was written
            written_content = mock_file.write.call_args[0][0]
            
            # Verify HTML tags were removed
            assert "<h1>" not in written_content
            assert "<p>" not in written_content
            assert "<script>" not in written_content
            assert "Title" in written_content
            assert "Paragraph" in written_content
    
    @pytest.mark.asyncio
    async def test_cleanup_file_after_delay(self):
        """Test file cleanup functionality"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b"test content")
        
        # Ensure file exists
        assert os.path.exists(tmp_path)
        
        # Test cleanup with very short delay
        await cleanup_file_after_delay(tmp_path, 0.1)
        
        # File should be deleted
        assert not os.path.exists(tmp_path)
    
    @pytest.mark.asyncio
    async def test_cleanup_nonexistent_file(self):
        """Test cleanup of non-existent file"""
        fake_path = "/tmp/nonexistent_file.txt"
        
        # Should not raise an exception
        await cleanup_file_after_delay(fake_path, 0.1)
    
    def test_pdf_html_wrapper_structure(self):
        """Test that PDF HTML wrapper has correct structure"""
        test_html = "<h1>Test Content</h1>"
        
        with patch('backend.services.pdf_service.WEASYPRINT_AVAILABLE', True):
            with patch('backend.services.pdf_service.HTML') as mock_html_class:
                with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
                    mock_file = MagicMock()
                    mock_file.name = "/tmp/test.pdf"
                    mock_tempfile.return_value.__enter__.return_value = mock_file
                    
                    html_to_pdf_file(test_html)
                    
                    # Check that HTML class was called with wrapped content
                    called_html = mock_html_class.call_args[1]['string']
                    
                    assert '<!DOCTYPE html>' in called_html
                    assert 'lang="he"' in called_html
                    assert 'dir="rtl"' in called_html
                    assert 'font-family: \'Alef\'' in called_html
                    assert test_html in called_html
    
    def test_text_content_cleaning(self):
        """Test text content cleaning functionality"""
        messy_html = """
        <html>
            <body>
                <h1>Title</h1>
                
                
                <p>Paragraph 1</p>
                <p>Paragraph 2</p>
                
                
                <div>Final section</div>
            </body>
        </html>
        """
        
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
            mock_file = MagicMock()
            mock_file.name = "/tmp/clean_test.txt"
            mock_tempfile.return_value.__enter__.return_value = mock_file
            
            html_to_text_file(messy_html, "Clean Test")
            
            written_content = mock_file.write.call_args[0][0]
            
            # Should have proper spacing and no excessive newlines
            lines = written_content.split('\n')
            # Remove empty lines for counting
            non_empty_lines = [line for line in lines if line.strip()]
            
            # Should have title line + content lines
            assert len(non_empty_lines) >= 4  # Title + at least 3 content lines
            assert "# Clean Test" in written_content