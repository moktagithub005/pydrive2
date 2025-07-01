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
import tempfile

# ✅ Page config must come FIRST
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
        token_json = st.secrets["google"]["TOKEN"]
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(credentials_json)
            credentials_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(token_json)
            token_file = f.name
        
        # Auth with PyDrive2
        gauth = GoogleAuth()
        
        # Load client config
        gauth.LoadClientConfigFile(credentials_file)
        
        # Set OAuth settings
        gauth.settings['oauth_scope'] = ["https://www.googleapis.com/auth/drive"]
        gauth.settings['get_refresh_token'] = True
        
        # Load existing credentials
        gauth.LoadCredentialsFile(token_file)
        
        if gauth.credentials is None:
            st.error("❌ No valid credentials found. Please re-run the authentication script.")
            return None
        elif gauth.access_token_expired:
            try:
                # Refresh the token
                gauth.Refresh()
                st.success("🔄 Token refreshed successfully!")
            except Exception as refresh_error:
                st.error(f"❌ Token refresh failed: {refresh_error}")
                st.error("Please re-run the authentication script to get a new token.")
                return None
        else:
            gauth.Authorize()
        
        # Clean up temporary files
        try:
            os.unlink(credentials_file)
            os.unlink(token_file)
        except:
            pass
        
        return GoogleDrive(gauth)
        
    except KeyError as e:
        st.error(f"❌ Missing Streamlit secret: {str(e)}")
        st.error("Please ensure both CREDENTIALS and TOKEN are set in [google] section of Streamlit secrets.")
        st.info("""
        **Expected format in secrets.toml:**
        ```
        [google]
        CREDENTIALS = '{"your": "credentials"}'
        TOKEN = '{"your": "token"}'
        ```
        """)
        return None
    except Exception as e:
        st.error(f"❌ Google Drive connection failed: {str(e)}")
        return None

# Function to find or create the apple_dataset folder
@st.cache_data
def get_or_create_folder(_drive, folder_name="apple_dataset"):
    """
    Find existing folder or create new one in Google Drive
    Returns folder ID
    """
    try:
        # Search for existing folder
        file_list = _drive.ListFile({
            'q': f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        }).GetList()
        
        if file_list:
            # Folder exists, return its ID
            folder_id = file_list[0]['id']
            st.info(f"📁 Using existing folder: {folder_name}")
            return folder_id
        else:
            # Create new folder
            folder_metadata = {
                'title': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = _drive.CreateFile(folder_metadata)
            folder.Upload()
            folder_id = folder['id']
            st.success(f"📁 Created new folder: {folder_name}")
            return folder_id
            
    except Exception as e:
        st.error(f"❌ Error with folder operations: {str(e)}")
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
    st.info("""
    **To fix this issue:**
    1. Run the authentication script locally to get a fresh token
    2. Copy the new token to your Streamlit secrets
    3. Restart your Streamlit app
    """)
    st.stop()

# Get or create the apple_dataset folder
folder_id = get_or_create_folder(drive, "apple_dataset")
if folder_id is None:
    st.error("❌ Failed to access or create the apple_dataset folder.")
    st.stop()

# Display folder information
st.info(f"""
📁 **Storage Location:** All images will be saved to the 'apple_dataset' folder in Google Drive.
🔗 **Access:** Log in to `unisole.empower@gmail.com` → My Drive → apple_dataset folder
""")

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
                with st.spinner("⏳ Uploading to apple_dataset folder... / apple_dataset फोल्डर में अपलोड हो रहा है..."):
                    # Create unique filename with metadata
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_id = uuid.uuid4().hex[:8]
                    
                    # Clean variety name for filename
                    clean_variety = "".join(c for c in variety if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    
                    filename = f"apple_dataset_{timestamp}_{clean_variety}_{unique_id}.jpg"
                    
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
                        'contributor_type': 'farmer_app',
                        'folder': 'apple_dataset'
                    }
                    
                    # Create file on Google Drive in the specific folder
                    file_drive = drive.CreateFile({
                        'title': filename,
                        'description': json.dumps(metadata, ensure_ascii=False),
                        'parents': [{'id': folder_id}]  # This uploads to the specific folder
                    })
                    
                    # Set content from uploaded image
                    uploaded_image.seek(0)
                    file_drive.content = uploaded_image
                    file_drive.Upload()
                    
                    st.success("✅ Thank you! Image uploaded successfully to the apple_dataset folder!")
                    st.success("✅ धन्यवाद! तस्वीर सफलतापूर्वक apple_dataset फोल्डर में अपलोड हो गई!")
                    st.balloons()
                    
                    # Show contribution summary
                    st.info(f"""
                    📊 **Your Contribution Summary:**
                    - Variety: {variety}
                    - Location: {location or 'Not specified'}
                    - Upload ID: {unique_id}
                    - 📁 Saved to: apple_dataset folder
                    - 🔍 Filename: {filename}
                    
                    **To find your image:**
                    1. Log in to Google Drive with unisole.empower@gmail.com
                    2. Go to My Drive → apple_dataset folder
                    3. Search for: {filename}
                    
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