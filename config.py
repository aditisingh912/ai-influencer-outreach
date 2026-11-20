import os
from dotenv import load_dotenv
load_dotenv()
ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY","")
CLAUDE_MODEL=os.getenv("CLAUDE_MODEL","claude-sonnet-4-5")
GOOGLE_OAUTH_CLIENT_FILE=os.getenv("GOOGLE_OAUTH_CLIENT_FILE","credentials/google_oauth_client.json")
GOOGLE_TOKEN_FILE=os.getenv("GOOGLE_TOKEN_FILE","credentials/gmail_token.json")
GOOGLE_SERVICE_ACCOUNT_FILE=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE","credentials/google_service_account.json")
GOOGLE_SHEET_ID=os.getenv("GOOGLE_SHEET_ID","")
SENDER_EMAIL=os.getenv("SENDER_EMAIL","")
BRAND_NAME=os.getenv("BRAND_NAME","Your Brand")
BRAND_DESCRIPTION=os.getenv("BRAND_DESCRIPTION","A brand seeking creator partnerships.")
DB_PATH="data/outreach.db"
