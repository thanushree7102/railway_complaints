import streamlit as st
import google.generativeai as genai
import sounddevice as sd
import numpy as np
import wave
import tempfile
import smtplib
import os
import pandas as pd
from email.message import EmailMessage
import speech_recognition as sr
from collections import defaultdict
import sqlite3
from datetime import datetime
import random

# 📌 Set page config as the FIRST Streamlit command
st.set_page_config(page_title="Railway Complaint System", layout="wide")

# 🔹 Configure Gemini AI
genai.configure(api_key="AIzaSyC2JpLpiqgnaH1BgL_-FTimpglTCxg45Dc")  # Replace with your valid API key
model = genai.GenerativeModel('gemini-1.5-flash')

# 🔹 Define valid PNR numbers
VALID_PNR_NUMBERS = {f"PNRA{i}" for i in range(1, 11)} | {f"PNRB{i}" for i in range(1, 11)}

# 🚀 Supported languages for speech recognition
LANGUAGE_MAP = {
    "Assamese": "as-IN", "Bengali": "bn-IN", "Bodo": "brx-IN",
    "Dogri": "doi-IN", "Gujarati": "gu-IN", "Hindi": "hi-IN",
    "Kannada": "kn-IN", "Kashmiri": "ks-IN", "Konkani": "kok-IN",
    "Maithili": "mai-IN", "Malayalam": "ml-IN", "Manipuri": "mni-IN",
    "Marathi": "mr-IN", "Nepali": "ne-IN", "Odia": "or-IN",
    "Punjabi": "pa-IN", "Sanskrit": "sa-IN", "Santali": "sat-IN",
    "Sindhi": "sd-IN", "Tamil": "ta-IN", "Telugu": "te-IN",
    "Urdu": "ur-IN", "English": "en-IN"
}

# 🚨 Complaint categories and subcategories
CATEGORY_MAP = {
    "STAFF BEHAVIOUR": ["Staff – Behaviour"],
    "SECURITY": ["Smoking", "Drinking Alcohol/Narcotics", "Theft of Passengers' Belongings", "Snatching", "Harassment", "Others"],
    "COACH-CLEANLINESS": ["Toilets", "Cockroach", "Rodents", "Coach-Interior", "Others"],
    "ELECTRICAL-EQUIPMENT": ["Air Conditioner", "Fans", "Lights"],
    "CORRUPTION/BRIBERY": ["Corruption/Bribery"],
    "GOODS": ["Booking", "Delivery", "Overcharging", "Staff Not Available", "Others"],
    "CATERING AND VENDING SERVICES": ["Overcharging", "Service Quality", "Food Quantity", "Food Quality", "Food and Water Not Available", "Others"],
    "MEDICAL ASSISTANCE": ["Medical Assistance"],
    "WATER AVAILABILITY": ["Drinking Water at Platform", "Packaged Drinking Water", "Rail Neer", "Water Vending Machine", "Retiring Room", "Waiting Room", "Toilet", "Others"],
    "MISCELLANEOUS": ["Miscellaneous"]
}

# 📧 Email Credentials (App Passwords)
EMAIL_CREDENTIALS = {
    "tshree4179@gmail.com": "pcxkzqekbymmpywi",
    "vis12356789@gmail.com": "jpprsezowjfabtdi",
    "sphalguna17@gmail.com": "qncwrnpbetipmxvx",
    "mohitv9110@gmail.com": "xbgohksvkgvslisv",
    "sn3951418@gmail.com": "syltqmkdhwdemway",
    "manjushreemr18@gmail.com": "skrdbhwptqxjtyte"
}

# 📧 Email recipients based on category
CATEGORY_EMAILS = {
    "STAFF BEHAVIOUR": "tshree4179@gmail.com",
    "SECURITY": "vis12356789@gmail.com",
    "COACH-CLEANLINESS": "manjushreemr18@gmail.com",
    "ELECTRICAL-EQUIPMENT": "sphalguna17@gmail.com",
    "CORRUPTION/BRIBERY": "sn3951418@gmail.com",
    "GOODS": "tshree4179@gmail.com",
    "CATERING AND VENDING SERVICES": "mohitv9110@gmail.com",
    "MEDICAL ASSISTANCE": "manjushreemr18@gmail.com",
    "WATER AVAILABILITY": "sphalguna17@gmail.com",
    "MISCELLANEOUS": "sn3951418@gmail.com"
}

# 🏢 Station names and dummy phone numbers
STATIONS = [
    {"name": "Mumbai Central", "phone": "022-55501001"},
    {"name": "New Delhi Station", "phone": "011-55501002"},
    {"name": "Chennai Central", "phone": "044-55501003"},
    {"name": "Kolkata Howrah", "phone": "033-55501004"},
    {"name": "Bangalore City", "phone": "080-55501005"},
    {"name": "Hyderabad Deccan", "phone": "040-55501006"},
    {"name": "Ahmedabad Junction", "phone": "079-55501007"},
    {"name": "Pune Junction", "phone": "020-55501008"},
    {"name": "Jaipur Station", "phone": "0141-55501009"},
    {"name": "Lucknow Charbagh", "phone": "0522-55501010"}
]

# 🌐 Placeholder text in different languages for the complaint text area
LANGUAGE_PLACEHOLDERS = {
    "Assamese": "আপোনাৰ অভিযোগ ইয়াত লিখক",
    "Bengali": "এখানে আপনার অভিযোগ লিখুন",
    "Bodo": "निनार खन्थायखौ इयानि लिर",
    "Dogri": "इथे अपणी शिकायत लिखो",
    "Gujarati": "અહીં તમારી ફરિયાદ લખો",
    "Hindi": "यहाँ अपनी शिकायत लिखें",
    "Kannada": "ಇಲ್ಲಿ ನಿಮ್ಮ ದೂರು ಬರೆಯಿರಿ",
    "Kashmiri": "پننہ شکایت ایتھہ لکھو",
    "Konkani": "हांगा तुमची तक्रार बरयात",
    "Maithili": "एहि ठाम अपन शिकायत लिखू",
    "Malayalam": "നിന്റെ പരാതി ഇവിടെ എഴുതുക",
    "Manipuri": "ꯅꯤꯡꯒꯤ ꯊꯥꯖꯤꯟꯕ ꯃꯐꯝ ꯂꯤꯁꯤꯟꯕꯤꯗꯨ",
    "Marathi": "येथे तुमची तक्रार लिहा",
    "Nepali": "यहाँ आफ्नो गुनासो लेख्नुहोस्",
    "Odia": "ଏଠାରେ ଆପଣଙ୍କ ଅଭିଯୋଗ ଲେଖନ୍ତୁ",
    "Punjabi": "ਇੱਥੇ ਆਪਣੀ ਸ਼ਿਕਾਇਤ ਲਿਖੋ",
    "Sanskrit": "अत्र तव संनादति लिख",
    "Santali": "ᱤᱱᱟᱹ ᱟᱢᱟᱜ ᱠᱷᱟᱱᱛᱟᱭ ᱚᱞ",
    "Sindhi": "هتي پنهنجي شڪايت لکو",
    "Tamil": "இங்கு உங்கள் புகாரை எழுதவும்",
    "Telugu": "ఇక్కడ మీ ఫిర్యాదును రాయండి",
    "Urdu": "یہاں اپنی شکایت لکھیں",
    "English": "Enter your complaint here"
}

# 🔧 SQLite Database Setup with Schema Migration
def init_db():
    # Use os.path.join for proper path construction
    db_path = os.path.join(r"C:\Users\user\Documents", "complaints.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Check if the table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='complaints'")
    table_exists = c.fetchone()

    # Define the expected columns
    expected_columns = [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "phone_number TEXT",
        "pnr_number TEXT",
        "complaint TEXT",
        "category_subcategory TEXT",
        "language TEXT",
        "timestamp TEXT",
        "station_name TEXT",
        "station_phone TEXT"
    ]

    if not table_exists:
        c.execute(f'''
            CREATE TABLE complaints (
                {", ".join(expected_columns)}
            )
        ''')
    else:
        c.execute("PRAGMA table_info(complaints)")
        existing_columns = [col[1] for col in c.fetchall()]
        expected_column_names = [col.split()[0] for col in expected_columns]
        missing_columns = [col for col in expected_column_names if col not in existing_columns]

        if missing_columns:
            c.execute("ALTER TABLE complaints RENAME TO complaints_old")
            c.execute(f'''
                CREATE TABLE complaints (
                    {", ".join(expected_columns)}
                )
            ''')
            c.execute("PRAGMA table_info(complaints_old)")
            old_columns = [col[1] for col in c.fetchall()]
            common_columns = [col for col in expected_column_names if col in old_columns and col != "id"]
            if common_columns:
                columns_str = ", ".join(common_columns)
                c.execute(f'''
                    INSERT INTO complaints ({columns_str})
                    SELECT {columns_str}
                    FROM complaints_old
                ''')
            c.execute("DROP TABLE complaints_old")

    conn.commit()
    conn.close()

# Initialize the database
init_db()

def save_to_db(complaint_data):
    try:
        db_path = os.path.join(r"C:\Users\user\Documents", "complaints.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO complaints (phone_number, pnr_number, complaint, category_subcategory, language, timestamp, station_name, station_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            complaint_data["phone_number"],
            complaint_data["pnr_number"],
            complaint_data["complaint"],
            complaint_data["category_subcategory"],
            complaint_data["language"],
            complaint_data["timestamp"],
            complaint_data["station_name"],
            complaint_data["station_phone"]
        ))
        conn.commit()
        st.success("✅ Complaint saved to SQLite database successfully!")
    except Exception as e:
        st.error(f"❌ Error saving to database: {e}")
        raise e
    finally:
        conn.close()

def read_from_db():
    try:
        db_path = os.path.join(r"C:\Users\user\Documents", "complaints.db")
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM complaints", conn)
        return df
    except Exception as e:
        st.error(f"❌ Error reading from database: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def categorize_complaint(complaint_text):
    prompt = (
        f"Classify this railway complaint: '{complaint_text}'. "
        f"Identify all relevant categories and subcategories. "
        f"Return them in the format: 'CATEGORY1 - SUBCATEGORY1, CATEGORY2 - SUBCATEGORY2, ...'. "
        f"Use only from these categories: {CATEGORY_MAP}."
    )
    response = model.generate_content(prompt)
    valid_pairs = []

    if response and response.text:
        ai_output = response.text.strip().upper()
        st.write(f"🟡 AI Output: {ai_output}")
        pairs = [pair.strip() for pair in ai_output.split(',')]
        for pair in pairs:
            if " - " in pair:
                cat, sub = pair.split(" - ", 1)
                cat = cat.strip().upper()
                sub = sub.strip().upper()
                matched_category = next((c for c in CATEGORY_MAP if c.upper() == cat), None)
                if matched_category:
                    valid_subcategories = [s.upper() for s in CATEGORY_MAP[matched_category]]
                    if sub in valid_subcategories:
                        valid_pairs.append((matched_category, sub))
                    else:
                        st.warning(f"⚠ Invalid subcategory '{sub}' for category '{matched_category}'. Skipping.")
                else:
                    st.warning(f"⚠ Invalid category '{cat}'. Skipping.")
            else:
                st.warning(f"⚠ Invalid pair format: '{pair}'. Skipping.")
    if not valid_pairs:
        valid_pairs = [("MISCELLANEOUS", "Others")]

    valid_pairs = list(set(valid_pairs))
    category_to_subcategories = defaultdict(list)
    for cat, sub in valid_pairs:
        category_to_subcategories[cat].append(sub)

    return category_to_subcategories

def display_categories(category_to_subcategories):
    st.write("📂 Assigned Categories and Subcategories:")
    for category, subcategories in category_to_subcategories.items():
        st.markdown(f'<p class="category-text">{category}</p>', unsafe_allow_html=True)
        for sub in subcategories:
            st.markdown(f'<p class="subcategory-text">  - {sub}</p>', unsafe_allow_html=True)

def assign_station():
    return random.choice(STATIONS)

def display_station(station):
    st.write("🏢 Assigned Station:")
    st.markdown(f'<p class="category-text">{station["name"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="subcategory-text">📞 Phone: {station["phone"]}</p>', unsafe_allow_html=True)

def send_complaint_email(category, subcategories, complaint_text, user_phone, pnr_number, station):
    recipient_email = CATEGORY_EMAILS.get(category, "tshree4179@gmail.com")
    sender_email = recipient_email
    sender_password = EMAIL_CREDENTIALS.get(sender_email, "")
    
    if not sender_password:
        st.error(f"❌ No password found for {sender_email}")
        return
    
    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = f"🚆 New Railway Complaint - {category}"
    
    subcategories_str = ", ".join(subcategories)
    msg.set_content(f"""
    🚨 New Complaint Submitted 🚨
    
    📂 Category: {category}
    🗂 Subcategories: {subcategories_str}
    📝 Complaint Details: {complaint_text}
    📞 User Phone: {user_phone}
    🎟 PNR Number: {pnr_number}
    🏢 Assigned Station: {station["name"]}
    📞 Station Phone: {station["phone"]}

    Please take necessary action.

    Regards,  
    Railway Complaint System
    """, charset="utf-8")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587

)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        st.success(f"✅ Email sent successfully to {recipient_email} for category {category}")
    except Exception as e:
        st.error(f"❌ Failed to send email to {recipient_email}: {e}")

@st.cache_resource
def set_styles():
    st.markdown(
        """
        <style>
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url("https://images.yourstory.com/cs/2/3fb20ae02dc911e9af58c17e6cc3d915/shutterstock1049569559-1599036632157.png?mode=crop&crop=faces&ar=2%3A1&format=auto&w=1920&q=75") no-repeat center center fixed;
            background-size: cover;
            filter: blur(10px);
            z-index: -1;
        }
        .stApp {
            background: rgba(255, 255, 255, 0.85);
            position: relative;
            z-index: 1;
            min-height: 100vh;
        }
        [data-testid="stSidebar"] {
            background: transparent !important;
            z-index: 2;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #000000 !important;
        }
        [data-testid="stSidebarNav"] * {
            color: white !important;
            font-weight: bold !important;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }
        [data-testid="stSidebar"] a, [data-testid="stSidebar"] button {
            color: white !important;
        }
        h1, h2, h3 {
            color: white !important;
            font-size: 35px !important;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }
        h4, h5, h6, p, label {
            color: #000000 !important;
            font-size: 35px !important;
        }
        input, textarea {
            font-size: 30px !important;
            color: #000000 !important;
            background-color: white !important;
            border: 1px solid #000000 !important;
            font-family: 'Noto Sans', sans-serif !important;
        }
        .stButton>button {
            color: #000000 !important;
            font-size: 30px !important;
            background-color: white !important;
            border: 1px solid #000000 !important;
        }
        .centered-title {
            text-align: center;
            font-size: 80px !important;
            font-weight: bold;
            color: white !important;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            margin-top: 50px;
        }
        .category-text {
            font-size: 35px !important;
            color: white !important;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }
        .subcategory-text {
            font-size: 28px !important;
            color: white !important;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }
        .stMarkdown, .stText, .stRadio > label, .stSelectbox > label, .stTextInput > label, .stTextArea > label {
            color: #000000 !important;
            font-family: 'Noto Sans', sans-serif !important;
        }
        .help-info, .stMarkdown {
            color: #000000 !important;
            font-family: 'Noto Sans', sans-serif !important;
        }
        * {
            font-family: 'Noto Sans', sans-serif !important;
        }
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wght@0,400;0,700;1,400;1,700&family=Noto+Sans+Assamese&family=Noto+Sans+Bengali&family=Noto+Sans+Devanagari&family=Noto+Sans+Gujarati&family=Noto+Sans+Kannada&family=Noto+Sans+Malayalam&family=Noto+Sans+Oriya&family=Noto+Sans+Punjabi&family=Noto+Sans+Tamil&family=Noto+Sans+Telugu&family=Noto+Sans+Urdu&display=swap" rel="stylesheet">
        """,
        unsafe_allow_html=True
    )

set_styles()

st.sidebar.image(r"C:\Users\user\Downloads\thanu 2025-03-27 at 20.46.20_f82eedda.jpg", width=250)
st.sidebar.title("📌 Navigation")
menu = ["Home", "File a Complaint", "Admin Panel", "Help"]
choice = st.sidebar.radio("Go to", menu)

if "audio_path" not in st.session_state:
    st.session_state["audio_path"] = None
if "complaint_data" not in st.session_state:
    st.session_state["complaint_data"] = []

if choice == "File a Complaint":
    st.title("📩 File a Complaint")
    phone_number = st.text_input("📞 Enter Phone Number")
    pnr_number = st.text_input("🎟 Enter PNR Number")

    if pnr_number and pnr_number not in VALID_PNR_NUMBERS:
        st.error("❌ Invalid PNR number! Please enter a valid PNR from PNRA1–PNRA10 or PNRB1–PNRB10.")
        st.stop()

    language = st.selectbox("🌎 Choose Complaint Language", list(LANGUAGE_MAP.keys()))
    selected_lang_code = LANGUAGE_MAP[language]

    st.subheader("📝 How would you like to submit your complaint?")
    input_method = st.radio("Select Input Method", ["Record/Upload Audio", "Type Complaint"])

    if input_method == "Record/Upload Audio":
        st.subheader("🎙 Record or Upload Complaint Audio")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🎙 Start Recording (10 sec)"):
                st.write("✅ Recording started! Speak now.")
                temp_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
                audio_data = sd.rec(int(10 * 44100), samplerate=44100, channels=1, dtype=np.int16)
                sd.wait()
                with wave.open(temp_audio_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(44100)
                    wf.writeframes(audio_data.tobytes())
                st.session_state["audio_path"] = temp_audio_path
                st.success("✅ Recording Completed!")

        with col2:
            uploaded_file = st.file_uploader("📂 Upload an Audio File", type=["wav", "mp3", "m4a"])
            if uploaded_file:
                temp_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
                with open(temp_audio_path, "wb") as f:
                    f.write(uploaded_file.read())
                st.session_state["audio_path"] = temp_audio_path
                st.success("✅ File Uploaded Successfully.")

        if st.session_state["audio_path"] and st.button("📩 Submit Audio Complaint", key="submit_audio"):
            st.write("⏳ Transcribing Audio Complaint...")
            recognizer = sr.Recognizer()
            with sr.AudioFile(st.session_state["audio_path"]) as source:
                audio_data = recognizer.record(source)
            try:
                complaint_text = recognizer.recognize_google(audio_data, language=selected_lang_code)
            except sr.UnknownValueError:
                complaint_text = "❌ Could not understand the audio."
                st.error(complaint_text)
                st.stop()
            except sr.RequestError:
                complaint_text = "❌ Speech Recognition API unavailable."
                st.error(complaint_text)
                st.stop()

            category_to_subcategories = categorize_complaint(complaint_text)
            display_categories(category_to_subcategories)

            st.session_state["complaint_data"].append({
                "phone_number": phone_number,
                "pnr_number": pnr_number,
                "audio_path": st.session_state["audio_path"],
                "language_code": selected_lang_code,
                "input_type": "audio",
                "complaint_text": complaint_text
            })
            st.session_state["audio_path"] = None

    elif input_method == "Type Complaint":
        st.subheader("✍ Type Your Complaint")
        placeholder_text = LANGUAGE_PLACEHOLDERS.get(language, "Enter your complaint here")
        typed_complaint = st.text_area("Enter your complaint here", height=150, placeholder=placeholder_text)
        
        if st.button("📩 Submit Typed Complaint", key="submit_typed"):
            if typed_complaint:
                category_to_subcategories = categorize_complaint(typed_complaint)
                display_categories(category_to_subcategories)

                st.session_state["complaint_data"].append({
                    "phone_number": phone_number,
                    "pnr_number": pnr_number,
                    "complaint_text": typed_complaint,
                    "language_code": selected_lang_code,
                    "input_type": "text",
                    "language": language
                })
            else:
                st.error("❌ Please enter a complaint before submitting.")

elif choice == "Admin Panel":
    st.title("🔒 Admin Panel")
    password = st.text_input("Enter Admin Password", type="password")
    if password != "admin123":
        st.error("❌ Incorrect password!")
        st.stop()

    st.subheader("Pending Complaints")
    if not st.session_state["complaint_data"]:
        st.write("No pending complaints.")
    else:
        for idx, complaint in enumerate(st.session_state["complaint_data"]):
            st.write(f"Complaint {idx + 1}:")
            st.write(f"Phone: {complaint['phone_number']}, PNR: {complaint['pnr_number']}")
            st.write(f"Language: {complaint.get('language', 'Not specified')}")

            if complaint["input_type"] == "audio":
                complaint_text = complaint["complaint_text"]
            else:
                st.write("📝 Typed Complaint:")
                complaint_text = complaint["complaint_text"]

            edited_text = st.text_area(f"Edit Complaint Text (Complaint {idx + 1}):", complaint_text, height=150, key=f"edit_{idx}")

            if st.button(f"Process Complaint {idx + 1}", key=f"process_{idx}"):
                category_to_subcategories = categorize_complaint(edited_text)
                display_categories(category_to_subcategories)

                assigned_station = assign_station()
                display_station(assigned_station)

                category_subcategory_str = ", ".join([f"{cat} - {sub}" for cat, subs in category_to_subcategories.items() for sub in subs])
                complaint_data = {
                    "phone_number": complaint["phone_number"],
                    "pnr_number": complaint["pnr_number"],
                    "complaint": edited_text,
                    "category_subcategory": category_subcategory_str,
                    "language": complaint.get("language", "Not specified"),
                    "timestamp": datetime.now().isoformat(),
                    "station_name": assigned_station["name"],
                    "station_phone": assigned_station["phone"]
                }
                save_to_db(complaint_data)

                for category, subcategories in category_to_subcategories.items():
                    send_complaint_email(category, subcategories, edited_text, complaint["phone_number"], complaint["pnr_number"], assigned_station)

                st.session_state["complaint_data"].pop(idx)
                st.success("✅ Complaint processed and removed from pending list!")

    st.subheader("All Processed Complaints")
    df = read_from_db()
    if not df.empty:
        st.dataframe(df)
    else:
        st.write("No processed complaints found in the database.")

elif choice == "Help":
    st.title("ℹ Help & Information")
    st.write("""
    ### How to Use the Railway Complaint System
    1. Enter Details: Provide your phone number and PNR number.
    2. Select Language: Choose your preferred language for the complaint.
    3. Submit Complaint: Either record/upload an audio complaint or type your complaint directly.
    4. Submit: Submit for admin review.
    5. Admin Panel: Admins can process complaints, categorize them, and send emails.

    ### Supported Categories
    Your complaint can be classified into multiple categories and subcategories, such as:
    - STAFF BEHAVIOUR: Staff – Behaviour
    - SECURITY: Smoking, Theft, etc.
    - COACH-CLEANLINESS: Toilets, Cockroach, etc.
    - And more...

    ### Contact
    For assistance, email: support@railwaycomplaints.com
    """)

elif choice == "Home":
    st.markdown('<h1 class="centered-title">🚆 Railway Complaint System</h1>', unsafe_allow_html=True)