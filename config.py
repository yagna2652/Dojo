"""
Configuration settings for the Gmail Draft Generator application.

This module contains all configurable parameters for the application, organized by category.
Modify these settings to customize the behavior of the email generator.
"""

# Google Sheets Configuration
# --------------------------
# The ID of the Google Sheet containing contact information
SPREADSHEET_ID = '1l-vEUokNLIpapyUA_WADeb8aGaygHKplQKgVOuBrc_4'

# Range of cells to read from the sheet (format: SheetName!Range)
RANGE_NAME = 'Sheet1!A1:C100'


# Email Configuration
# ------------------
# Default subject line template (recipient name will be added)
EMAIL_SUBJECT_TEMPLATE = "Your Custom Email"


# Hugging Face Model Configuration
# ------------------------------
# Model for standard contacts
DEFAULT_MODEL = "gpt2"

# Model for VIP contacts (higher quality but more expensive)
PREMIUM_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

# Maximum number of tokens to generate for each email
MAX_NEW_TOKENS = 500


# Cost Management Settings
# -----------------------
# Maximum monthly budget in USD
MONTHLY_BUDGET = 50.0

# Whether to track and report API usage costs
TRACK_COSTS = True


# Spreadsheet Column Names
# -----------------------
# These should exactly match your Google Sheet headers (case-sensitive)
COLUMN_NAME = "Name"
COLUMN_EMAIL = "Email"
COLUMN_CONTEXT = "Context"
COLUMN_IMPORTANCE = "Importance"