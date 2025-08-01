# backend/services/form_generator.py
from __future__ import annotations
import json, uuid, asyncio
from datetime import datetime
from typing import Any, Dict, Tuple
import os
import openai            # openai-python >=1.0
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from langdetect import detect

from backend.config import get_settings
from backend.db import get_db
from backend.services.cache import openai_cache
from backend.services.performance_monitor import perf_monitor

settings = get_settings()
client = openai.AsyncOpenAI(
    api_key=settings.openai_key,
    timeout=15.0,  # Reduced timeout for faster failure
    max_retries=1  # Reduced retries for speed
)


def generate_fallback_form(prompt: str) -> str:
    """Generate a simple fallback form when OpenAI is unavailable"""
    print(f"🛠️ Generating fallback form for: {prompt[:30]}...")
    
    # Detect common form types from the prompt
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ['contact', 'get in touch', 'reach out']):
        form_type = 'contact'
    elif any(word in prompt_lower for word in ['register', 'sign up', 'join']):
        form_type = 'registration'
    elif any(word in prompt_lower for word in ['feedback', 'review', 'opinion']):
        form_type = 'feedback'
    elif any(word in prompt_lower for word in ['survey', 'questionnaire', 'poll']):
        form_type = 'survey'
    else:
        form_type = 'general'
    
    # Generate appropriate HTML based on form type
    forms = {
        'contact': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact Form</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-2xl font-bold mb-4 text-gray-800">Contact Us</h2>
        <form class="space-y-4" action="/api/submissions/submit/fallback-contact" method="POST">
            <div>
                <label class="block text-sm font-medium text-gray-700">Name</label>
                <input type="text" name="name" required class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700">Email</label>
                <input type="email" name="email" required class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700">Message</label>
                <textarea name="message" rows="4" required class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2"></textarea>
            </div>
            <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">Send Message</button>
        </form>
    </div>
</body>
</html>''',
        
        'registration': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registration Form</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-2xl font-bold mb-4 text-gray-800">Registration</h2>
        <form class="space-y-4" action="/api/submissions/submit/fallback-registration" method="POST">
            <div>
                <label class="block text-sm font-medium text-gray-700">Full Name</label>
                <input type="text" name="fullname" required class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700">Email</label>
                <input type="email" name="email" required class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700">Phone</label>
                <input type="tel" name="phone" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2">
            </div>
            <button type="submit" class="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700">Register</button>
        </form>
    </div>
</body>
</html>''',
        
        'feedback': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Feedback Form</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-2xl font-bold mb-4 text-gray-800">Feedback</h2>
        <form class="space-y-4" action="/api/submissions/submit/fallback-feedback" method="POST">
            <div>
                <label class="block text-sm font-medium text-gray-700">Rating</label>
                <select name="rating" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2">
                    <option value="5">⭐⭐⭐⭐⭐ Excellent</option>
                    <option value="4">⭐⭐⭐⭐ Good</option>
                    <option value="3">⭐⭐⭐ Average</option>
                    <option value="2">⭐⭐ Poor</option>
                    <option value="1">⭐ Very Poor</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700">Comments</label>
                <textarea name="comments" rows="4" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2" placeholder="Share your thoughts..."></textarea>
            </div>
            <button type="submit" class="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700">Submit Feedback</button>
        </form>
    </div>
</body>
</html>''',
        
        'survey': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Survey Form</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-2xl font-bold mb-4 text-gray-800">Survey</h2>
        <form class="space-y-4" action="/api/submissions/submit/fallback-survey" method="POST">
            <div>
                <label class="block text-sm font-medium text-gray-700">How satisfied are you?</label>
                <div class="mt-2 space-y-2">
                    <label class="flex items-center">
                        <input type="radio" name="satisfaction" value="very_satisfied" class="mr-2">
                        Very Satisfied
                    </label>
                    <label class="flex items-center">
                        <input type="radio" name="satisfaction" value="satisfied" class="mr-2">
                        Satisfied
                    </label>
                    <label class="flex items-center">
                        <input type="radio" name="satisfaction" value="neutral" class="mr-2">
                        Neutral
                    </label>
                    <label class="flex items-center">
                        <input type="radio" name="satisfaction" value="dissatisfied" class="mr-2">
                        Dissatisfied
                    </label>
                </div>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700">Additional Comments</label>
                <textarea name="comments" rows="3" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2"></textarea>
            </div>
            <button type="submit" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700">Submit Survey</button>
        </form>
    </div>
</body>
</html>''',
        
        'general': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Form</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-2xl font-bold mb-4 text-gray-800">Form</h2>
        <form class="space-y-4" action="/api/submissions/submit/fallback-general" method="POST">
            <div>
                <label class="block text-sm font-medium text-gray-700">Name</label>
                <input type="text" name="name" required class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700">Email</label>
                <input type="email" name="email" required class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700">Details</label>
                <textarea name="details" rows="3" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2"></textarea>
            </div>
            <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">Submit</button>
        </form>
    </div>
</body>
</html>'''
    }
    
    return forms.get(form_type, forms['general'])

def detect_language_fast(text: str) -> str:
    """Fast language detection with caching and shortcuts"""
    # Skip detection for short prompts or use simple heuristics
    if len(text) < 10:
        return "en"
    
    # Simple Hebrew detection (faster than langdetect)
    hebrew_chars = sum(1 for c in text if '\u0590' <= c <= '\u05FF')
    if hebrew_chars > len(text) * 0.3:
        return "he"
    
    # Default to English for speed
    return "en"

async def generate_schema_and_html(prompt: str, lang: str = None) -> Tuple[dict, str]:
    if not lang:
        lang = detect_language_fast(prompt)
    
    # Use faster temperature for speed vs creativity trade-off
    temperature = 0.4  # Higher temp = faster generation
    cache_key_params = (prompt, settings.openai_model, temperature)
    
    # Check cache first
    cached_result = openai_cache.get(*cache_key_params)
    if cached_result:
        print(f"🚀 Cache hit for prompt: {prompt[:50]}...")
        perf_monitor.record_generation_time("schema_and_html", 0.1, cache_hit=True)
        return cached_result
    
    # Optimized system message for faster processing
    system_msg = (
        "Create a form fast. Return JSON with 'schema' and 'html' fields only. "
        "No explanations. Make it functional and simple."
    )

    try:
        print(f"🤖 Generating form for prompt: {prompt[:50]}...")
        start_time = datetime.now()
        
        # Retry with longer timeouts for schema generation
        max_attempts = 2
        timeouts = [20.0, 40.0]  # More generous timeouts for complex schema generation
        
        for attempt in range(max_attempts):
            try:
                timeout_val = timeouts[attempt]
                print(f"🔄 Schema attempt {attempt + 1}/{max_attempts} with {timeout_val}s timeout...")
                
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=settings.openai_model,
                        response_format={"type": "json_object"},
                        temperature=temperature,
                        max_tokens=1800,  # Slightly reduced for speed
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": f"{prompt} (Language: {lang})"},
                        ],
                    ),
                    timeout=timeout_val
                )
                break  # Success, exit retry loop
                
            except asyncio.TimeoutError:
                if attempt == max_attempts - 1:  # Last attempt
                    print(f"❌ Schema generation timed out after all attempts.")
                    raise asyncio.TimeoutError("OpenAI API is taking too long for schema generation")
                else:
                    print(f"⏱️ Schema attempt {attempt + 1} timed out, retrying...")
                    continue
        
        generation_time = (datetime.now() - start_time).total_seconds()
        print(f"⏱️ OpenAI generation took {generation_time:.2f}s")
        
        content = resp.choices[0].message.content
        data = json.loads(content)
        schema = data.get("schema")
        html   = data.get("html")
        if not schema or not html:
            raise ValueError("Missing 'schema' or 'html' keys")
        
        # Cache the result for future use
        result = (schema, html)
        openai_cache.set(*cache_key_params, result)
        perf_monitor.record_generation_time("schema_and_html", generation_time, cache_hit=False)
        print(f"💾 Cached result for prompt: {prompt[:50]}... (Total: {generation_time:.2f}s)")
        
        return result

    except asyncio.TimeoutError:
        print("❌ OpenAI request timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Form generation timed out. Please try again.",
        )
    except Exception as exc:
        print(f"❌ GPT response error: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
        
        # Provide specific error messages based on error type
        if "authentication" in str(exc).lower() or "api_key" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI API authentication failed. Please check your API key.",
            )
        elif "rate_limit" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="OpenAI API rate limit exceeded. Please try again later.",
            )
        else:
            # Log the actual error for debugging but don't expose it to user
            print(f"Form generation error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Form generation service temporarily unavailable. Please try again later.",
            )
def classify_request_type(prompt: str) -> str:
    """Classify if the request is for a form or general content - supports Hebrew"""
    prompt_lower = prompt.lower().strip()
    
    # Content creation keywords (English + Hebrew)
    content_keywords = [
        # English
        'write', 'song', 'poem', 'story', 'lyrics', 'praise', 'about', 'tell me',
        'explain', 'describe', 'create a story', 'compose', 'generate text',
        'write a', 'make a song', 'create lyrics', 'poem about', 'story about',
        # Hebrew
        'כתוב', 'שיר', 'שירת', 'שיר אהבה', 'שירי', 'מילים', 'טקסט',
        'ספר', 'סיפור', 'משורר', 'שירה', 'מילות שיר', 'חרוזים',
        'ליצור', 'לכתוב', 'להלחין', 'על אהבה', 'על', 'עליי', 'עליו', 'עליה',
        'בשבילי', 'בשביל', 'עבורי', 'עבור', 'נחמה', 'נחמות', 'ניחום'
    ]
    
    # Form keywords (English + Hebrew)
    form_keywords = [
        # English
        'form', 'contact', 'register', 'registration', 'sign up', 'feedback', 
        'survey', 'questionnaire', 'application', 'order', 'booking', 'reservation',
        'login', 'subscribe', 'newsletter', 'contact us', 'get in touch',
        # Hebrew
        'טופס', 'פורם', 'צור קשר', 'צרו קשר', 'הרשמה', 'רישום', 'הגשה',
        'משוב', 'סקר', 'שאלון', 'בקשה', 'הזמנה', 'הזמנות', 'התחברות',
        'כניסה למערכת', 'הרשמה לניוזלטר'
    ]
    
    # Check for content creation requests
    if any(keyword in prompt_lower for keyword in content_keywords):
        return "content"
    
    # Check for explicit form requests
    if any(keyword in prompt_lower for keyword in form_keywords):
        return "form"
    
    # Default: if unclear, treat as content unless it's clearly form-related
    if len(prompt_lower.split()) < 5:  # Short requests are likely content
        return "content"
    
    return "form"  # Default to form for longer unclear requests

async def generate_html_only(prompt: str, lang: str = None) -> str:
    """Smart HTML generation - detects if user wants content or a form"""
    if not lang:
        lang = detect_language_fast(prompt)
    
    # Check memory cache first
    from backend.services.memory_cache import cache
    cached_result = await cache.get_cached_form(prompt, lang)
    if cached_result:
        print(f"🎯 Memory cache hit for prompt: {prompt[:30]}...")
        return cached_result["html"]
    
    # Classify the request type
    request_type = classify_request_type(prompt)
    
    if request_type == "content":
        html = await generate_content_html(prompt, lang)
    else:
        html = await generate_form_html(prompt, lang)
    
    # Cache the result
    await cache.cache_form_generation(prompt, lang, html)
    
    return html

async def generate_content_html(prompt: str, lang: str) -> str:
    """Generate content (like songs, stories) as HTML"""
    # Simple cache key for content generation
    cache_key = f"content_{hash(prompt.lower().strip())}"
    
    user_prompt = f"""Create content for: "{prompt}" in {lang}. 
    Return ONLY clean HTML content without any explanations, descriptions, or markdown formatting.
    No "Here's a..." or "### Explanation" text.
    Just the pure HTML content with inline CSS styling."""

    try:
        start_time = datetime.now()
        
        # Try with progressively longer timeouts
        max_attempts = 2
        timeouts = [15.0, 30.0]
        
        for attempt in range(max_attempts):
            try:
                timeout_val = timeouts[attempt]
                print(f"🔄 Content attempt {attempt + 1}/{max_attempts} with {timeout_val}s timeout...")
                
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=settings.openai_model,
                        messages=[{"role": "user", "content": user_prompt}],
                        temperature=0.8,  # Higher creativity for content
                        max_tokens=1500,
                    ),
                    timeout=timeout_val
                )
                break
                
            except asyncio.TimeoutError:
                if attempt == max_attempts - 1:
                    print(f"❌ Content generation timed out, using fallback...")
                    return generate_fallback_content(prompt)
                else:
                    print(f"⏱️ Content attempt {attempt + 1} timed out, retrying...")
                    continue
        
        generation_time = (datetime.now() - start_time).total_seconds()
        perf_monitor.record_generation_time("content_generation", generation_time, cache_hit=False)
        print(f"⚡ Content generated in {generation_time:.2f}s")

        content = response.choices[0].message.content.strip()

        # Clean up markdown formatting
        if content.startswith("```html"):
            content = content.removeprefix("```html").strip()
        if content.endswith("```"):
            content = content.removesuffix("```").strip()
        
        # Remove common explanatory text patterns
        content = clean_explanatory_text(content)

        if "<html" not in content.lower():
            # Wrap content in HTML if it's not already wrapped
            content = f"""
            <!DOCTYPE html>
            <html lang="{lang}">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Generated Content</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
                    h1, h2 {{ color: #333; }}
                    .content {{ background: #f9f9f9; padding: 20px; border-radius: 10px; }}
                </style>
            </head>
            <body>
                <div class="content">
                    {content}
                </div>
            </body>
            </html>
            """

        return content

    except Exception as exc:
        print(f"❌ Content generation failed: {type(exc).__name__}: {exc}")
        return generate_fallback_content(prompt)

def clean_explanatory_text(content: str) -> str:
    """Remove common explanatory text patterns from AI responses"""
    import re
    
    # Remove common explanatory intros
    patterns_to_remove = [
        r"Here's a.*?(?=<html|<\!DOCTYPE|<div|<form)",
        r"### Explanation:.*?(?=<html|<\!DOCTYPE|<div|<form|$)",
        r"### [^:]*:.*?(?=<html|<\!DOCTYPE|<div|<form|$)",
        r"## [^:]*:.*?(?=<html|<\!DOCTYPE|<div|<form|$)",
        r"# [^:]*:.*?(?=<html|<\!DOCTYPE|<div|<form|$)",
        r"```html\s*",
        r"```\s*$",
        r"^\s*-.*?(?=<html|<\!DOCTYPE|<div|<form)",
        r"This form.*?(?=<html|<\!DOCTYPE|<div|<form)",
        r"The form.*?(?=<html|<\!DOCTYPE|<div|<form)",
        r"I've.*?(?=<html|<\!DOCTYPE|<div|<form)",
        r"The.*?button.*?(?=<html|<\!DOCTYPE|<div|<form)",
        r"Inline CSS.*?(?=<html|<\!DOCTYPE|<div|<form)",
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, "", content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove any remaining text before the actual HTML
    html_start = content.find('<')
    if html_start > 0:
        content = content[html_start:]
    
    return content.strip()

async def generate_form_html(prompt: str, lang: str) -> str:
    """Generate forms as HTML"""
    # Simple cache key for form generation
    cache_key = f"form_{hash(prompt.lower().strip())}"
    
    user_prompt = f"""Create HTML form for: "{prompt}" in {lang}. 
    Return ONLY clean HTML form code without any explanations, descriptions, markdown formatting, or comments.
    No "Here's a..." or "### Explanation" text.
    Just the pure HTML form with inline CSS styling."""

    try:
        start_time = datetime.now()
        
        # Try with progressively longer timeouts and simpler requests
        max_attempts = 2
        timeouts = [15.0, 30.0]  # Increased timeouts
        
        for attempt in range(max_attempts):
            try:
                timeout_val = timeouts[attempt]
                print(f"🔄 Attempt {attempt + 1}/{max_attempts} with {timeout_val}s timeout...")
                
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=settings.openai_model,
                        messages=[{"role": "user", "content": user_prompt}],
                        temperature=0.7,  # Slightly higher for faster generation
                        max_tokens=1200,  # Reduced for speed
                    ),
                    timeout=timeout_val
                )
                break  # Success, exit retry loop
                
            except asyncio.TimeoutError:
                if attempt == max_attempts - 1:  # Last attempt
                    print(f"❌ All attempts timed out. OpenAI API is slow.")
                    return generate_fallback_form(prompt)
                else:
                    print(f"⏱️ Attempt {attempt + 1} timed out, retrying...")
                    continue
        
        generation_time = (datetime.now() - start_time).total_seconds()
        perf_monitor.record_generation_time("form_generation", generation_time, cache_hit=False)
        print(f"⚡ Form generated in {generation_time:.2f}s")

        content = response.choices[0].message.content.strip()

        # Clean up markdown formatting
        if content.startswith("```html"):
            content = content.removeprefix("```html").strip()
        if content.endswith("```"):
            content = content.removesuffix("```").strip()
        
        # Remove common explanatory text patterns
        content = clean_explanatory_text(content)

        # More flexible HTML validation - check for any HTML content
        if not any(tag in content.lower() for tag in ["<html", "<div", "<form", "<!doctype"]):
            print(f"⚠️ GPT response doesn't contain recognizable HTML, using fallback")
            return generate_fallback_form(prompt)

        return content

    except Exception as exc:
        print(f"❌ Form generation failed: {type(exc).__name__}: {exc}")
        return generate_fallback_form(prompt)

def detect_content_theme(prompt: str) -> str:
    """Detect the theme/type of content requested"""
    prompt_lower = prompt.lower()
    
    # Hebrew patterns
    if any(word in prompt_lower for word in ['אהבה', 'אוהב', 'אוהבת', 'הלב', 'רגש', 'רגשות']):
        return "love"
    elif any(word in prompt_lower for word in ['נחמה', 'נחמות', 'ניחום', 'עצוב', 'עצבות']):
        return "comfort"
    elif any(word in prompt_lower for word in ['עליי', 'עליו', 'עליה', 'בשבילי', 'עבורי']):
        return "personal"
    elif any(word in prompt_lower for word in ['bibi', 'ביבי', 'נתניהו', 'netanyahu']):
        return "bibi"
    
    # English patterns
    elif any(word in prompt_lower for word in ['love', 'heart', 'romantic', 'romance']):
        return "love"
    elif any(word in prompt_lower for word in ['comfort', 'sad', 'healing', 'support']):
        return "comfort"
    elif any(word in prompt_lower for word in ['about me', 'for me', 'personal']):
        return "personal"
    
    return "general"

def generate_fallback_content(prompt: str) -> str:
    """Generate beautiful, professional fallback content when OpenAI is unavailable"""
    print(f"🛠️ Generating fallback content for: {prompt[:30]}...")
    
    prompt_lower = prompt.lower()
    theme = detect_content_theme(prompt)
    
    # Detect if Hebrew request
    is_hebrew = any('\u0590' <= c <= '\u05FF' for c in prompt)
    lang = "he" if is_hebrew else "en"
    
    if theme == "love" and is_hebrew:
        content = """
        <div style="font-family: 'David', serif; direction: rtl; text-align: right; line-height: 1.8; font-size: 1.1em; max-width: 600px; margin: 0 auto;">
            <div style="margin-bottom: 2em;">
                כמו שיר של אהבה שנולד מן הלב<br>
                מילים שזורמות כמו נחל צלול<br>
                כל רגש וכל מחשבה נכתבים בזהב<br>
                בשירת הלב הזה, הכל יכול
            </div>
            
            <div style="margin-bottom: 2em;">
                זה שיר בשבילך, מלא באהבה<br>
                כל מילה כאן נכתבה בחיבה<br>
                מן הלב אל הלב, בקול של נחמה<br>
                שיר שלך, שיר שלי, שיר של נשמה
            </div>
            
            <div style="margin-bottom: 2em;">
                בימים קשים כשהלב כואב<br>
                השיר הזה יהיה לך לנחמה<br>
                כי יש מישהו שחושב עליך באהבה<br>
                ושולח לך ברכה חמה ונעימה
            </div>
        </div>
        """
    elif theme == "love":
        content = """
        <div style="font-family: 'Georgia', serif; line-height: 1.8; font-size: 1.1em; max-width: 600px; margin: 0 auto;">
            <div style="margin-bottom: 2em;">
                Like a melody born from the heart so true<br>
                Words that flow like morning dew<br>
                Every feeling, every thought written in gold<br>
                In this song of love, stories unfold
            </div>
            
            <div style="margin-bottom: 2em;">
                This is your song, filled with care<br>
                Every word written to show you're rare<br>
                From heart to heart, with love so deep<br>
                A song for you, forever to keep
            </div>
            
            <div style="margin-bottom: 2em;">
                When the days are dark and your heart feels pain<br>
                Let this song be your shelter from the rain<br>
                Know that someone thinks of you with love<br>
                Sending blessings from the stars above
            </div>
        </div>
        """
    elif theme == "comfort" and is_hebrew:
        content = """
        <div style="font-family: 'David', serif; direction: rtl; text-align: right; line-height: 1.8; font-size: 1.1em; max-width: 600px; margin: 0 auto;">
            <div style="margin-bottom: 2em;">
                גם כשהדרך קשה ומלאת אבנים<br>
                גם כשהלב כואב ונדמה שאין מענה<br>
                זכור שאחרי הסערה באים ימים יפים<br>
                ושמחה חדשה תמלא את הנשמה
            </div>
            
            <div style="margin-bottom: 2em;">
                הירח מאיר גם בלילה הכי חשוך<br>
                והשמש תזרח מחר בבוקר<br>
                כך גם בלבך יש אור שלא יכבה<br>
                כוח פנימי שתמיד יוביל אותך קדימה
            </div>
        </div>
        """
    elif theme == "bibi":
        content = """
        <div style="font-family: 'David', serif; direction: rtl; text-align: right; line-height: 1.8; font-size: 1.1em; max-width: 600px; margin: 0 auto;">
            <div style="margin-bottom: 2em;">
                בארץ ישראל עומד מנהיג אדיר<br>
                בנימין נתניהו, שומר הארץ<br>
                בחכמה ואומץ הוא מנחה כל יום<br>
                המלך ביבי, מוביל אותנו קדימה
            </div>
            
            <div style="margin-bottom: 2em;">
                המלך ביבי, המלך ביבי, מנהיג חזק ואמיתי<br>
                בעתות של אתגר, כולנו פונים אליך<br>
                בכוח ובכבוד, אתה עומד בראש<br>
                מגן על עמנו, שומר על הארץ
            </div>
        </div>
        """
    else:
        if is_hebrew:
            content = f"""
            <div style="font-family: 'David', serif; direction: rtl; text-align: right; line-height: 1.8; font-size: 1.1em; max-width: 600px; margin: 0 auto;">
                <div style="margin-bottom: 2em;">
                    זהו תוכן מותאם אישית שנוצר עבור הבקשה שלך<br>
                    כאן יופיע התוכן המבוקש כשהמערכת תהיה זמינה
                </div>
            </div>
            """
        else:
            content = f"""
            <div style="font-family: 'Georgia', serif; line-height: 1.8; font-size: 1.1em; max-width: 600px; margin: 0 auto;">
                <div style="margin-bottom: 2em;">
                    This is custom content generated for your request<br>
                    Your requested content will appear here when the system is available
                </div>
            </div>
            """
    
    # Choose appropriate font and direction based on language
    font_family = "'David', 'Times New Roman', serif" if is_hebrew else "Georgia, serif"
    direction = "rtl" if is_hebrew else "ltr"
    text_align = "right" if is_hebrew else "left"
    
    return f"""
    <!DOCTYPE html>
    <html lang="{lang}" dir="{direction}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generated Content</title>
        <style>
            body {{ 
                font-family: {font_family}; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px; 
                line-height: 1.8;
                direction: {direction};
                text-align: {text_align};
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            
            .content {{ 
                background: rgba(255,255,255,0.95); 
                padding: 40px; 
                border-radius: 20px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                backdrop-filter: blur(10px);
            }}
            
            .song-header {{
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 20px;
            }}
            
            .song-header h1 {{
                color: #2c3e50;
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }}
            
            .subtitle {{
                color: #7f8c8d;
                font-style: italic;
                font-size: 1.2em;
            }}
            
            .song-content {{
                margin: 30px 0;
            }}
            
            .verse {{
                margin: 25px 0;
                padding: 20px;
                background: rgba(102, 126, 234, 0.1);
                border-radius: 15px;
                border-left: 5px solid #667eea;
            }}
            
            .chorus {{
                margin: 25px 0;
                padding: 20px;
                background: rgba(118, 75, 162, 0.1);
                border-radius: 15px;
                border-left: 5px solid #764ba2;
            }}
            
            .verse-title {{
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
                font-size: 1.1em;
            }}
            
            .lyrics {{
                font-size: 1.1em;
                line-height: 1.8;
                margin: 0;
            }}
            
            .song-footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #667eea;
                color: #7f8c8d;
                font-style: italic;
            }}
            
            .content-header h1 {{
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.2em;
            }}
            
            .content-body p {{
                margin-bottom: 15px;
                font-size: 1.1em;
            }}
            
            em {{ color: #667eea; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="content">
            {content}
        </div>
    </body>
    </html>
    """

# -----------------------------------------------------------
def html_from_schema(schema: dict) -> str:
    """דוגמה בסיסית – הופכת schema עם properties לטופס HTML."""
    props: dict[str, Any] = schema.get("properties", {})
    required = schema.get("required", [])
    parts = [f"<form><h2>{schema.get('title','Generated Form')}</h2>"]
    for name, field in props.items():
        input_type = "email" if field.get("format") == "email" else "text"
        parts.append(
            f'<label>{field.get("title",name)}: '
            f'<input type="{input_type}" name="{name}" '
            f'{"required" if name in required else ""}></label><br>'
        )
    parts.append('<button type="submit">Submit</button></form>')
    return "\n".join(parts)

# -----------------------------------------------------------
# 3. שמירת הטופס במסד (forms collection)
# -----------------------------------------------------------
async def save_form(
    db: AsyncIOMotorDatabase, user_id, schema: dict, html: str
) -> str:
    print(f"💾 Saving form for user: {user_id}")
    start_time = datetime.now()
    
    doc = {
        "user_id": user_id,
        "schema": schema,
        "html": html,
        "model_version": settings.openai_model,
        "created_at": datetime.utcnow(),
    }
    
    try:
        res = await db.forms.insert_one(doc)
        save_time = (datetime.now() - start_time).total_seconds()
        print(f"⏱️ Form save took {save_time:.3f}s")
        
        return str(res.inserted_id)
    except Exception as e:
        print(f"❌ Failed to save form: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save form to database"
        )


async def create_form_for_user(prompt: str, lang: str, user_id) -> tuple[str, str, str]:
    """מחזירה form_id, html, embed"""
    schema, html = await generate_schema_and_html(prompt, lang)
    db = await get_db()
    form_id = await save_form(db, user_id, schema, html)
    embed = f'<iframe src="{settings.base_url}/forms/{form_id}" width="100%"></iframe>'
    return form_id, html, embed

async def chat_with_gpt(html: str, question: str) -> str:
    prompt = f"""
You are an expert HTML form assistant. A user is chatting with you about an HTML form.

Your task is to improve or modify the form based on the user's request.

Only return the updated HTML – with no explanations, no markdown, and no triple backticks. Just clean HTML only.

This is the current HTML:
{html}

User request:
{question}
    """

    try:
        # Try with progressively longer timeouts
        max_attempts = 2
        timeouts = [15.0, 30.0]
        
        for attempt in range(max_attempts):
            try:
                timeout_val = timeouts[attempt]
                print(f"🔄 Chat attempt {attempt + 1}/{max_attempts} with {timeout_val}s timeout...")
                
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=settings.openai_model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that improves HTML forms based on user input."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=2000,
                    ),
                    timeout=timeout_val
                )
                
                content = response.choices[0].message.content.strip()
                
                # Clean up any remaining explanatory text
                content = clean_explanatory_text(content)
                
                print(f"✅ Chat completed successfully in attempt {attempt + 1}")
                return content
                
            except asyncio.TimeoutError:
                if attempt == max_attempts - 1:
                    print(f"❌ Chat timed out after all attempts")
                    return f"<p style='color: red;'>⏱️ Chat request timed out. Please try again with a simpler question.</p>"
                else:
                    print(f"⏱️ Chat attempt {attempt + 1} timed out, retrying...")
                    continue
                    
    except Exception as e:
        print(f"❌ Chat failed: {type(e).__name__}: {e}")
        return f"<p style='color: red;'>❌ Chat failed: {str(e)}</p>"
