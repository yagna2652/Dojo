"""
Hugging Face Email Generator Demo

This script demonstrates the email generation functionality using Hugging Face models
without requiring Google API authentication.
"""

import os
import requests
from datetime import datetime
from config import DEFAULT_MODEL, PREMIUM_MODEL, MAX_NEW_TOKENS
from cost_tracker import CostTracker

# Hugging Face inference API settings
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

if not HUGGINGFACE_API_KEY:
    raise EnvironmentError("HUGGINGFACE_API_KEY environment variable is not set. Please set it before running the script.")

# Initialize cost tracker
cost_tracker = CostTracker()

def generate_email(prompt, is_vip=False):
    """Generate email content using Hugging Face API."""
    # Select model based on importance
    model = PREMIUM_MODEL if is_vip else DEFAULT_MODEL
    
    # Construct API URL for the selected model
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Format the prompt for better email generation
    formatted_prompt = f"Generate a professional email based on the following context: {prompt}"
    
    payload = {
        "inputs": formatted_prompt,
        "parameters": {"max_new_tokens": MAX_NEW_TOKENS, "temperature": 0.7}
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        if response.status_code == 200:
            result = response.json()
            # Handle different response formats from Hugging Face models
            if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
                generated_text = result[0]['generated_text']
            elif isinstance(result, dict) and 'generated_text' in result:
                generated_text = result['generated_text']
            else:
                generated_text = str(result)
                
            # Track the API usage
            output_tokens = len(generated_text.split())
            cost_tracker.track_request(model, output_tokens)
            
            return generated_text
        else:
            print(f"Hugging Face API error: {response.status_code} - {response.text}")
            return "[Error generating email]"
    except Exception as e:
        print(f"Error calling Hugging Face API: {str(e)}")
        return f"[Error: {str(e)}]"

def main():
    """Main function to demonstrate email generation."""
    # Sample data for demonstration
    sample_data = [
        {
            "name": "John Smith",
            "email": "john.smith@example.com",
            "context": "Follow up on the marketing proposal we discussed last week. Mention the budget increase of 15%.",
            "is_vip": False
        },
        {
            "name": "Sarah Johnson",
            "email": "sarah.j@example.com",
            "context": "Invitation to speak at our annual tech conference in September. Offer to cover travel expenses.",
            "is_vip": True
        },
        {
            "name": "Michael Chen",
            "email": "m.chen@example.com",
            "context": "Thank them for their recent product purchase and ask for feedback on their experience.",
            "is_vip": False
        }
    ]
    
    print("\n===== Hugging Face Email Generator Demo =====\n")
    
    for contact in sample_data:
        print(f"Generating email for {contact['name']} ({contact['email']})..." + 
              (" (VIP)" if contact['is_vip'] else ""))
        
        subject = f"Generated Email - {datetime.now().strftime('%Y-%m-%d')}"
        body = generate_email(contact['context'], contact['is_vip'])
        
        print(f"\nEmail Content (would be sent to {contact['email']}):\n")
        print(f"Subject: {subject}\n")
        print(body)
        print("\n---\n")
    
    # Print usage report at the end
    cost_tracker.print_usage_report()

if __name__ == "__main__":
    main()
