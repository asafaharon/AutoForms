#!/usr/bin/env python3
"""
Test script to verify the implemented security features work correctly
"""

def test_csrf_token_generation():
    """Test CSRF token generation"""
    try:
        from backend.services.security import SecurityManager
        
        token = SecurityManager.generate_csrf_token()
        assert len(token) > 20, "CSRF token should be sufficiently long"
        print("✅ CSRF token generation works")
        
        # Test token with secret
        secret_token = SecurityManager.create_csrf_token_with_secret("test-secret")
        assert ":" in secret_token, "Secret-based token should contain delimiters"
        print("✅ Secret-based CSRF token generation works")
        
        # Test token verification
        is_valid = SecurityManager.verify_csrf_token(secret_token, "test-secret")
        assert is_valid, "Token should verify correctly"
        print("✅ CSRF token verification works")
        
        # Test invalid token
        is_invalid = SecurityManager.verify_csrf_token("invalid:token:signature", "test-secret")
        assert not is_invalid, "Invalid token should not verify"
        print("✅ CSRF token rejects invalid tokens")
        
    except Exception as e:
        print(f"❌ CSRF token test failed: {e}")
        return False
    
    return True

def test_email_functions():
    """Test email-related functions"""
    try:
        from backend.services.email_service import get_email_translations, add_unsubscribe_footer
        from backend.config import get_settings
        
        # Test translations
        en_translations = get_email_translations("en")
        assert "subject" in en_translations, "English translations should have required keys"
        print("✅ Email translations work")
        
        he_translations = get_email_translations("he")
        assert "subject" in he_translations, "Hebrew translations should have required keys"
        print("✅ Hebrew email translations work")
        
        # Test unsubscribe footer
        settings = get_settings()
        sample_html = "<html><body><p>Test content</p></body></html>"
        html_with_footer = add_unsubscribe_footer(sample_html, "test@example.com", settings)
        assert "unsubscribe" in html_with_footer.lower(), "Footer should contain unsubscribe link"
        print("✅ Unsubscribe footer injection works")
        
    except Exception as e:
        print(f"❌ Email functions test failed: {e}")
        return False
    
    return True

def test_model_imports():
    """Test model imports and structure"""
    try:
        from backend.models.form_models import FormSubmission, EmailUnsubscribe
        
        # Test FormSubmission has email field
        import inspect
        fields = inspect.signature(FormSubmission.__init__).parameters
        assert "email" in fields, "FormSubmission should have email field"
        print("✅ FormSubmission model updated correctly")
        
        # Test EmailUnsubscribe model
        unsubscribe_fields = inspect.signature(EmailUnsubscribe.__init__).parameters
        assert "unsubscribe_token" in unsubscribe_fields, "EmailUnsubscribe should have token field"
        print("✅ EmailUnsubscribe model works")
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False
    
    return True

def test_transaction_manager():
    """Test transaction manager syntax"""
    try:
        from backend.services.db_transaction import TransactionManager, db_transaction
        print("✅ Transaction manager imports successfully")
        
        # Test that the class has required methods
        tm = TransactionManager()
        assert hasattr(tm, '__aenter__'), "TransactionManager should be async context manager"
        assert hasattr(tm, '__aexit__'), "TransactionManager should be async context manager"
        print("✅ Transaction manager structure is correct")
        
    except Exception as e:
        print(f"❌ Transaction manager test failed: {e}")
        return False
    
    return True

def run_all_tests():
    """Run all verification tests"""
    print("🧪 Running implementation verification tests...\n")
    
    tests = [
        ("CSRF Token Generation", test_csrf_token_generation),
        ("Email Functions", test_email_functions),
        ("Model Updates", test_model_imports),
        ("Transaction Manager", test_transaction_manager),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All implementation tests passed!")
        return True
    else:
        print("⚠️ Some tests failed - check implementation")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)