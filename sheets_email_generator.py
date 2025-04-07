"""
Google Sheets Email Generator with Hugging Face API

This script reads data from a public Google Sheet and generates email content
using Hugging Face models.
"""

import os
import requests
import pandas as pd
from datetime import datetime
from config import DEFAULT_MODEL, PREMIUM_MODEL, MAX_NEW_TOKENS, SPREADSHEET_ID
from cost_tracker import CostTracker

# Hugging Face inference API settings
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

if not HUGGINGFACE_API_KEY:
    raise EnvironmentError("HUGGINGFACE_API_KEY environment variable is not set. Please set it before running the script.")

# Initialize cost tracker
cost_tracker = CostTracker()

def read_sheet_data(sheet_id=None):
    """
    Read data from a Google Sheet using its public CSV export URL.
    This only works for sheets that are publicly accessible or shared with anyone with the link.
    """
    if not sheet_id:
        sheet_id = SPREADSHEET_ID
        
    try:
        # Construct the CSV export URL for the Google Sheet
        # Format: https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        
        print(f"Fetching data from Google Sheet: {sheet_url}")
        
        # Read the CSV data into a pandas DataFrame
        df = pd.read_csv(sheet_url)
        
        print(f"Successfully read sheet with {len(df)} rows and columns: {', '.join(df.columns)}")
        return df
    except Exception as e:
        print(f"Error reading Google Sheet: {str(e)}")
        print("Make sure the sheet is publicly accessible or shared with anyone with the link.")
        return None

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

def create_email_draft(to, subject, body):
    """
    This function would normally create a Gmail draft.
    For now, it just prints the email content.
    """
    print(f"\nEmail Content (would be sent to {to}):\n")
    print(f"Subject: {subject}\n")
    print(body)
    print("\n---\n")

def main():
    """Main function to read sheet data and generate emails."""
    # For demonstration, you can specify a sheet ID as a command-line argument
    # or use a default sheet ID from config
    import sys
    sheet_id = sys.argv[1] if len(sys.argv) > 1 else SPREADSHEET_ID
    
    # Read data from Google Sheet
    df = read_sheet_data(sheet_id)
    
    if df is None or df.empty:
        print("No data found or unable to access the Google Sheet.")
        
        # Use sample data as fallback
        print("Using sample data instead...")
        df = pd.DataFrame([
            {"Name": "John Smith", "Email": "john.smith@example.com", 
             "Context": "Follow up on the marketing proposal we discussed last week. Mention the budget increase of 15%.",
             "Importance": "Regular"},
            {"Name": "Sarah Johnson", "Email": "sarah.j@example.com", 
             "Context": "Invitation to speak at our annual tech conference in September. Offer to cover travel expenses.",
             "Importance": "VIP"},
            {"Name": "Michael Chen", "Email": "m.chen@example.com", 
             "Context": "Thank them for their recent product purchase and ask for feedback on their experience.",
             "Importance": "Regular"}
        ])
    
    print("\n===== Google Sheets Email Generator with Hugging Face =====\n")
    
    # Process each row in the DataFrame
    for _, row in df.iterrows():
        try:
            # Extract data from the row
            name = row.get('Name', 'Recipient')
            email = row.get('Email', 'no-email@example.com')
            context = row.get('Context', '')
            
            # Check if this is a VIP contact
            is_vip = False
            if 'Importance' in row:
                is_vip = str(row['Importance']).upper() in ['VIP', 'HIGH', 'IMPORTANT']
            
            print(f"Generating email for {name} ({email})..." + (" (VIP)" if is_vip else ""))
            
            # Generate personalized subject with recipient's name
            subject = f"Email for {name} - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Generate email content
            body = generate_email(context, is_vip)
            
            # Create email draft (in this demo, just print the content)
            create_email_draft(email, subject, body)
            
        except Exception as e:
            print(f"Error processing row: {str(e)}")
    
    # Print usage report at the end
    cost_tracker.print_usage_report()

if __name__ == "__main__":
    main()
