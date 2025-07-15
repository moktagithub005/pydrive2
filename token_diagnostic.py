#!/usr/bin/env python3
"""
Token Diagnostic Script
This script helps diagnose and fix token-related issues
"""

import json
import os
import sys
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def main():
    print("🔍 Google Drive Token Diagnostic")
    print("=" * 50)
    
    # Check for required files
    files_to_check = {
        "credentials.json": "OAuth client credentials",
        "token.json": "OAuth access token",
        "service-account.json": "Service account credentials"
    }
    
    existing_files = {}
    for file, description in files_to_check.items():
        if os.path.exists(file):
            existing_files[file] = description
            print(f"✅ Found {file} ({description})")
        else:
            print(f"❌ Missing {file} ({description})")
    
    if not existing_files:
        print("\n❌ No credential files found!")
        print("Please run the authentication script first.")
        return
    
    # Analyze each file
    print("\n" + "=" * 50)
    print("📊 FILE ANALYSIS")
    print("=" * 50)
    
    for file, description in existing_files.items():
        print(f"\n🔍 Analyzing {file}:")
        analyze_file(file)
    
    # Test authentication methods
    print("\n" + "=" * 50)
    print("🧪 AUTHENTICATION TESTS")
    print("=" * 50)
    
    if "token.json" in existing_files and "credentials.json" in existing_files:
        print("\n🔧 Testing OAuth method...")
        test_oauth_auth()
    
    if "service-account.json" in existing_files:
        print("\n🔧 Testing service account method...")
        test_service_account_auth()
    
    # Show recommendations
    print("\n" + "=" * 50)
    print("💡 RECOMMENDATIONS")
    print("=" * 50)
    show_recommendations()

def analyze_file(filename):
    """Analyze a credential file"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        if filename == "credentials.json":
            analyze_oauth_credentials(data)
        elif filename == "token.json":
            analyze_oauth_token(data)
        elif filename == "service-account.json":
            analyze_service_account(data)
            
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON format in {filename}")
    except Exception as e:
        print(f"❌ Error reading {filename}: {str(e)}")

def analyze_oauth_credentials(data):
    """Analyze OAuth credentials file"""
    if "installed" in data:
        creds = data["installed"]
        print("✅ OAuth credentials structure: Valid")
        print(f"📱 Client ID: {creds.get('client_id', 'Missing')[:20]}...")
        print(f"🔐 Client Secret: {'Present' if creds.get('client_secret') else 'Missing'}")
        print(f"🔗 Redirect URIs: {len(creds.get('redirect_uris', []))} configured")
    else:
        print("❌ OAuth credentials structure: Invalid")

def analyze_oauth_token(data):
    """Analyze OAuth token file"""
    required_fields = ['access_token', 'refresh_token', 'token_expiry']
    
    for field in required_fields:
        if field in data:
            print(f"✅ {field}: Present")
        else:
            print(f"❌ {field}: Missing")
    
    if 'token_expiry' in data:
        try:
            expiry_str = data['token_expiry']
            # Handle different date formats
            if expiry_str.endswith('Z'):
                expiry_str = expiry_str[:-1] + '+00:00'
            
            expiry_time = datetime.fromisoformat(expiry_str)
            current_time = datetime.now(expiry_time.tzinfo)
            
            if expiry_time > current_time:
                print("✅ Token expiry: Valid (not expired)")
            else:
                print("⚠️  Token expiry: Expired (but can be refreshed)")
                
        except Exception as e:
            print(f"❌ Token expiry: Cannot parse ({str(e)})")

def analyze_service_account(data):
    """Analyze service account file"""
    if data.get('type') == 'service_account':
        print("✅ Service account structure: Valid")
        print(f"📧 Client email: {data.get('client_email', 'Missing')}")
        print(f"🆔 Project ID: {data.get('project_id', 'Missing')}")
        print(f"🔐 Private key: {'Present' if data.get('private_key') else 'Missing'}")
    else:
        print("❌ Service account structure: Invalid")

def test_oauth_auth():
    """Test OAuth authentication"""
    try:
        gauth = GoogleAuth()
        gauth.LoadClientConfigFile("credentials.json")
        gauth.settings['oauth_scope'] = ["https://www.googleapis.com/auth/drive"]
        gauth.settings['get_refresh_token'] = True
        
        # Try to load existing credentials
        gauth.LoadCredentialsFile("token.json")
        
        if gauth.credentials is None:
            print("❌ No valid credentials found")
            return False
        elif gauth.access_token_expired:
            print("⏳ Token expired, attempting refresh...")
            try:
                gauth.Refresh()
                print("✅ Token refreshed successfully")
            except Exception as e:
                print(f"❌ Token refresh failed: {str(e)}")
                return False
        else:
            print("✅ Existing token is valid")
        
        gauth.Authorize()
        
        # Test drive connection
        drive = GoogleDrive(gauth)
        file_list = drive.ListFile({'q': "'root' in parents and trashed=false", 'maxResults': 1}).GetList()
        
        print(f"✅ OAuth authentication successful! Can access {len(file_list)} files")
        return True
        
    except Exception as e:
        print(f"❌ OAuth authentication failed: {str(e)}")
        return False

def test_service_account_auth():
    """Test service account authentication"""
    try:
        with open("service-account.json", 'r') as f:
            service_account_info = json.load(f)
        
        gauth = GoogleAuth()
        gauth.settings['service_config'] = {
            'client_service_email': service_account_info['client_email'],
            'client_service_key_file': 'service-account.json',
            'client_pkl_file': None,
            'client_secrets_file': None
        }
        
        gauth.ServiceAuth()
        
        # Test drive connection
        drive = GoogleDrive(gauth)
        file_list = drive.ListFile({'q': "'root' in parents and trashed=false", 'maxResults': 1}).GetList()
        
        print(f"✅ Service account authentication successful! Can access {len(file_list)} files")
        return True
        
    except Exception as e:
        print(f"❌ Service account authentication failed: {str(e)}")
        return False

def show_recommendations():
    """Show recommendations based on findings"""
    print("\n🎯 Based on the analysis:")
    
    print("\n📋 For immediate fix:")
    print("1. Delete all existing token files")
    print("2. Run a fresh authentication")
    print("3. Use the same Google account consistently")
    print("4. Ensure stable internet connection during auth")
    
    print("\n🏭 For production deployment:")
    print("1. Consider using service account instead of OAuth")
    print("2. Service accounts don't expire like OAuth tokens")
    print("3. Share your Drive folder with service account email")
    print("4. Store credentials securely in environment variables")
    
    print("\n🔧 Common fixes for 'invalid_grant' error:")
    print("1. Generate token on the same machine/environment")
    print("2. Check system clock is accurate")
    print("3. Ensure OAuth consent screen is properly configured")
    print("4. Use the correct Google Cloud project")
    print("5. Don't mix tokens from different projects/accounts")
    
    print("\n💻 For Streamlit Cloud:")
    print("1. Use Streamlit secrets for credential storage")
    print("2. Never commit credentials to version control")
    print("3. Test authentication locally first")
    print("4. Consider using service account for stability")

if __name__ == "__main__":
    main()