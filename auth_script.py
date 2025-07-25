
from pydrive2.auth import GoogleAuth
import json

# Setup GoogleAuth with offline access
gauth = GoogleAuth()
gauth.settings['oauth_scope'] = ['https://www.googleapis.com/auth/drive']
gauth.settings['get_refresh_token'] = True
gauth.LocalWebserverAuth()

# Save credentials to JSON
creds = json.loads(gauth.credentials.to_json())

# Print as string for Streamlit secrets.toml
print("\n--- Paste the following in your .streamlit/secrets.toml ---\n")
print("[google]")
print(f'CREDENTIALS = """{json.dumps(gauth.client_config)}"""')
print(f'TOKEN = """{json.dumps(creds)}"""')