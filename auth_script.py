from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Create GoogleAuth instance
gauth = GoogleAuth()

# Load client config
gauth.LoadClientConfigFile("credentials.json")

# Enable refresh token
gauth.settings['oauth_scope'] = ["https://www.googleapis.com/auth/drive"]
gauth.settings['get_refresh_token'] = True

# 🔐 This opens a browser window to authorize & fetch token with refresh_token
gauth.LocalWebserverAuth()

# Save token to file
gauth.SaveCredentialsFile("token.json")

# Test the drive connection
drive = GoogleDrive(gauth)
print("✅ Authentication successful! Token saved to token.json")

# Show token so you can paste in Streamlit secrets
with open("token.json", "r") as f:
    print("\n📋 Copy this TOKEN content to Streamlit Cloud secrets:")
    print("=" * 50)
    print(f.read())
    print("=" * 50)
