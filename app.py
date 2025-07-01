import streamlit as st
import json
import os
import io
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from PIL import Image
import uuid
from datetime import datetime
import base64

# ✅ Page config must come FIRST - remove duplicate
st.set_page_config(
    page_title="Apple Image Collector - TEAM UNISOLE", 
    layout="centered",
    page_icon="🍎"
)

# Authenticate Google Drive using Streamlit secrets (Streamlit Cloud compatible)
@st.cache_resource
def connect_drive():
    try:
        # Set up credentials from Streamlit secrets
        credentials_json = st.secrets["google"]["CREDENTIALS"]
        token_json = st.secrets["google"].get("TOKEN", "{}")
        
        # Save credentials to temporary file
        with open("credentials.json", "w") as f:
            f.write(credentials_json)
        
        # Save token to temporary file if exists
        with open("token.json", "w") as f:
            f.write(token_json)
        
        # Auth with PyDrive2 - Streamlit Cloud compatible
        gauth = GoogleAuth()
        
        # Load client config first
        gauth.LoadClientConfigFile("credentials.json")
        
        # Try to load existing credentials
        gauth.LoadCredentialsFile("token.json")
        
        if gauth.credentials is None:
            # For Streamlit Cloud - use CommandLineAuth instead of LocalWebserverAuth
            st.error("❌ No valid token found. Please update your TOKEN in Streamlit secrets.")
            st.info("""
            **Setup Instructions:**
            1. Run the auth locally first to get token.json
            2. Copy the token.json content to Streamlit secrets as TOKEN
            3. Redeploy the app
            """)
            return None
        elif gauth.access_token_expired:
            try:
                gauth.Refresh()
                # Save refreshed token back (though it won't persist in Cloud)
                gauth.SaveCredentialsFile("token.json")
            except Exception as refresh_error:
                st.error(f"Token refresh failed: {refresh_error}")
                st.info("Please update your TOKEN in Streamlit secrets with a fresh token.")
                return None
        else:
            gauth.Authorize()
        
        return GoogleDrive(gauth)
        
    except KeyError as e:
        st.error(f"Missing Streamlit secret: {str(e)}")
        st.error("Please ensure both CREDENTIALS and TOKEN are set in [google] section of Streamlit secrets.")
        st.info("""
        **Expected format in secrets.toml:**
        ```
        [google]
        CREDENTIALS = "..."
        TOKEN = "..."
        ```
        """)
        return None
    except Exception as e:
        st.error(f"Google Drive connection failed: {str(e)}")
        st.error("Please check your credentials and token in Streamlit secrets.")
        return None

# Initialize drive connection
drive = connect_drive()

# --- Header Section ---
st.title("🍎 Apple Dataset Collector")
st.markdown("### **TEAM UNISOLE** - Incubated at IARI (Indian Agricultural Research Institute)")
st.markdown("📞 **Contact:** 7876471141 | 📧 **Email:** team.unisole@gmail.com")

# --- Mission Statement ---
st.markdown("""
---
### 🎯 Our Mission / हमारा मिशन

**English:** We are building India's largest open dataset of apple varieties to develop AI-powered tools for farmers. As an IARI-incubated startup, we're creating technology that helps farmers:
- Identify apple varieties instantly using photos
- Get better market prices through accurate variety classification
- Improve crop management with AI insights
- Access expert agricultural knowledge

**हिंदी:** हम भारत का सबसे बड़ा सेब किस्मों का डेटासेट बना रहे हैं ताकि किसानों के लिए AI-आधारित उपकरण विकसित कर सकें। IARI से इनक्यूबेटेड स्टार्टअप के रूप में, हम ऐसी तकनीक बना रहे हैं जो किसानों की मदद करती है:
- तस्वीरों से सेब की किस्मों की तुरंत पहचान करना
- सटीक किस्म वर्गीकरण के माध्यम से बेहतर बाजार मूल्य पाना
- AI अंतर्दृष्टि के साथ फसल प्रबंधन में सुधार
- विशेषज्ञ कृषि ज्ञान तक पहुंच

**🔬 Research Impact:** Your contribution will directly help build AI models that benefit the entire farming community.
---
""")

# Check if drive is connected
if drive is None:
    st.error("❌ Google Drive connection failed. Please check your credentials.")
    st.stop()

# --- Image Capture/Upload Section ---
st.subheader("📸 Share Your Apple Images / अपनी सेब की तस्वीरें साझा करें")

# Tabs for different input methods
tab1, tab2 = st.tabs(["📷 कैमरा / Camera", "📁 फाइल अपलोड / File Upload"])

uploaded_image = None
rotation_angle = 0

# Rotation utility function
def rotate_image(image_data, angle):
    """Rotate image by specified angle"""
    try:
        image = Image.open(image_data)
        if angle != 0:
            rotated = image.rotate(-angle, expand=True)
        else:
            rotated = image
        
        # Convert to RGB if necessary
        if rotated.mode != 'RGB':
            rotated = rotated.convert('RGB')
        
        byte_arr = io.BytesIO()
        rotated.save(byte_arr, format='JPEG', quality=90)
        byte_arr.seek(0)
        return byte_arr
    except Exception as e:
        st.error(f"Error rotating image: {str(e)}")
        return None

# Tab 1: Camera Input
with tab1:
    st.markdown("📱 **Tip:** Ensure good lighting and clear focus for best results")
    camera_image = st.camera_input("📸 Take a photo of an apple / सेब की तस्वीर लें")
    
    if camera_image:
        rotation_angle = st.slider(
            "🔄 Rotate Image if needed / यदि आवश्यक हो तो छवि घुमाएं", 
            0, 360, 0, step=90, 
            key="camera_rotation"
        )
        
        img_bytes = rotate_image(camera_image, rotation_angle)
        if img_bytes:
            uploaded_image = img_bytes
            st.image(img_bytes, caption="📷 Your Image / आपकी तस्वीर", width=300)

# Tab 2: File Upload
with tab2:
    st.markdown("📁 **Supported formats:** JPG, JPEG, PNG")
    file_upload = st.file_uploader(
        "📁 Upload apple image / सेब की तस्वीर अपलोड करें", 
        type=["jpg", "jpeg", "png"]
    )
    
    if file_upload:
        rotation_angle = st.slider(
            "🔄 Rotate Image if needed / यदि आवश्यक हो तो छवि घुमाएं", 
            0, 360, 0, step=90, 
            key="upload_rotation"
        )
        
        img_bytes = rotate_image(file_upload, rotation_angle)
        if img_bytes:
            uploaded_image = img_bytes
            st.image(img_bytes, caption="🖼️ Your Image / आपकी तस्वीर", width=300)

# --- Metadata Collection ---
if uploaded_image:
    st.subheader("📋 Image Information / तस्वीर की जानकारी")
    
    col1, col2 = st.columns(2)
    
    with col1:
        variety = st.text_input(
            "🍏 Apple Variety / सेब की किस्म*", 
            placeholder="e.g., Red Delicious, Fuji, Gala",
            help="Enter the specific variety name if known"
        )
        
        size = st.selectbox(
            "📏 Apple Size / सेब का आकार",
            ["Small/छोटा", "Medium/मध्यम", "Large/बड़ा", "Extra Large/अतिरिक्त बड़ा"]
        )
    
    with col2:
        location = st.text_input(
            "📍 Location / स्थान", 
            placeholder="e.g., Shimla, Kashmir, Uttarakhand",
            help="State or region where the apple was grown"
        )
        
        ripeness = st.selectbox(
            "🍎 Ripeness / पकने की स्थिति",
            ["Unripe/कच्चा", "Ripe/पका हुआ", "Overripe/अधिक पका"]
        )
    
    # Additional information
    st.markdown("**Optional Details / वैकल्पिक विवरण**")
    
    col3, col4 = st.columns(2)
    with col3:
        season = st.selectbox(
            "🗓️ Harvest Season / फसल का मौसम",
            ["Spring/वसंत", "Summer/गर्मी", "Autumn/शरद", "Winter/सर्दी", "Not Sure/पता नहीं"]
        )
    
    with col4:
        quality = st.selectbox(
            "⭐ Quality Grade / गुणवत्ता ग्रेड",
            ["Excellent/उत्कृष्ट", "Good/अच्छा", "Average/औसत", "Poor/खराब"]
        )
    
    additional_notes = st.text_area(
        "📝 Additional Notes / अतिरिक्त टिप्पणियां",
        placeholder="Any other observations about the apple...",
        height=100
    )

    # --- Submit Section ---
    st.markdown("---")
    
    if st.button("🚀 Upload to Dataset / डेटासेट में अपलोड करें", type="primary", use_container_width=True):
        if not variety.strip():
            st.error("❌ Please enter apple variety / कृपया सेब की किस्म दर्ज करें")
        else:
            try:
                with st.spinner("⏳ Uploading to research database... / अनुसंधान डेटाबेस में अपलोड हो रहा है..."):
                    # Create unique filename with metadata
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_id = uuid.uuid4().hex[:8]
                    
                    # Clean variety name for filename
                    clean_variety = "".join(c for c in variety if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    
                    filename = f"apple_dataset/{timestamp}_{clean_variety}_{unique_id}.jpg"
                    
                    # Prepare metadata
                    metadata = {
                        'variety': variety,
                        'location': location,
                        'size': size,
                        'ripeness': ripeness,
                        'season': season,
                        'quality': quality,
                        'notes': additional_notes,
                        'upload_time': datetime.now().isoformat(),
                        'contributor_type': 'farmer_app'
                    }
                    
                    # Create file on Google Drive
                    file_drive = drive.CreateFile({
                        'title': filename,
                        'parents': [{"id": "root"}],
                        'description': str(metadata)
                    })
                    
                    # Convert image to base64 for upload
                    uploaded_image.seek(0)
                    image_data = uploaded_image.read()
                    file_drive.SetContentString(base64.b64encode(image_data).decode())
                    file_drive.Upload()
                    
                    st.success("✅ Thank you! Image uploaded successfully to our research database!")
                    st.success("✅ धन्यवाद! तस्वीर सफलतापूर्वक हमारे अनुसंधान डेटाबेस में अपलोड हो गई!")
                    st.balloons()
                    
                    # Show contribution summary
                    st.info(f"""
                    📊 **Your Contribution Summary:**
                    - Variety: {variety}
                    - Location: {location or 'Not specified'}
                    - Upload ID: {unique_id}
                    
                    This data will help train AI models to benefit farmers across India!
                    """)
                    
            except Exception as e:
                st.error(f"❌ Upload failed: {str(e)}")
                st.error("Please check your internet connection and try again.")

# --- Footer ---
st.markdown("---")
st.markdown("""
### 🤝 About TEAM UNISOLE

We are a research-driven startup incubated at **IARI (Indian Agricultural Research Institute)**, India's premier agricultural research institution. Our mission is to bridge the gap between cutting-edge agricultural research and practical farming solutions using AI and machine learning.

**Our Impact Goals:**
- Build comprehensive datasets for Indian agriculture
- Develop AI tools specifically for Indian farming conditions  
- Provide free technology solutions to support farmers
- Contribute to food security and sustainable agriculture

**Contact Us:**
- 📞 Phone: 7876471141
- 📧 Email: team.unisole@gmail.com
- 🏢 Incubated at: IARI, New Delhi

*Your contribution today helps build tomorrow's farming technology!*
""")

st.markdown("---")
st.markdown("*© 2024 TEAM UNISOLE - Building the future of Indian agriculture with AI*")