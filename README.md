# Gmail Draft Generator using Google Sheets

This tool automates the process of creating personalized email drafts in Gmail using data from Google Sheets and OpenAI's language models.

## Features

- Reads contact data from Google Sheets (names, emails, context)
- Generates personalized email content using OpenAI API
- Creates draft emails in Gmail
- Optimizes API usage to minimize costs
- Tracks API usage and enforces budget limits
- Caches generated content to avoid duplicate API calls

## Setup

### Prerequisites

- Python 3.7+
- Google account with access to Google Sheets and Gmail
- Hugging Face API

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up Google Cloud Platform project:
   - Create a new project at https://console.cloud.google.com/
   - Enable the Google Sheets API and Gmail API
   - Create OAuth credentials (Desktop application)
   - Download the credentials JSON file and save it as `credentials.json` in the project directory

4. Set your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY="your-api-key"
   ```

5. Update the configuration in `config.py`:
   - Set your Google Sheets ID and range
   - Adjust other parameters as needed

### Google Sheets Format

Your Google Sheet should have at least these columns:
- First Name: The recipient's first name
- Email: The recipient's email address
- Context: Information about the recipient or the purpose of the email
- Importance (optional): Set to "VIP" to use a more advanced model

## Usage

Run the script:

```
python gmail_draft_generator.py
```

The first time you run it, a browser window will open asking you to authorize the application to access your Google account.

## Cost Management

The application includes a cost tracking system to help manage OpenAI API usage:

- Set monthly budget limits in `config.py`
- View usage statistics in the generated `api_usage.json` file
- Usage report is printed after each run

## Customization

- Modify the email templates in `generate_email_content()`
- Adjust the batch processing size in `main()`
- Configure model selection based on your needs in `config.py` 
