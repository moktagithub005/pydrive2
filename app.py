import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import json
import os
import tempfile
from io import BytesIO

# MUST BE FIRST: Set page config
st.set_page_config(page_title="Apple Image Uploader", page_icon="🍎")

# Initialize session state for drive connection
if 'drive' not in st.session_state:
    st.session_state.drive = None
    st.session_state.auth_success = False

def authenticate_google_drive():
    """Authenticate with Google Drive using service account"""
    try:
        # Step 1: Load SERVICE_ACCOUNT from secrets
        service_account_info = json.loads(st.secrets["google"]["SERVICE_ACCOUNT"])
        
        # Step 2: Create temporary service account file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(service_account_info, f)
            service_account_path = f.name
        
        # Step 3: Create settings dictionary (not file)
        settings = {
            'client_config_backend': 'service',
            'service_config': {
                'client_json_file_path': service_account_path,
            }
        }
        
        # Step 4: Authenticate
        gauth = GoogleAuth(settings=settings)
        gauth.ServiceAuth()
        
        # Step 5: Create drive object
        drive = GoogleDrive(gauth)
        
        # Cleanup
        if os.path.exists(service_account_path):
            os.unlink(service_account_path)
        
        return drive, True, "✅ Authenticated with Google Drive successfully!"
        
    except KeyError as e:
        return None, False, f"❌ Missing key in service account: {e}"
    except json.JSONDecodeError as e:
        return None, False, f"❌ Invalid JSON in service account: {e}"
    except Exception as e:
        return None, False, f"❌ Authentication failed: {str(e)}"

# Try to authenticate if not already done
if not st.session_state.auth_success:
    with st.spinner("🔐 Authenticating with Google Drive..."):
        drive, success, message = authenticate_google_drive()
        
        if success:
            st.session_state.drive = drive
            st.session_state.auth_success = True
            st.success(message)
        else:
            st.error(message)
            st.error("Please check your service account credentials in Streamlit secrets.")
            
            # Show debug info
            with st.expander("🔍 Debug Information"):
                st.write("Expected secrets format:")
                st.code('''
[google]
SERVICE_ACCOUNT = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY\\n-----END PRIVATE KEY-----\\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
"""
                ''')
                
                # Check if secrets exist
                try:
                    if "google" in st.secrets and "SERVICE_ACCOUNT" in st.secrets["google"]:
                        st.write("✅ SERVICE_ACCOUNT found in secrets")
                        # Try to parse JSON
                        try:
                            parsed = json.loads(st.secrets["google"]["SERVICE_ACCOUNT"])
                            required_fields = ["type", "project_id", "private_key", "client_email", "client_id"]
                            missing_fields = [field for field in required_fields if field not in parsed]
                            if missing_fields:
                                st.write(f"❌ Missing required fields: {missing_fields}")
                            else:
                                st.write("✅ All required fields present")
                        except json.JSONDecodeError:
                            st.write("❌ Invalid JSON format in SERVICE_ACCOUNT")
                    else:
                        st.write("❌ SERVICE_ACCOUNT not found in secrets")
                except Exception as e:
                    st.write(f"❌ Error checking secrets: {e}")
            
            st.stop()

# Your Google Drive folder ID for 'apple_dataset'
FOLDER_ID = "1bHPAGisgocVuTXT6BLWycQFIncCA_x4W"  # Replace with your actual folder ID

# Streamlit UI
st.title("🍎 Apple Image Uploader for AI Dataset (IARI Delhi सहयोग)")

st.markdown("""
📢 **Help us build India's largest AI-based Apple Variety Dataset!**

**भारत का सबसे बड़ा एआई आधारित सेब डेटासेट बनाने में हमारी मदद करें!**

🧠 This technology will help farmers assess **color, ripeness, and damage** of apples.

📞 संपर्क: 7876471141
📧 ईमेल: unisole.empower@gmail.com
""")

st.markdown("---")

# Only show the form if authentication was successful
if st.session_state.auth_success:
    with st.form("upload_form"):
        st.subheader("📷 Choose Image Source / छवि स्रोत चुनें")
        source = st.radio(
            "Select one / एक विकल्प चुनें:",
            ["📁 Upload from device / डिवाइस से अपलोड करें", "📸 Use camera / कैमरा से लें"]
        )

        if source == "📁 Upload from device / डिवाइस से अपलोड करें":
            uploaded_file = st.file_uploader("Upload apple image / सेब की तस्वीर अपलोड करें", type=["jpg", "jpeg", "png"])
        else:
            uploaded_file = st.camera_input("Take a picture / एक तस्वीर लें")

        st.markdown("---")
        st.subheader("🍏 Apple Metadata / सेब की जानकारी")

        col1, col2 = st.columns(2)
        with col1:
            quality = st.selectbox("Quality / गुणवत्ता", ["High / उच्च", "Medium / मध्यम", "Low / कम"])
            size = st.selectbox("Size / आकार", ["Small / छोटा", "Medium / मध्यम", "Large / बड़ा"])
        with col2:
            ripeness = st.selectbox("Ripeness / पकने की स्थिति", ["Unripe / कच्चा", "Semi-ripe / अधपका", "Ripe / पका हुआ"])

        submitted = st.form_submit_button("📤 Upload / अपलोड करें")

    # Upload to Drive
    if submitted and uploaded_file:
        try:
            st.image(uploaded_file, caption="📸 Preview / पूर्वावलोकन", use_container_width=True)

            # Compose filename from metadata
            file_name = f"{quality}_{size}_{ripeness}_{uploaded_file.name if hasattr(uploaded_file, 'name') else 'captured_image.jpg'}"

            # Create file in Drive
            with st.spinner("⬆️ Uploading to Google Drive..."):
                file_drive = st.session_state.drive.CreateFile({
                    'title': file_name,
                    'parents': [{'id': FOLDER_ID}]
                })
                
                # Create temporary file for upload
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Set content from temporary file
                file_drive.SetContentFile(tmp_file_path)
                file_drive.Upload()
                
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

            st.success("✅ File uploaded successfully! / फ़ाइल सफलतापूर्वक अपलोड हो गई!")
            st.info("🎉 धन्यवाद! यह तस्वीर हमारे AI मॉडल के लिए संग्रहित कर ली गई है।\nThank you! Your image has been saved for our AI model.")
            
        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")
            st.error("Please try again or contact support.")

else:
    st.warning("⚠️ Please fix the authentication issues above to continue.")