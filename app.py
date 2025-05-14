import streamlit as st
import pandas as pd
import docx
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
import tempfile

st.set_page_config(page_title="Persona Builder", layout="wide")
st.title("🧠 AI Persona Builder")

# Authenticate with Google
creds = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
drive_service = build("drive", "v3", credentials=creds)

folder_id = st.text_input("Enter Google Drive folder ID")

def list_files(folder_id):
    try:
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType)",
        ).execute()
        return results.get("files", [])
    except Exception as e:
        st.error(f"Google Drive API error: {e}")
        return []

def read_csv(file_id):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        return pd.read_csv(BytesIO(data))
    except Exception as e:
        st.error(f"CSV read error: {e}")
        return None

def read_excel(file_id):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        return pd.read_excel(BytesIO(data))
    except Exception as e:
        st.error(f"Excel read error: {e}")
        return None

def read_docx(file_id):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        doc = docx.Document(BytesIO(data))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception as e:
        st.error(f"Word read error: {e}")
        return None

def read_pdf(file_id):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(data)
            doc = fitz.open(tmp.name)
            return "\n".join([page.get_text() for page in doc])
    except Exception as e:
        st.error(f"PDF read error: {e}")
        return None

def read_png(file_id):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        image = Image.open(BytesIO(data))
        return pytesseract.image_to_string(image)
    except Exception as e:
        st.error(f"OCR error: {e}")
        return None

if folder_id:
    files = list_files(folder_id)
    if not files:
        st.warning("No files found.")
    else:
        for file in files:
            st.markdown(f"---\n📄 **{file['name']}** ({file['mimeType']})")
            st.code(file["mimeType"])
            parsed = None
            if file["mimeType"] == "text/csv":
                parsed = read_csv(file["id"])
                if parsed is not None:
                    st.dataframe(parsed.head())
            elif file["mimeType"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                parsed = read_excel(file["id"])
                if parsed is not None:
                    st.dataframe(parsed.head())
            elif file["mimeType"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                parsed = read_docx(file["id"])
                if parsed:
                    st.text(parsed[:2000])
            elif file["mimeType"] == "application/pdf":
                parsed = read_pdf(file["id"])
                if parsed:
                    st.text(parsed[:2000])
            elif file["mimeType"] == "image/png":
                parsed = read_png(file["id"])
                if parsed:
                    st.text(parsed[:2000])
            else:
                st.info("⏭️ Unsupported file type: " + file["mimeType"])
