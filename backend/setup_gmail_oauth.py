"""One-time setup: get Gmail API refresh token via OAuth.

Usage: python setup_gmail_oauth.py

Prerequisites:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create project → Enable Gmail API
3. Create OAuth 2.0 Client ID (Desktop application)
4. Download credentials as credentials.json and put it in this directory
5. Run this script — it opens a browser for you to authorize
6. Copy the refresh token into your .env file
"""
import os
import pickle

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "gmail_token.pickle"


def main():
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"""
========================================
  Missing {CREDENTIALS_FILE}
========================================

Please follow these steps:

1. Visit https://console.cloud.google.com/apis/credentials
2. Create a new project (or select existing)
3. Go to "Library" → search "Gmail API" → Enable
4. Go to "Credentials" → Create Credentials → OAuth client ID
5. Application type: Desktop application
6. Download the JSON file
7. Rename it to credentials.json
8. Place it in: {os.getcwd()}
9. Run this script again
""")
        return

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n========================================")
    print("  OAuth Successful! Add to .env:")
    print("========================================")
    print(f"GMAIL_CLIENT_ID={creds.client_id}")
    print(f"GMAIL_CLIENT_SECRET={creds.client_secret}")
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
    print("\nAlso add to EMAIL_ACCOUNTS:")
    print("EMAIL_ACCOUNTS=your@gmail.com:gmail_api:::")

    # Save token for future use
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)
    print(f"\nToken saved to {TOKEN_FILE}")


if __name__ == "__main__":
    main()
