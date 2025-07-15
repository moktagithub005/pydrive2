#!/usr/bin/env python3
"""
Improved Google Drive Authentication Script for PyDrive2
This script generates fresh tokens and handles common authentication issues
"""

import os
import json
import time
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def main():
    print("🔐 Google Drive Authentication Script")
    print("=" * 50)
    
    # Check if credentials.json exists
    if not os.path.exists("credentials.json"):
        print("❌ Error: credentials.json not found!")
        print("\nTo fix this:")
        print("1. Go to Google Cloud Console")
        print("2. Create OAuth 2.0 credentials")
        print("3. Download as credentials.json")
        print("4. Place it in the same directory as this script")
        return
    
    try:
        # Clean up any existing token files
        if os.path.exists("token.json"):
            print("🗑️ Removing old token.json...")
            os.remove("token.json")
        
        if os.path.exists("credentials.dat"):
            print("🗑️ Removing old credentials.dat...")
            os.remove("credentials.dat")
        
        # Initialize GoogleAuth
        print("🔧 Initializing Google Auth...")
        gauth = GoogleAuth()
        
        # Load client configuration
        gauth.LoadClientConfigFile("credentials.json")
        
        # Configure OAuth settings
        gauth.settings['oauth_scope'] = ["https://www.googleapis.com/auth/drive"]
        gauth.settings['get_refresh_token'] = True
        
        # Force fresh authentication
        print("🌐 Starting authentication process...")
        print("📖 This will open a browser window for authentication")
        print("⚠️  Make sure to:")
        print("   - Use the same Google account as your Drive")
        print("   - Accept all permissions")
        print("   - Complete the full authorization flow")
        
        # Wait for user confirmation
        input("\n🔄 Press Enter when ready to continue...")
        
        # Perform authentication
        gauth.LocalWebserverAuth()
        
        # Save credentials
        print("💾 Saving credentials...")
        gauth.SaveCredentialsFile("token.json")
        
        # Test the connection
        print("🧪 Testing Google Drive connection...")
        drive = GoogleDrive(gauth)
        
        # Try to list files to verify access
        file_list = drive.ListFile({'q': "'root' in parents and trashed=false", 'maxResults': 5}).GetList()
        print(f"✅ Success! Found {len(file_list)} files in your Google Drive")
        
        # Show token content for Streamlit
        print("\n" + "=" * 50)
        print("📋 STREAMLIT SECRETS CONFIGURATION")
        print("=" * 50)
        
        # Read credentials.json
        with open("credentials.json", "r") as f:
            credentials_content = f.read().strip()
        
        # Read token.json
        with open("token.json", "r") as f:
            token_content = f.read().strip()
        
        print("\n🔧 Add this to your Streamlit secrets.toml:")
        print("\n[google]")
        print(f'CREDENTIALS = \'\'\'{credentials_content}\'\'\'')
        print(f'TOKEN = \'\'\'{token_content}\'\'\'')
        
        print("\n" + "=" * 50)
        print("📝 ALTERNATIVE: Environment Variables")
        print("=" * 50)
        print("\n🔧 Or set these environment variables:")
        print(f'export GOOGLE_CREDENTIALS=\'{credentials_content}\'')
        print(f'export GOOGLE_TOKEN=\'{token_content}\'')
        
        # Verify token structure
        token_data = json.loads(token_content)
        print("\n" + "=" * 50)
        print("🔍 TOKEN VERIFICATION")
        print("=" * 50)
        
        required_fields = ['access_token', 'refresh_token', 'token_expiry']
        missing_fields = []
        
        for field in required_fields:
            if field in token_data:
                print(f"✅ {field}: Present")
            else:
                print(f"❌ {field}: Missing")
                missing_fields.append(field)
        
        if missing_fields:
            print(f"\n⚠️  WARNING: Missing fields: {missing_fields}")
            print("This may cause authentication issues.")
        else:
            print("\n✅ Token structure looks good!")
        
        # Additional validation
        print("\n" + "=" * 50)
        print("🔧 TROUBLESHOOTING INFO")
        print("=" * 50)
        
        if 'token_expiry' in token_data:
            from datetime import datetime
            try:
                expiry_time = datetime.fromisoformat(token_data['token_expiry'].replace('Z', '+00:00'))
                current_time = datetime.now(expiry_time.tzinfo)
                if expiry_time > current_time:
                    print("✅ Token is currently valid")
                else:
                    print("⚠️  Token is expired (but has refresh_token)")
            except:
                print("⚠️  Could not parse token expiry")
        
        print(f"📍 Token saved to: {os.path.abspath('token.json')}")
        print(f"📍 Credentials at: {os.path.abspath('credentials.json')}")
        
        print("\n" + "=" * 50)
        print("✅ AUTHENTICATION COMPLETE!")
        print("=" * 50)
        print("🚀 You can now use this token in your Streamlit app")
        print("📖 Copy the secrets configuration above to your Streamlit secrets")
        
    except Exception as e:
        print(f"\n❌ Authentication failed: {str(e)}")
        print("\n🔧 Common fixes:")
        print("1. Check your credentials.json file")
        print("2. Ensure Google Drive API is enabled")
        print("3. Verify OAuth consent screen is configured")
        print("4. Try with a different Google account")
        print("5. Check your internet connection")
        print("6. Make sure you're using the correct Google Cloud project")
        
        # Show detailed error info
        import traceback
        print("\n🐛 Detailed error information:")
        traceback.print_exc()

if __name__ == "__main__":
    main()