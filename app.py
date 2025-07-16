import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.client import OAuth2Credentials
import tempfile
import os

# Set page title and icon
st.set_page_config(page_title="Apple Image Uploader", page_icon="🍎")

# Session state setup
if 'drive' not in st.session_state:
    st.session_state.drive = None
    st.session_state.auth_success = False

def authenticate_google_drive():
    """Authenticate using OAuth2 with refresh token (Streamlit Cloud compatible)"""
    try:
        settings = {
            "client_config_backend": "settings",
            "client_config": {
                "client_id": st.secrets["google"]["client_id"],
                "client_secret": st.secrets["google"]["client_secret"],
                "auth_uri": st.secrets["google"]["auth_uri"],
                "token_uri": st.secrets["google"]["token_uri"],
            },
            "save_credentials": False,
            "get_refresh_token": True,
            "oauth_scope": ["https://www.googleapis.com/auth/drive.file"]
        }

        gauth = GoogleAuth(settings=settings)

        # Load refresh token from Streamlit secrets
        if "refresh_token" in st.secrets["google"]:
            creds = OAuth2Credentials(
                access_token=None,
                client_id=st.secrets["google"]["client_id"],
                client_secret=st.secrets["google"]["client_secret"],
                refresh_token=st.secrets["google"]["refresh_token"],
                token_expiry=None,
                token_uri=st.secrets["google"]["token_uri"],
                user_agent="streamlit"
            )
            gauth.credentials = creds
            gauth.Refresh()
        else:
            # First time only: Launch browser to get refresh token
            gauth.LocalWebserverAuth()
            st.warning("🔐 Copy the following refresh token and paste it into Streamlit Cloud secrets:")
            st.code(gauth.credentials.refresh_token)
            st.stop()

        drive = GoogleDrive(gauth)
        return drive, True, "✅ Google Drive authenticated with OAuth2!"

    except Exception as e:
        return None, False, f"❌ OAuth2 Authentication Failed: {str(e)}"

# Run auth
if not st.session_state.auth_success:
    with st.spinner("🔐 Authenticating with Google Drive..."):
        drive, success, message = authenticate_google_drive()

        if success:
            st.session_state.drive = drive
            st.session_state.auth_success = True
            st.success(message)
        else:
            st.error(message)
            st.stop()

# Your Google Drive folder ID (replace this with your own folder inside Drive)
FOLDER_ID = "1bHPAGisgocVuTXT6BLWycQFIncCA_x4W"  # 'apple_dataset'

# App Header
st.title("🍎 Apple Image Uploader for AI Dataset (IARI Delhi सहयोग)")

st.markdown("""
📢 **Help us build India's largest AI-based Apple Variety Dataset!**  
**भारत का सबसे बड़ा एआई आधारित सेब डेटासेट बनाने में हमारी मदद करें!**

🧠 This technology will help farmers assess **color, ripeness, and damage** of apples.

📞 संपर्क: 7876471141  
📧 ईमेल: unisole.empower@gmail.com
""")
st.markdown("---")

# Upload form
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

    if submitted and uploaded_file:
        try:
            st.image(uploaded_file, caption="📸 Preview / पूर्वावलोकन", use_container_width=True)

            file_name = f"{quality}_{size}_{ripeness}_{uploaded_file.name if hasattr(uploaded_file, 'name') else 'captured_image.jpg'}"

            with st.spinner("⬆️ Uploading to Google Drive..."):
                file_drive = st.session_state.drive.CreateFile({
                    'title': file_name,
                    'parents': [{'id': FOLDER_ID}]
                })

                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                file_drive.SetContentFile(tmp_file_path)
                file_drive.Upload()

                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

            st.success("✅ File uploaded successfully!")
            st.info("🎉 धन्यवाद! यह तस्वीर हमारे AI मॉडल के लिए संग्रहित कर ली गई है।")

        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")
else:
    st.warning("⚠️ Google Drive authentication required.")
