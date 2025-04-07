import os
import requests
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from config import SPREADSHEET_ID, RANGE_NAME, DEFAULT_MODEL, PREMIUM_MODEL, MAX_NEW_TOKENS
from cost_tracker import CostTracker

# Hugging Face inference API settings
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

if not HUGGINGFACE_API_KEY:
    raise EnvironmentError("HUGGINGFACE_API_KEY environment variable is not set. Please set it before running the script.")

# Initialize cost tracker
cost_tracker = CostTracker()

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/gmail.compose'
]

def authenticate_google():
    # For testing purposes only - using API key instead of OAuth
    # In a production environment, you should use OAuth as originally implemented
    try:
        # Try to read API key from environment variable
        api_key = os.environ.get('GOOGLE_API_KEY')
        
        if not api_key:
            print("\nWARNING: GOOGLE_API_KEY environment variable not set.")
            print("For testing only: Using sheets API with developer key.")
            print("This will only work for public Google Sheets or those shared with anyone with the link.")
            print("For Gmail functionality, you'll need to set up proper OAuth.\n")
        
        # Build the Sheets service with API key (limited functionality)
        sheets_service = build('sheets', 'v4', developerKey=api_key)
        
        # For Gmail, we still need OAuth, so we'll return None for now
        # In a real implementation, you would need to complete the OAuth verification process
        print("Gmail functionality requires OAuth. Returning None for gmail_service.")
        gmail_service = None
        
        return sheets_service, gmail_service
        
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        print("To test with API key, set the GOOGLE_API_KEY environment variable.")
        print("To use full functionality, complete the Google verification process.")
        raise

def read_sheet_data(service):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    return values

def generate_email(prompt, is_vip=False):
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

def create_gmail_draft(service, to, subject, body):
    message = {
        'message': {
            'raw': create_raw_email(to, subject, body)
        }
    }
    draft = service.users().drafts().create(userId="me", body=message).execute()
    print(f"Draft created: {draft['id']}")

def create_raw_email(to, subject, body):
    import base64
    from email.mime.text import MIMEText
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return raw

def main():
    sheets_service, gmail_service = authenticate_google()
    
    try:
        rows = read_sheet_data(sheets_service)

        if not rows:
            print("No data found.")
            return
        
        # Get header row to find column indices
        headers = rows[0] if rows else []
        email_idx = headers.index("Email") if "Email" in headers else 1
        context_idx = headers.index("Context") if "Context" in headers else 2
        importance_idx = headers.index("Importance") if "Importance" in headers else -1
        
        # Process each contact (skip header row)
        for row in rows[1:]:
            if len(row) <= max(email_idx, context_idx):
                print(f"Skipping row with insufficient data: {row}")
                continue
                
            to = row[email_idx]
            prompt = row[context_idx]
            
            # Check if this is a VIP contact
            is_vip = False
            if importance_idx >= 0 and len(row) > importance_idx:
                is_vip = row[importance_idx].upper() == "VIP"
            
            print(f"Generating email for {to}..." + (" (VIP)" if is_vip else ""))
            
            subject = f"Generated Email - {datetime.now().strftime('%Y-%m-%d')}"
            body = generate_email(prompt, is_vip)
            
            # Only create Gmail draft if gmail_service is available
            if gmail_service:
                create_gmail_draft(gmail_service, to, subject, body)
            else:
                print(f"\nEmail Content (would be sent to {to}):\n")
                print(f"Subject: {subject}\n")
                print(body)
                print("\n---\n")
        
        # Print usage report at the end
        cost_tracker.print_usage_report()
        
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        print("If this is related to Google Sheets access, make sure your spreadsheet is publicly accessible or shared with anyone with the link.")

if __name__ == "__main__":
    main()