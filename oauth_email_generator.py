"""
OAuth-based Email Generator with Hugging Face API

This script reads data from Google Sheets using OAuth authentication,
generates email content using Hugging Face models, and creates Gmail drafts.
"""

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

# Google API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/gmail.compose'
]

def authenticate_google():
    """Authenticate with Google using OAuth."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    sheets_service = build('sheets', 'v4', credentials=creds)
    gmail_service = build('gmail', 'v1', credentials=creds)
    return sheets_service, gmail_service

def read_sheet_data(service):
    """Read data from Google Sheets using the Sheets API."""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        
        if not values:
            print("No data found in the sheet.")
            return None
            
        # Convert to list of dictionaries with header row as keys
        headers = values[0]
        data = []
        for row in values[1:]:
            # Pad row with empty strings if it's shorter than headers
            padded_row = row + [''] * (len(headers) - len(row))
            data.append(dict(zip(headers, padded_row)))
            
        print(f"Successfully read {len(data)} rows from Google Sheet")
        return data
    except Exception as e:
        print(f"Error reading Google Sheet: {str(e)}")
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
    
    # Format the prompt for better email generation with more specific instructions
    formatted_prompt = f"""
    Generate a professional and concise email based on the following context: {prompt}
    
    The email should:
    1. Have a clear subject line
    2. Start with a professional greeting
    3. Have a brief introduction paragraph
    4. Include the main message in 2-3 paragraphs
    5. End with a clear call to action
    6. Have a professional sign-off
    
    Format the email properly with appropriate spacing between paragraphs.
    """
    
    
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
    """Create a draft email in Gmail."""
    try:
        message = {
            'message': {
                'raw': create_raw_email(to, subject, body)
            }
        }
        draft = service.users().drafts().create(userId="me", body=message).execute()
        print(f"Draft created with ID: {draft['id']}")
        return draft['id']
    except Exception as e:
        print(f"Error creating Gmail draft: {str(e)}")
        # Print the email content as fallback
        print(f"\nEmail Content (would be sent to {to}):\n")
        print(f"Subject: {subject}\n")
        print(body)
        print("\n---\n")
        return None

def create_raw_email(to, subject, body):
    """Create a base64url encoded email message."""
    import base64
    from email.mime.text import MIMEText
    
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return raw

def main():
    """Main function to read sheet data, generate emails, and create drafts."""
    print("\n===== OAuth Email Generator with Hugging Face =====\n")
    
    try:
        # Authenticate with Google
        print("Authenticating with Google...")
        sheets_service, gmail_service = authenticate_google()
        
        # Read data from Google Sheet
        print(f"Reading data from Google Sheet (ID: {SPREADSHEET_ID})...")
        data = read_sheet_data(sheets_service)
        
        if not data:
            print("No data found or unable to access the Google Sheet.")
            return
        
        # Process each row in the data
        for row in data:
            try:
                # Extract data from the row
                name = row.get('Name', '')
                email = row.get('Email', '')
                context = row.get('Context', '')
                
                if not email or not context:
                    print(f"Skipping row with missing email or context: {row}")
                    continue
                
                # Check if this is a VIP contact
                is_vip = False
                if 'Importance' in row:
                    is_vip = str(row['Importance']).upper() in ['VIP', 'HIGH', 'IMPORTANT']
                
                print(f"Generating email for {name} ({email})..." + (" (VIP)" if is_vip else ""))
                
                # Generate personalized subject with recipient's name
                subject = f"Email for {name} - {datetime.now().strftime('%Y-%m-%d')}"
                
                # Generate email content
                body = generate_email(context, is_vip)
                
                # Create email draft in Gmail
                create_gmail_draft(gmail_service, email, subject, body)
                
            except Exception as e:
                print(f"Error processing row: {str(e)}")
        
        # Print usage report at the end
        cost_tracker.print_usage_report()
        
    except Exception as e:
        print(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    main()
