#!/usr/bin/env python3
"""
Setup script for Gmail Draft Generator
This script helps users set up their environment for the Gmail Draft Generator.
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is at least 3.7."""
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 7):
        print("Error: This application requires Python 3.7 or higher.")
        print(f"Current Python version: {major}.{minor}")
        return False
    return True

def check_dependencies():
    """Check if required packages are installed and install them if needed."""
    try:
        import pip
    except ImportError:
        print("Error: pip is not installed. Please install pip first.")
        return False
    
    print("Installing required packages...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("Error installing dependencies:")
        print(result.stderr)
        return False
    
    print("Dependencies installed successfully.")
    return True

def check_credentials():
    """Check if credentials.json file exists."""
    if not os.path.exists("credentials.json"):
        print("Warning: credentials.json file not found.")
        print("You need to create a project in Google Cloud Platform and download OAuth credentials.")
        print("Follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. In the sidebar, go to APIs & Services > Dashboard")
        print("4. Click '+ ENABLE APIS AND SERVICES'")
        print("5. Search for and enable 'Google Sheets API' and 'Gmail API'")
        print("6. Go to APIs & Services > Credentials")
        print("7. Click 'CREATE CREDENTIALS' and select 'OAuth client ID'")
        print("8. Set Application type to 'Desktop application'")
        print("9. Download the JSON file and save it as 'credentials.json' in this directory")
        return False
    
    print("credentials.json file found.")
    return True

def check_openai_key():
    """Check if OpenAI API key is set."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("You need to set your OpenAI API key as an environment variable:")
        print("  export OPENAI_API_KEY='your-api-key'")
        return False
    
    print("OpenAI API key found in environment variables.")
    return True

def check_config():
    """Check if config.py is properly configured."""
    import config
    
    if config.SPREADSHEET_ID == 'your_spreadsheet_id':
        print("Warning: You need to update the SPREADSHEET_ID in config.py with your actual Google Sheet ID.")
        print("The ID is the part of your Google Sheet URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
        return False
    
    print("Configuration appears to be set up.")
    return True

def main():
    """Run all checks and provide a summary."""
    print("=== Gmail Draft Generator Setup ===\n")
    
    checks = [
        ("Python version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Google API credentials", check_credentials),
        ("OpenAI API key", check_openai_key)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        result = check_func()
        results.append((name, result))
        
    try:
        # Only check config if all previous checks passed
        if all(result for _, result in results):
            results.append(("Configuration", check_config()))
    except ImportError:
        results.append(("Configuration", False))
        print("Error: Could not import config.py. Ensure the file exists and is properly formatted.")
    
    print("\n=== Setup Summary ===")
    all_passed = True
    for name, result in results:
        status = "✅ Ready" if result else "❌ Action needed"
        print(f"{name}: {status}")
        all_passed = all_passed and result
    
    if all_passed:
        print("\nSetup complete! You can now run the application with:")
        print("  python gmail_draft_generator.py")
    else:
        print("\nSome setup steps need attention. Please address the issues marked with ❌")

if __name__ == "__main__":
    main() 