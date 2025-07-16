# backend/services/form_generator.py
from __future__ import annotations
import json, uuid, asyncio
from datetime import datetime
from typing import Any, Dict, Tuple
import  os
import openai            # openai-python >=1.0
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from langdetect import detect

from backend.config import get_settings
from backend.db import get_db
from backend.services.cache import openai_cache
from backend.services.template_cache import template_cache

settings = get_settings()
client = openai.AsyncOpenAI(
    api_key=settings.openai_key,
    timeout=30.0,  # 30 second timeout
    max_retries=2
)


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except:
        return "en" # ברירת מחדל

async def generate_schema_and_html(prompt: str, lang: str = None) -> Tuple[dict, str]:
    if not lang:
        lang = detect_language(prompt)
    
    # Check template cache first for common forms
    template_result = template_cache.find_template_by_prompt(prompt)
    if template_result:
        print(f"🎯 Template cache hit for prompt: {prompt[:50]}...")
        return template_result
    
    # Create cache key parameters
    cache_key_params = (prompt, settings.openai_model, 0.2)
    
    # Check OpenAI cache
    cached_result = openai_cache.get(*cache_key_params)
    if cached_result:
        print(f"🚀 OpenAI cache hit for prompt: {prompt[:50]}...")
        return cached_result
    
    system_msg = (
        "You are a form generator. Return a JSON response with exactly two fields:\n"
        "schema – a valid JSON Schema (draft-07);\n"
        "html   – full HTML code of the form.\n"
        "Do not add any free text or comments."
    )

    try:
        print(f"🤖 Generating form for prompt: {prompt[:50]}...")
        start_time = datetime.now()
        
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model=settings.openai_model,
                response_format={"type": "json_object"},
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"Prompt: {prompt}\nLanguage: {lang}"},
                ],
            ),
            timeout=25.0  # 25 second timeout
        )
        
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
        print(f"💾 Cached result for prompt: {prompt[:50]}...")
        
        return result

    except asyncio.TimeoutError:
        print("❌ OpenAI request timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Form generation timed out. Please try again.",
        )
    except Exception as exc:
        print("❌ GPT response error:", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GPT response invalid: {exc}",
        )
async def generate_html_only(prompt: str, lang: str = None) -> str:
    if not lang:
        lang = detect_language(prompt)
    """
    Receives a free-form prompt and returns a complete HTML page, including <html>, <head>, and <body> tags.
    Intended for generating general-purpose pages (not necessarily forms).
    """
    if not lang:
        lang = detect_language(prompt)
    user_prompt = f"""
    Write a complete, valid HTML5 page in {lang}.
    The user requested: "{prompt}"

    Return only a fully structured HTML5 document. It must include <html>, <head>, and <body>.
    Do not include explanation. Use <style> or Tailwind classes where needed.
    """

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.8,
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```html"):
            content = content.removeprefix("```html").strip()
        if content.endswith("```"):
            content = content.removesuffix("```").strip()

        print("📥 GPT Raw HTML Output:\n", content[:500], "..." if len(content) > 500 else "")

        if "<html" not in content.lower():
            raise ValueError("GPT did not return valid HTML5 page")

        return content

    except Exception as exc:
        print("❌ GPT HTML generation failed:", exc)
        raise HTTPException(status_code=502, detail=f"HTML generation failed: {exc}")

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

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that improves HTML forms based on user input."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
