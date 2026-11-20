# Sankar Group — AI Influencer Outreach Assistant

## Install
Python 3.10+ is recommended.
```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```
Fill `.env` with your Anthropic API key, sender email, brand details and Google configuration.

## Claude
Create an API key in Anthropic Console. Set `ANTHROPIC_API_KEY`. Verify the model identifier available to your account and set `CLAUDE_MODEL`.

## Gmail API
1. In Google Cloud Console, create/select a project and enable Gmail API.
2. Configure OAuth consent screen; for testing, add your own account as a test user.
3. Create OAuth Client ID → Desktop app and download the JSON.
4. Save it as `credentials/google_oauth_client.json`.
5. The first Gmail action opens Google sign-in and stores a token at `credentials/gmail_token.json`.
6. Review Google OAuth testing/verification requirements before deploying to other users.

## Google Sheets
1. Enable Google Sheets API.
2. Create a service account and download its JSON to `credentials/google_service_account.json`.
3. Create a Sheet and share it with the service account email as Editor.
4. Copy the ID from the Sheet URL into `GOOGLE_SHEET_ID`.

## Run
```bash
streamlit run app.py
```
Load demo data first. Upload CSVs with columns: `name,username,profile_url,niche,followers,email,location,bio`.

## Demo checklist
1. Load demo data.
2. Analyze one profile using Claude.
3. Generate an initial email.
4. Review and send only to a test inbox you control.
5. Demonstrate the follow-up queue logic without sending unsolicited test mail.
6. Fetch a test inbox reply and classify it.
7. Sync the CRM to Google Sheets.

## Scope and safety
This starter performs manual/CSV research. Instagram does not offer unrestricted access to arbitrary public profile data. Use official Meta APIs only where your app/account/use case is eligible. Never scrape private data or bypass platform restrictions. Use publicly displayed business contact details, comply with applicable anti-spam/privacy requirements, and suppress opted-out contacts.

This is an educational prototype, not yet a production unattended scheduler. The follow-up queue is evaluated on page refresh. A production system should use a persistent job scheduler, correlate Gmail threads, process MIME variants/pagination, and re-check replies and opt-outs immediately before sending. All AI-generated initial emails and reply drafts require human review.
