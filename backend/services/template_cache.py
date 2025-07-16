"""
Template caching system for common form types
"""
import json
from typing import Dict, Tuple, Optional
from backend.services.cache import SimpleCache

class TemplateCache:
    """Cache for pre-generated form templates"""
    
    def __init__(self):
        self.cache = SimpleCache(max_size=200, ttl_seconds=7200)  # 2 hours TTL
        self.templates = self._load_common_templates()
    
    def _load_common_templates(self) -> Dict[str, Tuple[dict, str]]:
        """Load common form templates"""
        templates = {}
        
        # Contact form template
        contact_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "title": "Full Name"},
                "email": {"type": "string", "format": "email", "title": "Email"},
                "message": {"type": "string", "title": "Message"}
            },
            "required": ["name", "email", "message"]
        }
        
        contact_html = """
        <form class="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
            <h2 class="text-2xl font-bold mb-6 text-gray-800">Contact Us</h2>
            
            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2" for="name">
                    Full Name *
                </label>
                <input class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                       id="name" name="name" type="text" required>
            </div>
            
            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2" for="email">
                    Email *
                </label>
                <input class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                       id="email" name="email" type="email" required>
            </div>
            
            <div class="mb-6">
                <label class="block text-gray-700 text-sm font-bold mb-2" for="message">
                    Message *
                </label>
                <textarea class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-32" 
                          id="message" name="message" required></textarea>
            </div>
            
            <button class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition-colors" 
                    type="submit">
                Send Message
            </button>
        </form>
        """
        
        templates["contact"] = (contact_schema, contact_html)
        
        # Registration form template
        registration_schema = {
            "type": "object",
            "properties": {
                "firstName": {"type": "string", "title": "First Name"},
                "lastName": {"type": "string", "title": "Last Name"},
                "email": {"type": "string", "format": "email", "title": "Email"},
                "phone": {"type": "string", "title": "Phone"},
                "age": {"type": "integer", "title": "Age", "minimum": 1}
            },
            "required": ["firstName", "lastName", "email"]
        }
        
        registration_html = """
        <form class="max-w-lg mx-auto p-6 bg-white rounded-lg shadow-lg">
            <h2 class="text-2xl font-bold mb-6 text-gray-800">Registration Form</h2>
            
            <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="firstName">
                        First Name *
                    </label>
                    <input class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                           id="firstName" name="firstName" type="text" required>
                </div>
                <div>
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="lastName">
                        Last Name *
                    </label>
                    <input class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                           id="lastName" name="lastName" type="text" required>
                </div>
            </div>
            
            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2" for="email">
                    Email *
                </label>
                <input class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                       id="email" name="email" type="email" required>
            </div>
            
            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2" for="phone">
                    Phone
                </label>
                <input class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                       id="phone" name="phone" type="tel">
            </div>
            
            <div class="mb-6">
                <label class="block text-gray-700 text-sm font-bold mb-2" for="age">
                    Age
                </label>
                <input class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                       id="age" name="age" type="number" min="1">
            </div>
            
            <button class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md transition-colors" 
                    type="submit">
                Register
            </button>
        </form>
        """
        
        templates["registration"] = (registration_schema, registration_html)
        
        return templates
    
    def get_template(self, template_key: str) -> Optional[Tuple[dict, str]]:
        """Get a template by key"""
        return self.templates.get(template_key)
    
    def find_template_by_prompt(self, prompt: str) -> Optional[Tuple[dict, str]]:
        """Find template based on prompt keywords"""
        prompt_lower = prompt.lower()
        
        # Contact form keywords
        contact_keywords = ["contact", "contact form", "get in touch", "message", "inquiry"]
        if any(keyword in prompt_lower for keyword in contact_keywords):
            return self.get_template("contact")
        
        # Registration form keywords
        registration_keywords = ["registration", "register", "sign up", "signup", "enroll"]
        if any(keyword in prompt_lower for keyword in registration_keywords):
            return self.get_template("registration")
        
        return None
    
    def get_available_templates(self) -> Dict[str, str]:
        """Get list of available templates"""
        return {
            "contact": "Contact form with name, email, and message",
            "registration": "Registration form with personal details"
        }

# Global template cache instance
template_cache = TemplateCache()