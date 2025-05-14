import streamlit as st
import pandas as pd
import docx
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import vision
import tempfile
from pptx import Presentation

st.set_page_config(page_title="Persona Builder", layout="wide")
st.title("🧠 AI Persona Builder")

# Authenticate with Google
creds = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
drive_service = build("drive", "v3", credentials=creds)
vision_client = vision.ImageAnnotatorClient(credentials=creds)

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

def read_excel(file_id, engine=None):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        return pd.read_excel(BytesIO(data), engine=engine)
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

def read_image_vision(file_id):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        image = vision.Image(content=data)
        response = vision_client.text_detection(image=image)
        return response.full_text_annotation.text
    except Exception as e:
        st.error(f"Google Vision OCR error: {e}")
        return None

def read_pptx(file_id):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        prs = Presentation(BytesIO(data))
        text = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text.append(shape.text)
        return "\n".join(text)
    except Exception as e:
        st.error(f"PPTX read error: {e}")
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
            mt = file["mimeType"]
            if mt == "text/csv":
                parsed = read_csv(file["id"])
                if parsed is not None:
                    st.dataframe(parsed.head())
            elif mt == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                parsed = read_excel(file["id"])
                if parsed is not None:
                    st.dataframe(parsed.head())
            elif mt == "application/vnd.ms-excel":
                parsed = read_excel(file["id"], engine="xlrd")
                if parsed is not None:
                    st.dataframe(parsed.head())
            elif mt == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                parsed = read_docx(file["id"])
                if parsed:
                    st.text(parsed[:2000])
            elif mt == "application/pdf":
                parsed = read_pdf(file["id"])
                if parsed:
                    st.text(parsed[:2000])
            elif mt in ["image/png", "image/jpeg"]:
                parsed = read_image_vision(file["id"])
                if parsed:
                    st.text(parsed[:2000])
            elif mt == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                parsed = read_pptx(file["id"])
                if parsed:
                    st.text(parsed[:2000])
            else:
                st.info("⏭️ Unsupported file type: " + mt)
