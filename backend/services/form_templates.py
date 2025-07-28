"""
Form Templates Library for AutoForms
Provides pre-built, professional form templates across various categories
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from backend.services.form_embedding import inject_submission_endpoint

@dataclass
class FormTemplate:
    """Template data structure"""
    id: str
    name: str
    description: str
    category: str
    preview_image: str  # URL or path to preview image
    html: str
    tags: List[str]

class FormTemplatesService:
    """Service for managing form templates"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> List[FormTemplate]:
        """Initialize all form templates"""
        return [
            # CONTACT FORMS
            FormTemplate(
                id="contact_basic",
                name="Basic Contact Form",
                description="Simple contact form with name, email, and message fields",
                category="contact",
                preview_image="/static/templates/contact_basic.png",
                tags=["basic", "contact", "simple"],
                html="""
<div class="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-2xl font-bold mb-6 text-gray-800">Contact Us</h2>
    <form>
        <div class="mb-4">
            <label class="block text-gray-700 text-sm font-bold mb-2" for="name">
                Full Name *
            </label>
            <input class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                   id="name" name="name" type="text" required>
        </div>
        <div class="mb-4">
            <label class="block text-gray-700 text-sm font-bold mb-2" for="email">
                Email Address *
            </label>
            <input class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                   id="email" name="email" type="email" required>
        </div>
        <div class="mb-4">
            <label class="block text-gray-700 text-sm font-bold mb-2" for="phone">
                Phone Number
            </label>
            <input class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                   id="phone" name="phone" type="tel">
        </div>
        <div class="mb-6">
            <label class="block text-gray-700 text-sm font-bold mb-2" for="message">
                Message *
            </label>
            <textarea class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                      id="message" name="message" rows="4" required></textarea>
        </div>
        <button class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition-colors" 
                type="submit">Send Message</button>
    </form>
</div>
                """
            ),
            
            FormTemplate(
                id="contact_business",
                name="Business Inquiry Form",
                description="Professional contact form for business inquiries with company details",
                category="contact",
                preview_image="/static/templates/contact_business.png",
                tags=["business", "professional", "inquiry"],
                html="""
<div class="max-w-2xl mx-auto bg-white p-8 rounded-lg shadow-lg">
    <h2 class="text-3xl font-bold mb-2 text-gray-800">Business Inquiry</h2>
    <p class="text-gray-600 mb-6">Get in touch with our team for business opportunities</p>
    <form class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="first_name">
                    First Name *
                </label>
                <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                       id="first_name" name="first_name" type="text" required>
            </div>
            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="last_name">
                    Last Name *
                </label>
                <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                       id="last_name" name="last_name" type="text" required>
            </div>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="company">
                Company Name *
            </label>
            <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                   id="company" name="company" type="text" required>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="email">
                    Business Email *
                </label>
                <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                       id="email" name="email" type="email" required>
            </div>
            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="phone">
                    Phone Number
                </label>
                <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                       id="phone" name="phone" type="tel">
            </div>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="inquiry_type">
                Inquiry Type *
            </label>
            <select class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    id="inquiry_type" name="inquiry_type" required>
                <option value="">Select inquiry type</option>
                <option value="partnership">Partnership Opportunity</option>
                <option value="service">Service Inquiry</option>
                <option value="sales">Sales Question</option>
                <option value="support">Technical Support</option>
                <option value="other">Other</option>
            </select>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="message">
                Message *
            </label>
            <textarea class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                      id="message" name="message" rows="5" required 
                      placeholder="Please describe your inquiry in detail..."></textarea>
        </div>
        <button class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-md transition-colors" 
                type="submit">Submit Inquiry</button>
    </form>
</div>
                """
            ),

            # EVENT REGISTRATION
            FormTemplate(
                id="event_registration",
                name="Event Registration",
                description="Complete event registration form with attendee details and preferences",
                category="event",
                preview_image="/static/templates/event_registration.png", 
                tags=["event", "registration", "attendee"],
                html="""
<div class="max-w-2xl mx-auto bg-white p-8 rounded-lg shadow-lg">
    <h2 class="text-3xl font-bold mb-2 text-gray-800">Event Registration</h2>
    <p class="text-gray-600 mb-6">Register for our upcoming event</p>
    <form class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="first_name">
                    First Name *
                </label>
                <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500" 
                       id="first_name" name="first_name" type="text" required>
            </div>
            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="last_name">
                    Last Name *
                </label>
                <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500" 
                       id="last_name" name="last_name" type="text" required>
            </div>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="email">
                Email Address *
            </label>
            <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500" 
                   id="email" name="email" type="email" required>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="organization">
                Organization/Company
            </label>
            <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500" 
                   id="organization" name="organization" type="text">
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="ticket_type">
                Ticket Type *
            </label>
            <select class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500" 
                    id="ticket_type" name="ticket_type" required>
                <option value="">Select ticket type</option>
                <option value="general">General Admission - Free</option>
                <option value="vip">VIP Access - $50</option>
                <option value="student">Student Discount - $25</option>
            </select>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">
                Dietary Restrictions
            </label>
            <div class="space-y-2">
                <label class="flex items-center">
                    <input type="checkbox" name="dietary[]" value="vegetarian" class="mr-2">
                    <span class="text-sm text-gray-700">Vegetarian</span>
                </label>
                <label class="flex items-center">
                    <input type="checkbox" name="dietary[]" value="vegan" class="mr-2">
                    <span class="text-sm text-gray-700">Vegan</span>
                </label>
                <label class="flex items-center">
                    <input type="checkbox" name="dietary[]" value="gluten_free" class="mr-2">
                    <span class="text-sm text-gray-700">Gluten-free</span>
                </label>
                <label class="flex items-center">
                    <input type="checkbox" name="dietary[]" value="none" class="mr-2">
                    <span class="text-sm text-gray-700">No restrictions</span>
                </label>
            </div>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="comments">
                Additional Comments
            </label>
            <textarea class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500" 
                      id="comments" name="comments" rows="3"></textarea>
        </div>
        <button class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-md transition-colors" 
                type="submit">Register for Event</button>
    </form>
</div>
                """
            ),

            # SURVEY/FEEDBACK
            FormTemplate(
                id="customer_feedback",
                name="Customer Feedback Survey",
                description="Comprehensive customer satisfaction survey with rating scales",
                category="survey",
                preview_image="/static/templates/customer_feedback.png",
                tags=["survey", "feedback", "satisfaction", "rating"],
                html="""
<div class="max-w-2xl mx-auto bg-white p-8 rounded-lg shadow-lg">
    <h2 class="text-3xl font-bold mb-2 text-gray-800">Customer Feedback</h2>
    <p class="text-gray-600 mb-6">Help us improve by sharing your experience</p>
    <form class="space-y-6">
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="name">
                Name (Optional)
            </label>
            <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500" 
                   id="name" name="name" type="text">
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="email">
                Email (Optional)
            </label>
            <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500" 
                   id="email" name="email" type="email">
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-3">
                Overall Satisfaction *
            </label>
            <div class="flex space-x-4">
                <label class="flex flex-col items-center">
                    <input type="radio" name="satisfaction" value="1" required class="mb-1">
                    <span class="text-xs text-gray-600">Very Poor</span>
                </label>
                <label class="flex flex-col items-center">
                    <input type="radio" name="satisfaction" value="2" required class="mb-1">
                    <span class="text-xs text-gray-600">Poor</span>
                </label>
                <label class="flex flex-col items-center">
                    <input type="radio" name="satisfaction" value="3" required class="mb-1">
                    <span class="text-xs text-gray-600">Average</span>
                </label>
                <label class="flex flex-col items-center">
                    <input type="radio" name="satisfaction" value="4" required class="mb-1">
                    <span class="text-xs text-gray-600">Good</span>
                </label>
                <label class="flex flex-col items-center">
                    <input type="radio" name="satisfaction" value="5" required class="mb-1">
                    <span class="text-xs text-gray-600">Excellent</span>
                </label>
            </div>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="service_quality">
                How would you rate our service quality? *
            </label>
            <select class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500" 
                    id="service_quality" name="service_quality" required>
                <option value="">Please select</option>
                <option value="excellent">Excellent</option>
                <option value="good">Good</option>
                <option value="average">Average</option>
                <option value="poor">Poor</option>
                <option value="very_poor">Very Poor</option>
            </select>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-3">
                Which areas need improvement? (Select all that apply)
            </label>
            <div class="space-y-2">
                <label class="flex items-center">
                    <input type="checkbox" name="improvements[]" value="customer_service" class="mr-2">
                    <span class="text-sm text-gray-700">Customer Service</span>
                </label>
                <label class="flex items-center">
                    <input type="checkbox" name="improvements[]" value="product_quality" class="mr-2">
                    <span class="text-sm text-gray-700">Product Quality</span>
                </label>
                <label class="flex items-center">
                    <input type="checkbox" name="improvements[]" value="delivery_speed" class="mr-2">
                    <span class="text-sm text-gray-700">Delivery Speed</span>
                </label>
                <label class="flex items-center">
                    <input type="checkbox" name="improvements[]" value="website_usability" class="mr-2">
                    <span class="text-sm text-gray-700">Website Usability</span>
                </label>
                <label class="flex items-center">
                    <input type="checkbox" name="improvements[]" value="pricing" class="mr-2">
                    <span class="text-sm text-gray-700">Pricing</span>
                </label>
            </div>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">
                Would you recommend us to others? *
            </label>
            <div class="space-y-2">
                <label class="flex items-center">
                    <input type="radio" name="recommend" value="definitely" required class="mr-2">
                    <span class="text-sm text-gray-700">Definitely</span>
                </label>
                <label class="flex items-center">
                    <input type="radio" name="recommend" value="probably" required class="mr-2">
                    <span class="text-sm text-gray-700">Probably</span>
                </label>
                <label class="flex items-center">
                    <input type="radio" name="recommend" value="maybe" required class="mr-2">
                    <span class="text-sm text-gray-700">Maybe</span>
                </label>
                <label class="flex items-center">
                    <input type="radio" name="recommend" value="probably_not" required class="mr-2">
                    <span class="text-sm text-gray-700">Probably Not</span>
                </label>
                <label class="flex items-center">
                    <input type="radio" name="recommend" value="definitely_not" required class="mr-2">
                    <span class="text-sm text-gray-700">Definitely Not</span>
                </label>
            </div>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="comments">
                Additional Comments
            </label>
            <textarea class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500" 
                      id="comments" name="comments" rows="4" 
                      placeholder="Please share any additional feedback or suggestions..."></textarea>
        </div>
        <button class="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-md transition-colors" 
                type="submit">Submit Feedback</button>
    </form>
</div>
                """
            ),

            # LEAD GENERATION
            FormTemplate(
                id="newsletter_signup",
                name="Newsletter Signup",
                description="Simple newsletter subscription form with preferences",
                category="lead_generation",
                preview_image="/static/templates/newsletter_signup.png",
                tags=["newsletter", "subscription", "email", "marketing"],
                html="""
<div class="max-w-md mx-auto bg-gradient-to-br from-blue-50 to-indigo-100 p-8 rounded-lg shadow-lg">
    <h2 class="text-2xl font-bold mb-2 text-gray-800">Stay Updated!</h2>
    <p class="text-gray-600 mb-6">Join our newsletter for the latest updates and exclusive content</p>
    <form class="space-y-4">
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="email">
                Email Address *
            </label>
            <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500" 
                   id="email" name="email" type="email" required placeholder="your@email.com">
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="first_name">
                First Name
            </label>
            <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500" 
                   id="first_name" name="first_name" type="text">
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-3">
                What interests you? (Optional)
            </label>
            <div class="space-y-2">
                <label class="flex items-center">
                    <input type="checkbox" name="interests[]" value="tech_news" class="mr-2">
                    <span class="text-sm text-gray-700">Tech News</span>
                </label>
                <label class="flex items-center">
                    <input type="checkbox" name="interests[]" value="product_updates" class="mr-2">
                    <span class="text-sm text-gray-700">Product Updates</span>
                </label>
                <label class="flex items-center">
                    <input type="checkbox" name="interests[]" value="industry_insights" class="mr-2">
                    <span class="text-sm text-gray-700">Industry Insights</span>
                </label>
                <label class="flex items-center">
                    <input type="checkbox" name="interests[]" value="special_offers" class="mr-2">
                    <span class="text-sm text-gray-700">Special Offers</span>
                </label>
            </div>
        </div>
        <div>
            <label class="flex items-start">
                <input type="checkbox" name="privacy_agree" required class="mr-2 mt-1">
                <span class="text-xs text-gray-600">I agree to receive marketing emails and understand I can unsubscribe at any time</span>
            </label>
        </div>
        <button class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-md transition-colors" 
                type="submit">Subscribe Now</button>
    </form>
    <p class="text-xs text-gray-500 mt-4 text-center">No spam, unsubscribe anytime</p>
</div>
                """
            ),

            # JOB APPLICATION
            FormTemplate(
                id="job_application",
                name="Job Application Form",
                description="Complete job application form with personal details and experience",
                category="application",
                preview_image="/static/templates/job_application.png",
                tags=["job", "application", "employment", "career"],
                html="""
<div class="max-w-3xl mx-auto bg-white p-8 rounded-lg shadow-lg">
    <h2 class="text-3xl font-bold mb-2 text-gray-800">Job Application</h2>
    <p class="text-gray-600 mb-6">Please fill out all required fields</p>
    <form class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="first_name">
                    First Name *
                </label>
                <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500" 
                       id="first_name" name="first_name" type="text" required>
            </div>
            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="last_name">
                    Last Name *
                </label>
                <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500" 
                       id="last_name" name="last_name" type="text" required>
            </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="email">
                    Email Address *
                </label>
                <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500" 
                       id="email" name="email" type="email" required>
            </div>
            <div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="phone">
                    Phone Number *
                </label>
                <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500" 
                       id="phone" name="phone" type="tel" required>
            </div>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="position">
                Position Applied For *
            </label>
            <select class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500" 
                    id="position" name="position" required>
                <option value="">Select a position</option>
                <option value="software_engineer">Software Engineer</option>
                <option value="product_manager">Product Manager</option>
                <option value="ux_designer">UX Designer</option>
                <option value="data_analyst">Data Analyst</option>
                <option value="marketing_specialist">Marketing Specialist</option>
                <option value="sales_representative">Sales Representative</option>
                <option value="other">Other</option>
            </select>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="experience">
                Years of Experience *
            </label>
            <select class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500" 
                    id="experience" name="experience" required>
                <option value="">Select experience level</option>
                <option value="0-1">0-1 years (Entry Level)</option>
                <option value="2-5">2-5 years</option>
                <option value="6-10">6-10 years</option>
                <option value="10+">10+ years (Senior Level)</option>
            </select>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="education">
                Highest Education Level *
            </label>
            <select class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500" 
                    id="education" name="education" required>
                <option value="">Select education level</option>
                <option value="high_school">High School Diploma</option>
                <option value="associates">Associate's Degree</option>
                <option value="bachelors">Bachelor's Degree</option>
                <option value="masters">Master's Degree</option>
                <option value="phd">PhD</option>
                <option value="other">Other</option>
            </select>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="skills">
                Key Skills & Technologies
            </label>
            <textarea class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500" 
                      id="skills" name="skills" rows="3" 
                      placeholder="List your relevant skills, technologies, and tools..."></textarea>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="cover_letter">
                Cover Letter / Why are you interested in this position? *
            </label>
            <textarea class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500" 
                      id="cover_letter" name="cover_letter" rows="5" required
                      placeholder="Tell us about yourself and why you'd be a great fit..."></textarea>
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="salary_expectation">
                Salary Expectation (Optional)
            </label>
            <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500" 
                   id="salary_expectation" name="salary_expectation" type="text" 
                   placeholder="e.g., $50,000 - $60,000">
        </div>
        <div>
            <label class="block text-gray-700 text-sm font-bold mb-2" for="start_date">
                Available Start Date
            </label>
            <input class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500" 
                   id="start_date" name="start_date" type="date">
        </div>
        <button class="w-full bg-orange-600 hover:bg-orange-700 text-white font-bold py-3 px-6 rounded-md transition-colors" 
                type="submit">Submit Application</button>
    </form>
</div>
                """
            )
        ]
    
    def get_all_templates(self) -> List[FormTemplate]:
        """Get all available templates"""
        return self.templates
    
    def get_template_by_id(self, template_id: str) -> Optional[FormTemplate]:
        """Get a specific template by ID"""
        for template in self.templates:
            if template.id == template_id:
                return template
        return None
    
    def get_templates_by_category(self, category: str) -> List[FormTemplate]:
        """Get templates filtered by category"""
        return [t for t in self.templates if t.category == category]
    
    def get_categories(self) -> List[str]:
        """Get all available categories"""
        categories = set(t.category for t in self.templates)
        return sorted(list(categories))
    
    def search_templates(self, query: str) -> List[FormTemplate]:
        """Search templates by name, description, or tags"""
        query = query.lower()
        results = []
        for template in self.templates:
            if (query in template.name.lower() or 
                query in template.description.lower() or 
                any(query in tag.lower() for tag in template.tags)):
                results.append(template)
        return results

# Global service instance
form_templates_service = FormTemplatesService()