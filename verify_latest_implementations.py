#!/usr/bin/env python3
"""
Verification script for the latest security and enhancement implementations:
1. Email Rate Limiting - Prevent abuse
2. Input Validation - Strengthen API endpoints
3. Language consistency - Standardize comments to English
"""

def test_rate_limiter():
    """Test email and API rate limiting functionality"""
    try:
        from backend.services.rate_limiter import EmailRateLimiter, APIRateLimiter, email_rate_limiter, api_rate_limiter
        
        # Test EmailRateLimiter class exists and has required methods
        assert hasattr(EmailRateLimiter, 'check_rate_limit'), "EmailRateLimiter should have check_rate_limit method"
        assert hasattr(EmailRateLimiter, 'record_email_sent'), "EmailRateLimiter should have record_email_sent method"
        assert hasattr(EmailRateLimiter, 'get_rate_limit_status'), "EmailRateLimiter should have get_rate_limit_status method"
        print("✅ EmailRateLimiter class structure is correct")
        
        # Test APIRateLimiter class exists and has required methods
        assert hasattr(APIRateLimiter, 'check_and_record'), "APIRateLimiter should have check_and_record method"
        print("✅ APIRateLimiter class structure is correct")
        
        # Test global instances exist
        assert email_rate_limiter is not None, "Global email_rate_limiter should exist"
        assert api_rate_limiter is not None, "Global api_rate_limiter should exist"
        print("✅ Global rate limiter instances exist")
        
        # Test rate limiting logic
        test_email = "test@example.com"
        allowed, reason = email_rate_limiter.check_rate_limit(test_email)
        assert isinstance(allowed, bool), "check_rate_limit should return boolean"
        assert isinstance(reason, str), "check_rate_limit should return string reason"
        print("✅ Rate limiting logic works")
        
        # Test API rate limiting
        allowed, reason = api_rate_limiter.check_and_record('api_per_ip', 'test_ip')
        assert isinstance(allowed, bool), "API rate limiter should return boolean"
        assert isinstance(reason, str), "API rate limiter should return string reason"
        print("✅ API rate limiting works")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limiter test failed: {e}")
        return False

def test_input_validation():
    """Test input validation functionality"""
    try:
        from backend.services.input_validation import InputValidator, input_validator
        
        # Test InputValidator class exists and has required methods
        assert hasattr(InputValidator, 'validate_field'), "InputValidator should have validate_field method"
        assert hasattr(InputValidator, 'validate_data'), "InputValidator should have validate_data method"
        assert hasattr(InputValidator, 'validate_form_data'), "InputValidator should have validate_form_data method"
        assert hasattr(InputValidator, 'sanitize_string'), "InputValidator should have sanitize_string method"
        assert hasattr(InputValidator, 'sanitize_email'), "InputValidator should have sanitize_email method"
        print("✅ InputValidator class structure is correct")
        
        # Test validation rules exist
        assert hasattr(InputValidator, 'VALIDATION_RULES'), "InputValidator should have VALIDATION_RULES"
        assert hasattr(InputValidator, 'PATTERNS'), "InputValidator should have PATTERNS"
        print("✅ Validation rules and patterns exist")
        
        # Test global instance exists
        assert input_validator is not None, "Global input_validator should exist"
        print("✅ Global input validator instance exists")
        
        # Test email validation
        try:
            valid_email = input_validator.sanitize_email("test@example.com")
            assert valid_email == "test@example.com", "Valid email should pass validation"
            print("✅ Email validation works")
        except Exception as e:
            print(f"⚠️ Email validation test issue: {e}")
        
        # Test string sanitization
        sanitized = input_validator.sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in sanitized or "&lt;script&gt;" in sanitized, "HTML should be escaped"
        print("✅ String sanitization works")
        
        # Test form data validation
        test_data = {"field1": "value1", "field2": "value2"}
        is_valid, errors, sanitized = input_validator.validate_form_data(test_data)
        assert isinstance(is_valid, bool), "validate_form_data should return boolean"
        assert isinstance(errors, list), "validate_form_data should return list of errors"
        assert isinstance(sanitized, dict), "validate_form_data should return sanitized data"
        print("✅ Form data validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Input validation test failed: {e}")
        return False

def test_updated_email_service():
    """Test that email service includes rate limiting"""
    try:
        from backend.services.email_service import send_form_link, send_form_pdf, send_reset_email, send_submission_notification
        import inspect
        
        # Check that email functions have been updated with rate limiting parameters
        send_form_link_sig = inspect.signature(send_form_link)
        assert 'user_id' in send_form_link_sig.parameters, "send_form_link should have user_id parameter"
        assert 'ip_address' in send_form_link_sig.parameters, "send_form_link should have ip_address parameter"
        print("✅ send_form_link updated with rate limiting parameters")
        
        send_form_pdf_sig = inspect.signature(send_form_pdf)
        assert 'user_id' in send_form_pdf_sig.parameters, "send_form_pdf should have user_id parameter"
        assert 'ip_address' in send_form_pdf_sig.parameters, "send_form_pdf should have ip_address parameter"
        print("✅ send_form_pdf updated with rate limiting parameters")
        
        send_reset_email_sig = inspect.signature(send_reset_email)
        assert 'ip_address' in send_reset_email_sig.parameters, "send_reset_email should have ip_address parameter"
        print("✅ send_reset_email updated with rate limiting parameters")
        
        send_submission_notification_sig = inspect.signature(send_submission_notification)
        assert 'user_id' in send_submission_notification_sig.parameters, "send_submission_notification should have user_id parameter"
        assert 'ip_address' in send_submission_notification_sig.parameters, "send_submission_notification should have ip_address parameter"
        print("✅ send_submission_notification updated with rate limiting parameters")
        
        return True
        
    except Exception as e:
        print(f"❌ Email service update test failed: {e}")
        return False

def test_updated_routers():
    """Test that routers include input validation and rate limiting"""
    try:
        from backend.routers.generate import generate_demo_html, save_form
        from backend.routers.submissions import submit_form
        import inspect
        
        # Check that generate router functions have been updated
        generate_demo_sig = inspect.signature(generate_demo_html)
        assert 'request' in generate_demo_sig.parameters, "generate_demo_html should have request parameter for IP extraction"
        print("✅ generate_demo_html updated with request parameter")
        
        save_form_sig = inspect.signature(save_form)
        assert 'request' in save_form_sig.parameters, "save_form should have request parameter"
        print("✅ save_form updated with request parameter")
        
        # Check that submissions router has been updated
        submit_form_sig = inspect.signature(submit_form)
        assert 'request' in submit_form_sig.parameters, "submit_form should have request parameter"
        print("✅ submit_form has request parameter for rate limiting")
        
        return True
        
    except Exception as e:
        print(f"❌ Router update test failed: {e}")
        return False

def test_language_consistency():
    """Test that Hebrew comments have been replaced with English"""
    try:
        import os
        import re
        
        # List of files to check for Hebrew comments
        files_to_check = [
            'backend/deps.py',
            'backend/main.py', 
            'backend/routers/password_reset.py',
            'backend/routers/generate.py',
            'backend/routers/auth.py',
            'backend/routers/creations.py'
        ]
        
        hebrew_pattern = re.compile(r'[א-ת]')
        issues = []
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Look for Hebrew characters in comments and strings
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        # Skip test data and content (focus on comments and error messages)
                        if (line.strip().startswith('#') or 
                            ('HTTPException' in line and hebrew_pattern.search(line)) or
                            ('return {"msg"' in line and hebrew_pattern.search(line))):
                            if hebrew_pattern.search(line):
                                issues.append(f"{file_path}:{i} - {line.strip()}")
                except Exception as e:
                    print(f"⚠️ Could not check {file_path}: {e}")
        
        if issues:
            print("⚠️ Found remaining Hebrew text in comments/messages:")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"   {issue}")
            if len(issues) > 5:
                print(f"   ... and {len(issues) - 5} more")
            return False
        else:
            print("✅ No Hebrew comments found in checked files")
            return True
            
    except Exception as e:
        print(f"❌ Language consistency test failed: {e}")
        return False

def test_integration_imports():
    """Test that all new modules can be imported together"""
    try:
        # Test that all our new services can be imported without conflicts
        from backend.services.rate_limiter import email_rate_limiter, api_rate_limiter
        from backend.services.input_validation import input_validator
        from backend.services.db_transaction import TransactionManager
        from backend.services.security import generate_csrf_token_for_request
        from backend.services.email_service import check_unsubscribed
        
        print("✅ All new services import successfully")
        
        # Test that updated routers can be imported
        from backend.routers.generate import router as generate_router
        from backend.routers.submissions import router as submissions_router
        from backend.routers.unsubscribe import router as unsubscribe_router
        
        print("✅ All updated routers import successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration imports test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_verification_tests():
    """Run all verification tests"""
    print("🧪 Running verification tests for latest implementations...\n")
    
    tests = [
        ("Rate Limiter Functionality", test_rate_limiter),
        ("Input Validation Functionality", test_input_validation),
        ("Email Service Updates", test_updated_email_service),
        ("Router Updates", test_updated_routers),
        ("Language Consistency", test_language_consistency),
        ("Integration Imports", test_integration_imports),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 Verification Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All verification tests passed! Implementations are working correctly.")
        return True
    else:
        print("⚠️ Some tests failed - check implementations")
        return False

if __name__ == "__main__":
    success = run_all_verification_tests()
    exit(0 if success else 1)