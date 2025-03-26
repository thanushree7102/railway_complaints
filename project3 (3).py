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
from openpyxl import load_workbook

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

def send_complaint_email(category, subcategory, complaint_text, user_phone, pnr_number):
    recipient_email = CATEGORY_EMAILS.get(category, "tshree4179@gmail.com")  # Default email
    sender_email = recipient_email  # The email sending should match the category
    sender_password = EMAIL_CREDENTIALS.get(sender_email, "")
    
    if not sender_password:
        print(f"❌ No password found for {sender_email}")
        return
    
    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = f"🚆 New Railway Complaint - {category} ({subcategory})"

    msg.set_content(f"""
    🚨 **New Complaint Submitted** 🚨
    
    📂 **Category**: {category}
    🗂 **Subcategory**: {subcategory}
    📝 **Complaint Details**: {complaint_text}
    📞 **User Phone**: {user_phone}
    🎟 **PNR Number**: {pnr_number}

    Please take necessary action.

    Regards,  
    **Railway Complaint System**
    """, charset="utf-8")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        
        
def save_to_excel(phone_number, pnr_number, category, subcategory, complaint_text):
    file_path = "complaints.xlsx"
    new_data = pd.DataFrame([[phone_number, pnr_number, category, subcategory, complaint_text]],
     columns=["Phone Number", "PNR", "Category", "Subcategory", "Complaint"])
    
    try:
        existing_data = pd.read_excel(file_path)
        updated_data = pd.concat([existing_data, new_data], ignore_index=True)
    except FileNotFoundError:
        updated_data = new_data
    
    updated_data.to_excel(file_path, index=False)

# 📌 Streamlit UI
st.set_page_config(page_title="Railway Complaint System", layout="wide")

st.sidebar.title("📌 Navigation")
menu = ["Home", "Submit Complaint", "Help"]
choice = st.sidebar.radio("Go to", menu)

# 🏠 *Home Page*
if choice == "Home":
    st.title("🚆 Railway Complaint System")
    st.image("C:\\Users\\user\\Downloads\\WhatsApp Image 2025-03-21 at 20.40.14_2204828e.jpg", use_column_width=True)
    st.write("Register railway complaints easily!")

# 📩 *Submit Complaint*
elif choice == "Submit Complaint":
    st.title("📩 Submit a Complaint")
    phone_number = st.text_input("📞 Enter Phone Number")
    pnr_number = st.text_input("🎟 Enter PNR Number")

    # 🚨 *Validate PNR*
    if pnr_number and pnr_number not in VALID_PNR_NUMBERS:
        st.error("❌ Invalid PNR number! Please enter a valid PNR from PNRA1–PNRA10 or PNRB1–PNRB10.")
        st.stop()

    # 🌍 *Select Language*
    language = st.selectbox("🌎 Choose Complaint Language", list(LANGUAGE_MAP.keys()))
    selected_lang_code = LANGUAGE_MAP[language]

    # 🎤 *Record or Upload Audio*
    st.subheader("🎙 Record or Upload Complaint Audio")
    col1, col2 = st.columns(2)

    if "audio_path" not in st.session_state:
        st.session_state["audio_path"] = None

    # 🎙 *Record Audio*
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

    # 📂 *Upload Audio*
    with col2:
        uploaded_file = st.file_uploader("📂 Upload an Audio File", type=["wav", "mp3", "m4a"])
        if uploaded_file:
            temp_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            with open(temp_audio_path, "wb") as f:
                f.write(uploaded_file.read())
            st.session_state["audio_path"] = temp_audio_path
            st.success("✅ File Uploaded Successfully.")

    # 📝 *Transcription Process*
    if st.session_state["audio_path"]:
        st.write("⏳ *Transcribing Complaint...*")
        recognizer = sr.Recognizer()
        with sr.AudioFile(st.session_state["audio_path"]) as source:
            audio_data = recognizer.record(source)
        try:
            transcribed_text = recognizer.recognize_google(audio_data, language=selected_lang_code)
        except sr.UnknownValueError:
            transcribed_text = "❌ Could not understand the audio."
        except sr.RequestError:
            transcribed_text = "❌ Speech Recognition API unavailable."

        edited_text = st.text_area("📝 Edit Complaint Text:", transcribed_text, height=150)

# 🏷 *Categorize Complaint using Gemini AI*
ai_output = "MISCELLANEOUS - Others"  # Default

if st.button("📩 Submit Complaint"):
    prompt = (
        f"Classify this railway complaint: '{edited_text}'. "
        f"Return the category and subcategory in this exact format: 'CATEGORY - SUBCATEGORY'. "
        f"Use only from these categories: {CATEGORY_MAP}."
    )

    response = model.generate_content(prompt)

    if response and response.text:
        ai_output = response.text.strip().upper()

    # 🔍 *Debugging - See what AI is returning*
    st.write(f"🟡 *AI Output:* {ai_output}")

    category, subcategory = "MISCELLANEOUS", "Others"

    if " - " in ai_output:
        cat, sub = ai_output.split(" - ", 1)
        cat = cat.strip()
        sub = sub.strip()

        # ✅ *Strict Category Check*
        matched_category = next((c for c in CATEGORY_MAP if c.upper() == cat), None)

        if matched_category:
            valid_subcategories = CATEGORY_MAP[matched_category]

            # ✅ *Strict Subcategory Check*
            matched_subcategory = next((s for s in valid_subcategories if s.upper() == sub), None)

            if matched_subcategory:
                subcategory = matched_subcategory  # ✅ Use AI-suggested subcategory if valid
            else:
                st.warning(f"⚠ AI suggested an invalid subcategory: {sub}. Using default: {valid_subcategories[0]}.")
                subcategory = valid_subcategories[0]  # ✅ STRICTLY PICK THE FIRST VALID SUBCATEGORY

            category = matched_category  # ✅ Assign category correctly
        else:
            st.warning(f"⚠ AI suggested an invalid category: {cat}. Defaulting to 'MISCELLANEOUS - Others'.")

    # 🔹 *Display the Corrected Category and Subcategory*
    st.write(f"📂 *Category:* {category}")
    st.write(f"📂 *Subcategory:* {subcategory}")
    st.success("✅ Complaint submitted successfully!")
    complaint_data = {
        "Phone Number": phone_number,
        "PNR Number": pnr_number,
        "Complaint": edited_text,
        "Category": category,
        "Subcategory": subcategory,
        "Timestamp": pd.Timestamp.now()
    }

    file_path = r"C:\Users\user\Downloads\complaints.xlsx"

    try:
        if os.path.exists(file_path):
            df = pd.read_excel(file_path, engine="openpyxl")
            df = pd.concat([df, pd.DataFrame([complaint_data])], ignore_index=True)
        else:
            df = pd.DataFrame([complaint_data])

        df.to_excel(file_path, index=False, engine="openpyxl")

        # ✅ Send email only to the correct category
        send_complaint_email(category, subcategory, edited_text, phone_number, pnr_number)

        st.success("✅ Complaint submitted successfully! (Saved in Excel & Email Sent)")

    except Exception as e:
        st.error(f"❌ Error saving complaint: {e}")