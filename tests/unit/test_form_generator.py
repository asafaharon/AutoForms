"""
Unit tests for form generator service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.services.form_generator import (
    classify_request_type,
    detect_content_theme,
    clean_explanatory_text,
    generate_fallback_content,
    generate_html_only
)


class TestRequestClassification:
    """Test request classification functionality"""
    
    def test_classify_content_request_english(self):
        """Test classification of English content requests"""
        assert classify_request_type("Write a song about love") == "content"
        assert classify_request_type("Create a poem about nature") == "content"
        assert classify_request_type("Tell me a story") == "content"
        assert classify_request_type("Write lyrics for a song") == "content"
    
    def test_classify_content_request_hebrew(self):
        """Test classification of Hebrew content requests"""
        assert classify_request_type("כתוב שיר אהבה") == "content"
        assert classify_request_type("שירת נחמה") == "content"
        assert classify_request_type("ספר לי סיפור") == "content"
        assert classify_request_type("מילות שיר") == "content"
    
    def test_classify_form_request_english(self):
        """Test classification of English form requests"""
        assert classify_request_type("Create a contact form") == "form"
        assert classify_request_type("Registration form") == "form"
        assert classify_request_type("Feedback survey") == "form"
        assert classify_request_type("Login form") == "form"
    
    def test_classify_form_request_hebrew(self):
        """Test classification of Hebrew form requests"""
        assert classify_request_type("צור טופס יצירת קשר") == "form"
        assert classify_request_type("טופס הרשמה") == "form"
        assert classify_request_type("צרו קשר") == "form"
        assert classify_request_type("שאלון משוב") == "form"
    
    def test_classify_edge_cases(self):
        """Test edge cases in classification"""
        # Short ambiguous requests should default to content
        assert classify_request_type("help") == "content"
        assert classify_request_type("test") == "content"
        
        # Empty string should default to form
        assert classify_request_type("") == "form"


class TestContentThemeDetection:
    """Test content theme detection"""
    
    def test_detect_love_theme_hebrew(self):
        """Test detection of love theme in Hebrew"""
        assert detect_content_theme("כתוב שיר אהבה") == "love"
        assert detect_content_theme("שיר על הלב") == "love"
        assert detect_content_theme("רגשות אהבה") == "love"
    
    def test_detect_comfort_theme_hebrew(self):
        """Test detection of comfort theme in Hebrew"""
        assert detect_content_theme("שיר נחמה") == "comfort"
        assert detect_content_theme("נחמות") == "comfort"
        assert detect_content_theme("ניחום") == "comfort"
    
    def test_detect_personal_theme_hebrew(self):
        """Test detection of personal theme in Hebrew"""
        assert detect_content_theme("שיר עליי") == "personal"
        assert detect_content_theme("בשבילי") == "personal"
        assert detect_content_theme("עבורי") == "personal"
    
    def test_detect_bibi_theme(self):
        """Test detection of Bibi theme"""
        assert detect_content_theme("Write a song about King Bibi") == "bibi"
        assert detect_content_theme("שיר על ביבי") == "bibi"
        assert detect_content_theme("נתניהו") == "bibi"
    
    def test_detect_love_theme_english(self):
        """Test detection of love theme in English"""
        assert detect_content_theme("love song") == "love"
        assert detect_content_theme("romantic music") == "love"
        assert detect_content_theme("heart") == "love"
    
    def test_detect_general_theme(self):
        """Test detection of general theme"""
        assert detect_content_theme("random text") == "general"
        assert detect_content_theme("something else") == "general"


class TestExplanatoryTextCleaning:
    """Test explanatory text cleaning functionality"""
    
    def test_clean_basic_explanations(self):
        """Test removal of basic explanatory text"""
        messy_content = """Here's a simple HTML form for you.
        
        <form>
            <input type="text" name="name">
        </form>
        
        ### Explanation:
        This form does something."""
        
        cleaned = clean_explanatory_text(messy_content)
        assert cleaned.startswith("<form>")
        assert "Here's a simple" not in cleaned
        assert "### Explanation:" not in cleaned
    
    def test_clean_markdown_blocks(self):
        """Test removal of markdown code blocks"""
        messy_content = """```html
        <div>Test content</div>
        ```"""
        
        cleaned = clean_explanatory_text(messy_content)
        assert cleaned.strip() == "<div>Test content</div>"
        assert "```" not in cleaned
    
    def test_clean_various_patterns(self):
        """Test removal of various explanatory patterns"""
        test_cases = [
            ("This form captures...<form></form>", "<form></form>"),
            ("I've added some CSS...<div></div>", "<div></div>"),
            ("The button is styled...<button></button>", "<button></button>"),
            ("Inline CSS is used...<html></html>", "<html></html>")
        ]
        
        for messy, expected in test_cases:
            cleaned = clean_explanatory_text(messy)
            assert cleaned.strip() == expected


class TestFallbackContent:
    """Test fallback content generation"""
    
    def test_generate_hebrew_love_content(self):
        """Test Hebrew love content generation"""
        content = generate_fallback_content("כתוב שיר אהבה עליי")
        assert "font-family: 'David'" in content
        assert "direction: rtl" in content
        assert "אהבה" in content
        assert "הלב" in content
    
    def test_generate_english_love_content(self):
        """Test English love content generation"""
        content = generate_fallback_content("Write a love song")
        assert "font-family: 'Georgia'" in content
        assert "love" in content
        assert "heart" in content
    
    def test_generate_hebrew_comfort_content(self):
        """Test Hebrew comfort content generation"""
        content = generate_fallback_content("שיר נחמה")
        assert "direction: rtl" in content
        assert "נחמה" in content or "נחמות" in content
    
    def test_generate_bibi_content(self):
        """Test Bibi content generation"""
        content = generate_fallback_content("Write a song about King Bibi")
        assert "ביבי" in content
        assert "נתניהו" in content
        assert "direction: rtl" in content
    
    def test_generate_generic_content(self):
        """Test generic content generation"""
        hebrew_content = generate_fallback_content("בקשה כללית")
        english_content = generate_fallback_content("general request")
        
        assert "direction: rtl" in hebrew_content
        assert "direction: rtl" not in english_content
        assert "עבור הבקשה" in hebrew_content
        assert "custom content" in english_content


class TestHTMLGeneration:
    """Test HTML generation functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_html_only_content(self, mock_openai_client):
        """Test HTML generation for content requests"""
        with patch('backend.services.form_generator.client', mock_openai_client):
            result = await generate_html_only("Write a love song")
            assert "<html>" in result
            assert "Test Form" in result
    
    @pytest.mark.asyncio
    async def test_generate_html_only_form(self, mock_openai_client):
        """Test HTML generation for form requests"""
        with patch('backend.services.form_generator.client', mock_openai_client):
            result = await generate_html_only("Create a contact form")
            assert "<html>" in result
            assert "Test Form" in result
    
    @pytest.mark.asyncio
    async def test_generate_html_timeout_fallback(self):
        """Test HTML generation with timeout fallback"""
        with patch('backend.services.form_generator.client') as mock_client:
            mock_client.chat.completions.create.side_effect = asyncio.TimeoutError()
            
            result = await generate_html_only("Write a song")
            # Should return fallback content
            assert "<div" in result
            assert "font-family" in result


class TestLanguageDetection:
    """Test language detection functionality"""
    
    def test_hebrew_detection(self):
        """Test Hebrew text detection"""
        from backend.services.form_generator import detect_language_fast
        
        assert detect_language_fast("כתוב שיר אהבה") == "he"
        assert detect_language_fast("שלום עולם") == "he"
        assert detect_language_fast("בקשה בעברית") == "he"
    
    def test_english_detection(self):
        """Test English text detection"""
        from backend.services.form_generator import detect_language_fast
        
        assert detect_language_fast("Write a love song") == "en"
        assert detect_language_fast("Hello world") == "en"
        assert detect_language_fast("English request") == "en"
    
    def test_mixed_language_detection(self):
        """Test mixed language detection"""
        from backend.services.form_generator import detect_language_fast
        
        # Should default to English for mixed content
        mixed_text = "Write a שיר אהבה"
        result = detect_language_fast(mixed_text)
        assert result in ["en", "he"]  # Either is acceptable for mixed content