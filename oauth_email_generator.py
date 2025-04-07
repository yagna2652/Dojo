"""
OAuth-based Email Generator with Hugging Face API

This script reads data from Google Sheets using OAuth authentication,
generates email content using Hugging Face models, and creates Gmail drafts.
"""

import os
import base64
import logging
import requests
from datetime import datetime
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Tuple, Any

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

from config import SPREADSHEET_ID, RANGE_NAME, DEFAULT_MODEL, PREMIUM_MODEL, MAX_NEW_TOKENS
from cost_tracker import CostTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('email_generator')

# Constants
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/gmail.compose'
]
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'
VIP_INDICATORS = ['VIP', 'HIGH', 'IMPORTANT']

# Initialize services
cost_tracker = CostTracker()

# Environment validation
def validate_environment() -> None:
    """Validate that all required environment variables are set."""
    if not os.environ.get("HUGGINGFACE_API_KEY"):
        raise EnvironmentError(
            "HUGGINGFACE_API_KEY environment variable is not set. "
            "Please set it before running the script."
        )

# Call validation at module level
validate_environment()

def authenticate_google() -> Tuple[Any, Any]:
    """
    Authenticate with Google using OAuth and return service clients.
    
    Returns:
        Tuple containing the Google Sheets service and Gmail service
    """
    credentials = load_or_create_credentials()
    sheets_service = build('sheets', 'v4', credentials=credentials)
    gmail_service = build('gmail', 'v1', credentials=credentials)
    
    return sheets_service, gmail_service


def load_or_create_credentials() -> Credentials:
    """
    Load existing credentials or create new ones through OAuth flow.
    
    Returns:
        Google OAuth credentials
    """
    if os.path.exists(TOKEN_FILE):
        return Credentials.from_authorized_user_file(TOKEN_FILE, GOOGLE_SCOPES)
    
    # No existing token, run the OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, GOOGLE_SCOPES)
    credentials = flow.run_local_server(port=0)
    
    # Save credentials for future use
    save_credentials(credentials)
    return credentials


def save_credentials(credentials: Credentials) -> None:
    """
    Save credentials to token file for reuse.
    
    Args:
        credentials: Google OAuth credentials to save
    """
    with open(TOKEN_FILE, 'w') as token_file:
        token_file.write(credentials.to_json())

def read_sheet_data(service: Any) -> Optional[List[Dict[str, str]]]:
    """
    Read data from Google Sheets using the Sheets API.
    
    Args:
        service: Google Sheets API service instance
        
    Returns:
        List of dictionaries containing the sheet data, or None if an error occurred
    """
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID, 
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            logger.warning("No data found in the sheet.")
            return None
        
        data = convert_sheet_values_to_dict(values)
        logger.info(f"Successfully read {len(data)} rows from Google Sheet")
        return data
        
    except HttpError as error:
        logger.error(f"Google Sheets API error: {error}")
        return None
    except Exception as error:
        logger.error(f"Unexpected error reading Google Sheet: {error}")
        return None


def convert_sheet_values_to_dict(values: List[List[str]]) -> List[Dict[str, str]]:
    """
    Convert sheet values (2D array) to a list of dictionaries.
    
    Args:
        values: 2D array of values from Google Sheets
        
    Returns:
        List of dictionaries with header row as keys
    """
    headers = values[0]
    data = []
    
    for row in values[1:]:
        # Pad row with empty strings if it's shorter than headers
        padded_row = row + [''] * (len(headers) - len(row))
        data.append(dict(zip(headers, padded_row)))
        
    return data

def generate_email(prompt: str, is_vip: bool = False) -> str:
    """
    Generate email content using Hugging Face API.
    
    Args:
        prompt: Context for email generation
        is_vip: Whether to use the premium model for VIP contacts
        
    Returns:
        Generated email text
    """
    model = select_model(is_vip)
    formatted_prompt = create_email_prompt(prompt)
    
    try:
        result = call_huggingface_api(model, formatted_prompt)
        generated_text = extract_generated_text(result)
        
        # Track API usage
        output_tokens = len(generated_text.split())
        cost_tracker.track_request(model, output_tokens)
        
        return generated_text
        
    except requests.RequestException as error:
        logger.error(f"Hugging Face API request error: {error}")
        return "[Error generating email]"
    except Exception as error:
        logger.error(f"Unexpected error generating email: {error}")
        return f"[Error: {str(error)}]"


def select_model(is_vip: bool) -> str:
    """
    Select the appropriate model based on contact importance.
    
    Args:
        is_vip: Whether the contact is a VIP
        
    Returns:
        Model identifier string
    """
    return PREMIUM_MODEL if is_vip else DEFAULT_MODEL


def create_email_prompt(context: str) -> str:
    """
    Create a structured prompt for email generation.
    
    Args:
        context: The context information for email generation
        
    Returns:
        Formatted prompt string
    """
    return f"""
    Generate a professional and concise email based on the following context: {context}
    
    The email should:
    1. Have a clear subject line
    2. Start with a professional greeting
    3. Have a brief introduction paragraph
    4. Include the main message in 2-3 paragraphs
    5. End with a clear call to action
    6. Have a professional sign-off
    
    Format the email properly with appropriate spacing between paragraphs.
    """


def call_huggingface_api(model: str, prompt: str) -> Any:
    """
    Call the Hugging Face API with the given model and prompt.
    
    Args:
        model: Hugging Face model identifier
        prompt: Formatted prompt for text generation
        
    Returns:
        API response data
        
    Raises:
        requests.RequestException: If the API request fails
    """
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    
    headers = {
        "Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": MAX_NEW_TOKENS, 
            "temperature": 0.7
        }
    }
    
    response = requests.post(api_url, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()


def extract_generated_text(result: Any) -> str:
    """
    Extract the generated text from various Hugging Face API response formats.
    
    Args:
        result: API response data
        
    Returns:
        Extracted generated text
    """
    if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
        return result[0]['generated_text']
    elif isinstance(result, dict) and 'generated_text' in result:
        return result['generated_text']
    else:
        return str(result)

def create_gmail_draft(service: Any, to: str, subject: str, body: str) -> Optional[str]:
    """
    Create a draft email in Gmail.
    
    Args:
        service: Gmail API service instance
        to: Recipient email address
        subject: Email subject
        body: Email body content
        
    Returns:
        Draft ID if successful, None otherwise
    """
    try:
        raw_message = create_raw_email(to, subject, body)
        message = {'message': {'raw': raw_message}}
        
        draft = service.users().drafts().create(
            userId="me", 
            body=message
        ).execute()
        
        draft_id = draft['id']
        logger.info(f"Draft created with ID: {draft_id}")
        return draft_id
        
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        log_fallback_email(to, subject, body)
        return None
    except Exception as error:
        logger.error(f"Unexpected error creating Gmail draft: {error}")
        log_fallback_email(to, subject, body)
        return None


def create_raw_email(to: str, subject: str, body: str) -> str:
    """
    Create a base64url encoded email message.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        
    Returns:
        Base64url encoded email message
    """
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return raw


def log_fallback_email(to: str, subject: str, body: str) -> None:
    """
    Log email content as fallback when Gmail draft creation fails.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
    """
    logger.info(f"\nEmail Content (would be sent to {to}):\n")
    logger.info(f"Subject: {subject}\n")
    logger.info(body)
    logger.info("\n---\n")

def main() -> None:
    """
    Main function to orchestrate the email generation workflow.
    
    1. Authenticates with Google
    2. Reads contact data from Google Sheets
    3. Generates personalized emails using Hugging Face
    4. Creates draft emails in Gmail
    5. Reports on API usage
    """
    logger.info("\n===== OAuth Email Generator with Hugging Face =====\n")
    
    try:
        services = setup_services()
        if not services:
            return
            
        sheets_service, gmail_service = services
        
        contacts = fetch_contacts(sheets_service)
        if not contacts:
            return
            
        process_contacts(contacts, gmail_service)
        
        # Print usage report at the end
        cost_tracker.print_usage_report()
        
    except Exception as error:
        logger.error(f"Error in main workflow: {error}")


def setup_services() -> Optional[Tuple[Any, Any]]:
    """
    Set up Google API services.
    
    Returns:
        Tuple of (sheets_service, gmail_service) if successful, None otherwise
    """
    try:
        logger.info("Authenticating with Google...")
        return authenticate_google()
    except Exception as error:
        logger.error(f"Failed to set up Google services: {error}")
        return None


def fetch_contacts(sheets_service: Any) -> Optional[List[Dict[str, str]]]:
    """
    Fetch contact data from Google Sheets.
    
    Args:
        sheets_service: Google Sheets API service instance
        
    Returns:
        List of contact data dictionaries if successful, None otherwise
    """
    logger.info(f"Reading data from Google Sheet (ID: {SPREADSHEET_ID})...")
    contacts = read_sheet_data(sheets_service)
    
    if not contacts:
        logger.warning("No data found or unable to access the Google Sheet.")
        return None
        
    return contacts


def process_contacts(contacts: List[Dict[str, str]], gmail_service: Any) -> None:
    """
    Process each contact to generate and create email drafts.
    
    Args:
        contacts: List of contact data dictionaries
        gmail_service: Gmail API service instance
    """
    for contact in contacts:
        try:
            process_single_contact(contact, gmail_service)
        except Exception as error:
            logger.error(f"Error processing contact: {error}")


def process_single_contact(contact: Dict[str, str], gmail_service: Any) -> None:
    """
    Process a single contact to generate and create an email draft.
    
    Args:
        contact: Contact data dictionary
        gmail_service: Gmail API service instance
    """
    # Extract contact data
    name = contact.get('Name', '')
    email = contact.get('Email', '')
    context = contact.get('Context', '')
    
    # Validate required fields
    if not email or not context:
        logger.warning(f"Skipping contact with missing email or context: {contact}")
        return
    
    # Determine if VIP
    is_vip = is_vip_contact(contact)
    
    logger.info(f"Generating email for {name} ({email})..." + 
               (" (VIP)" if is_vip else ""))
    
    # Generate personalized subject
    subject = create_subject(name)
    
    # Generate email content
    body = generate_email(context, is_vip)
    
    # Create email draft
    create_gmail_draft(gmail_service, email, subject, body)


def is_vip_contact(contact: Dict[str, str]) -> bool:
    """
    Determine if a contact is a VIP based on the Importance field.
    
    Args:
        contact: Contact data dictionary
        
    Returns:
        True if the contact is a VIP, False otherwise
    """
    if 'Importance' not in contact:
        return False
        
    importance = str(contact['Importance']).upper()
    return importance in VIP_INDICATORS


def create_subject(name: str) -> str:
    """
    Create a personalized email subject with the recipient's name.
    
    Args:
        name: Recipient's name
        
    Returns:
        Formatted subject string
    """
    date_str = datetime.now().strftime('%Y-%m-%d')
    return f"Email for {name} - {date_str}"

if __name__ == "__main__":
    main()
