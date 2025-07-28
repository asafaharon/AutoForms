"""
Form embedding and submission URL injection service
"""
import re
import uuid
from typing import Dict, Any
from backend.config import get_settings

def inject_submission_endpoint(html: str, form_id: str = None) -> Dict[str, Any]:
    """
    Inject submission endpoint into form HTML
    
    Args:
        html: The original form HTML
        form_id: Optional form ID, generates new one if not provided
        
    Returns:
        Dict with updated HTML and form metadata
    """
    if form_id is None:
        form_id = str(uuid.uuid4())
    
    settings = get_settings()
    base_url = settings.base_url
    submission_url = f"{base_url}/api/submissions/submit/{form_id}"
    
    # Find form tags and inject action and method
    form_pattern = r'<form([^>]*)>'
    
    def replace_form_tag(match):
        existing_attrs = match.group(1)
        
        # Remove existing action and method if present
        existing_attrs = re.sub(r'\s*action\s*=\s*["\'][^"\']*["\']', '', existing_attrs, flags=re.IGNORECASE)
        existing_attrs = re.sub(r'\s*method\s*=\s*["\'][^"\']*["\']', '', existing_attrs, flags=re.IGNORECASE)
        
        # Add our action and method
        new_form_tag = f'<form{existing_attrs} action="{submission_url}" method="POST">'
        return new_form_tag
    
    # Update all form tags
    updated_html = re.sub(form_pattern, replace_form_tag, html, flags=re.IGNORECASE)
    
    # Add CSRF token and form ID as hidden fields if not present
    csrf_token = str(uuid.uuid4())
    hidden_fields = f'''
    <input type="hidden" name="form_id" value="{form_id}">
    <input type="hidden" name="csrf_token" value="{csrf_token}">
    '''
    
    # Insert hidden fields after the first form tag
    form_start_pattern = r'(<form[^>]*>)'
    updated_html = re.sub(
        form_start_pattern, 
        r'\1' + hidden_fields, 
        updated_html, 
        count=1, 
        flags=re.IGNORECASE
    )
    
    # Add success/error handling JavaScript
    success_script = f'''
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        const forms = document.querySelectorAll('form[action*="/api/submissions/submit"]');
        
        forms.forEach(form => {{
            form.addEventListener('submit', function(e) {{
                e.preventDefault();
                
                const formData = new FormData(form);
                const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
                
                // Disable submit button
                if (submitButton) {{
                    submitButton.disabled = true;
                    submitButton.textContent = 'Submitting...';
                }}
                
                fetch(form.action, {{
                    method: 'POST',
                    body: formData
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        // Show success message
                        form.innerHTML = `
                            <div style="text-align: center; padding: 20px; background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 8px; color: #0c4a6e;">
                                <h3 style="color: #0c4a6e; margin-bottom: 10px;">✅ Thank you!</h3>
                                <p>Your form has been submitted successfully.</p>
                            </div>
                        `;
                    }} else {{
                        throw new Error(data.message || 'Submission failed');
                    }}
                }})
                .catch(error => {{
                    console.error('Form submission error:', error);
                    
                    // Show error message
                    let errorDiv = form.querySelector('.error-message');
                    if (!errorDiv) {{
                        errorDiv = document.createElement('div');
                        errorDiv.className = 'error-message';
                        errorDiv.style.cssText = 'background: #fef2f2; border: 1px solid #ef4444; color: #991b1b; padding: 10px; border-radius: 4px; margin-bottom: 15px;';
                        form.insertBefore(errorDiv, form.firstChild);
                    }}
                    errorDiv.innerHTML = `❌ Error: ${{error.message || 'Failed to submit form. Please try again.'}}`;
                    
                    // Re-enable submit button
                    if (submitButton) {{
                        submitButton.disabled = false;
                        submitButton.textContent = 'Submit';
                    }}
                }});
            }});
        }});
    }});
    </script>
    '''
    
    # Add script before closing body tag or at the end if no body tag
    if '</body>' in updated_html:
        updated_html = updated_html.replace('</body>', success_script + '</body>')
    else:
        updated_html += success_script
    
    return {
        "html": updated_html,
        "form_id": form_id,
        "submission_url": submission_url,
        "embed_code": generate_embed_code(updated_html, form_id),
        "iframe_code": generate_iframe_code(form_id)
    }

def generate_embed_code(html: str, form_id: str) -> str:
    """Generate embeddable code for the form"""
    
    # Extract just the form part (remove html, head, body tags for embedding)
    form_match = re.search(r'<form.*?</form>', html, re.DOTALL | re.IGNORECASE)
    if form_match:
        form_html = form_match.group(0)
    else:
        form_html = html
    
    # Escape the HTML for JavaScript
    escaped_html = form_html.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    
    # Use template string with placeholder to avoid f-string conflicts
    embed_template = '''
<!-- AutoForms Embedded Form - Form ID: FORM_ID_PLACEHOLDER -->
<div id="autoforms-FORM_ID_PLACEHOLDER"></div>
<script>
(function() {
    const formHtml = `ESCAPED_HTML_PLACEHOLDER`;
    document.getElementById('autoforms-FORM_ID_PLACEHOLDER').innerHTML = formHtml;
})();
</script>
<!-- End AutoForms Embedded Form -->
    '''.strip()
    
    # Safe replacement of placeholders
    embed_code = embed_template.replace('FORM_ID_PLACEHOLDER', form_id)
    embed_code = embed_code.replace('ESCAPED_HTML_PLACEHOLDER', escaped_html)
    
    return embed_code

def generate_iframe_code(form_id: str) -> str:
    """Generate iframe embed code for the form"""
    settings = get_settings()
    iframe_url = f"{settings.base_url}/embed/{form_id}"
    
    iframe_code = f'''
<iframe 
    src="{iframe_url}" 
    width="100%" 
    height="500" 
    frameborder="0" 
    style="border: 1px solid #e2e8f0; border-radius: 8px;">
</iframe>
    '''.strip()
    
    return iframe_code

def create_embeddable_form_page(html: str, form_id: str) -> str:
    """Create a complete standalone HTML page for iframe embedding"""
    
    # Extract form content
    form_match = re.search(r'<form.*?</form>', html, re.DOTALL | re.IGNORECASE)
    if form_match:
        form_content = form_match.group(0)
    else:
        form_content = html
    
    settings = get_settings()
    
    # Use template string with placeholder to avoid f-string conflicts
    embed_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoForms - Form</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f8fafc;
        }
        .form-container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            padding: 24px;
        }
        .powered-by {
            text-align: center;
            margin-top: 20px;
            font-size: 12px;
            color: #64748b;
        }
        .powered-by a {
            color: #2563eb;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="form-container">
        FORM_CONTENT_PLACEHOLDER
    </div>
    
    <div class="powered-by">
        Powered by <a href="BASE_URL_PLACEHOLDER" target="_blank">AutoForms</a>
    </div>

    <script>
    // Form submission handling
    document.addEventListener('DOMContentLoaded', function() {
        const forms = document.querySelectorAll('form[action*="/api/submissions/submit"]');
        
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(form);
                const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
                
                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.textContent = 'Submitting...';
                }
                
                fetch(form.action, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        form.innerHTML = `
                            <div style="text-align: center; padding: 30px; background: #f0f9ff; border: 2px solid #0ea5e9; border-radius: 12px; color: #0c4a6e;">
                                <h3 style="color: #0c4a6e; margin-bottom: 15px; font-size: 20px;">✅ Thank you!</h3>
                                <p style="margin: 0; font-size: 16px;">Your form has been submitted successfully.</p>
                            </div>
                        `;
                    } else {
                        throw new Error(data.message || 'Submission failed');
                    }
                })
                .catch(error => {
                    console.error('Form submission error:', error);
                    
                    let errorDiv = form.querySelector('.error-message');
                    if (!errorDiv) {
                        errorDiv = document.createElement('div');
                        errorDiv.className = 'error-message';
                        errorDiv.style.cssText = 'background: #fef2f2; border: 2px solid #ef4444; color: #991b1b; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center;';
                        form.insertBefore(errorDiv, form.firstChild);
                    }
                    errorDiv.innerHTML = `❌ ${error.message || 'Failed to submit form. Please try again.'}`;
                    
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.textContent = 'Submit';
                    }
                });
            });
        });
    });
    </script>
</body>
</html>
    '''.strip()
    
    # Safe replacement of placeholders
    embed_page = embed_template.replace('FORM_CONTENT_PLACEHOLDER', form_content)
    embed_page = embed_page.replace('BASE_URL_PLACEHOLDER', settings.base_url)
    
    return embed_page