# Google Sheets Configuration
SPREADSHEET_ID = '1l-vEUokNLIpapyUA_WADeb8aGaygHKplQKgVOuBrc_4'  # Updated with actual spreadsheet ID
RANGE_NAME = 'Sheet1!A1:C100'  # Format: SheetName!Range

# Email Configuration
EMAIL_SUBJECT = "Your Custom Email"

# Hugging Face Configuration
DEFAULT_MODEL = "gpt2"  # Standard model for regular emails
PREMIUM_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"  # More powerful model for VIP clients
MAX_NEW_TOKENS = 500  # Increased token limit for more complete emails

# Cost Management
MONTHLY_BUDGET = 50.0  # Maximum monthly budget in USD
TRACK_COSTS = True  # Enable cost tracking

# Column Names in Spreadsheet (case sensitive, should match your sheet headers)
FIRST_NAME_COLUMN = "First Name"
EMAIL_COLUMN = "Email"
CONTEXT_COLUMN = "Context"
IMPORTANCE_COLUMN = "Importance"  # Optional column for determining which model to use