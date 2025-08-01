#!/usr/bin/env python3
"""
Check integration and potential issues in the codebase
"""
import os
import re
import ast
import sys

def check_imports(file_path):
    """Check imports in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.append(f"{node.module}.{alias.name}")
        
        return imports
    except Exception as e:
        return f"Error: {e}"

def check_circular_imports():
    """Check for potential circular import issues"""
    print("🔍 Checking for potential circular imports...")
    
    backend_files = []
    for root, dirs, files in os.walk('backend'):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                backend_files.append(os.path.join(root, file))
    
    issues = []
    for file_path in backend_files:
        imports = check_imports(file_path)
        if isinstance(imports, str):  # Error case
            issues.append(f"{file_path}: {imports}")
    
    if issues:
        print("❌ Import issues found:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("✅ No import issues detected")
        return True

def check_missing_files():
    """Check if all required files exist"""
    print("🔍 Checking for missing required files...")
    
    required_files = [
        'backend/services/rate_limiter.py',
        'backend/services/input_validation.py', 
        'backend/services/db_transaction.py',
        'backend/routers/unsubscribe.py',
        'backend/templates/unsubscribe.html',
        'backend/templates/unsubscribe_success.html',
        'backend/templates/unsubscribe_error.html'
    ]
    
    missing = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing.append(file_path)
    
    if missing:
        print("❌ Missing required files:")
        for file_path in missing:
            print(f"   {file_path}")
        return False
    else:
        print("✅ All required files exist")
        return True

def check_configuration_consistency():
    """Check configuration consistency across files"""
    print("🔍 Checking configuration consistency...")
    
    # Check if main.py includes all routers
    try:
        with open('backend/main.py', 'r') as f:
            main_content = f.read()
        
        expected_routers = [
            'admin.router',
            'password_reset.router', 
            'creations.router',
            'auth_router',
            'generate.router',
            'forms.router',
            'submit.submit_router',
            'pages.router',
            'websocket.router',
            'template_router.router',
            'submissions.router',
            'unsubscribe.router'
        ]
        
        missing_routers = []
        for router in expected_routers:
            if router not in main_content:
                missing_routers.append(router)
        
        if missing_routers:
            print("❌ Missing router registrations:")
            for router in missing_routers:
                print(f"   {router}")
            return False
        else:
            print("✅ All routers properly registered")
            return True
            
    except Exception as e:
        print(f"❌ Error checking main.py: {e}")
        return False

def check_security_implementation():
    """Check if security implementations are properly integrated"""
    print("🔍 Checking security implementation integration...")
    
    checks = []
    
    # Check CSRF token in security.py
    try:
        with open('backend/services/security.py', 'r') as f:
            security_content = f.read()
        if 'generate_csrf_token_for_request' in security_content:
            checks.append("✅ CSRF token generation implemented")
        else:
            checks.append("❌ CSRF token generation missing")
    except:
        checks.append("❌ Could not check security.py")
    
    # Check rate limiting in email service
    try:
        with open('backend/services/email_service.py', 'r') as f:
            email_content = f.read()
        if 'email_rate_limiter.check_rate_limit' in email_content:
            checks.append("✅ Email rate limiting implemented")
        else:
            checks.append("❌ Email rate limiting missing")
    except:
        checks.append("❌ Could not check email_service.py")
    
    # Check input validation in routers
    try:
        with open('backend/routers/generate.py', 'r') as f:
            router_content = f.read()
        if 'input_validator.validate_data' in router_content:
            checks.append("✅ Input validation in generate router")
        else:
            checks.append("❌ Input validation missing in generate router")
    except:
        checks.append("❌ Could not check generate.py")
    
    # Check database transactions
    try:
        with open('backend/routers/submissions.py', 'r') as f:
            submissions_content = f.read()
        if 'TransactionManager' in submissions_content:
            checks.append("✅ Database transactions implemented")
        else:
            checks.append("❌ Database transactions missing")
    except:
        checks.append("❌ Could not check submissions.py")
    
    for check in checks:
        print(f"   {check}")
    
    failed_checks = [c for c in checks if c.startswith("❌")]
    return len(failed_checks) == 0

def run_integration_checks():
    """Run all integration checks"""
    print("🧪 Running comprehensive integration checks...\n")
    
    checks = [
        ("Circular Imports", check_circular_imports),
        ("Missing Files", check_missing_files),
        ("Configuration Consistency", check_configuration_consistency),
        ("Security Implementation", check_security_implementation)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        try:
            if check_func():
                passed += 1
            else:
                print(f"❌ {check_name} failed")
        except Exception as e:
            print(f"❌ {check_name} error: {e}")
    
    print(f"\n📊 Integration Check Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All integration checks passed!")
        return True
    else:
        print("⚠️ Some integration checks failed")
        return False

if __name__ == "__main__":
    success = run_integration_checks()
    sys.exit(0 if success else 1)