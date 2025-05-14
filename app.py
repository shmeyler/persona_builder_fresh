import streamlit as st
import pandas as pd
import docx
import fitz
from PIL import Image
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import vision
import tempfile
from pptx import Presentation

st.set_page_config(page_title="Persona Builder", layout="wide")
st.title("🧠 AI Persona Builder with Recursive Drive Scan")

creds = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
drive_service = build("drive", "v3", credentials=creds)
vision_client = vision.ImageAnnotatorClient(credentials=creds)

folder_id = st.text_input("Enter Google Drive folder ID")

filetypes = st.multiselect(
    "Choose file types to process",
    ["csv", "xlsx", "xls", "docx", "pdf", "png", "jpg", "pptx"],
    default=["csv", "xlsx", "xls", "docx", "pdf", "png", "jpg", "pptx"]
)

ext_map = {
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
}

def list_files_recursive(folder_id):
    files = []

    def recurse(fid):
        query = f"'{fid}' in parents and trashed=false"
        response = drive_service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        for file in response.get("files", []):
            if file["mimeType"] == "application/vnd.google-apps.folder":
                recurse(file["id"])
            else:
                files.append(file)

    recurse(folder_id)
    return files

def read_csv(file_id):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        return pd.read_csv(BytesIO(data))
    except:
        return None

def read_excel(file_id, engine=None):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        return pd.read_excel(BytesIO(data), engine=engine)
    except:
        return None

def read_docx(file_id):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        doc = docx.Document(BytesIO(data))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except:
        return None

def read_pdf_table(file_id):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(data)
            doc = fitz.open(tmp.name)
            text = "\n".join([page.get_text() for page in doc])
        return extract_table_like_structure(text)
    except:
        return None

def read_image_table(file_id):
    try:
        data = drive_service.files().get_media(fileId=file_id).execute()
        image = vision.Image(content=data)
        response = vision_client.text_detection(image=image)
        return extract_table_like_structure(response.full_text_annotation.text)
    except:
        return None

def extract_table_like_structure(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    rows = [line.split() for line in lines if len(line.split()) > 1]
    if not rows:
        return None
    try:
        df = pd.DataFrame(rows[1:], columns=rows[0]) if len(rows) > 1 else pd.DataFrame(rows)
        return df
    except:
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
    except:
        return None

if folder_id:
    files = list_files_recursive(folder_id)
    if not files:
        st.warning("No files found.")
    else:
        MAX_FILES = 10
        progress = st.progress(0)
        for i, file in enumerate(files[:MAX_FILES]):
            mt = file["mimeType"]
            name = file["name"]
            st.write(f"▶ Processing: {name} ({mt})")
            if mt not in [ext_map[ft] for ft in filetypes if ft in ext_map]:
                st.info("⏭️ Skipped due to file type filter")
                progress.progress((i + 1) / MAX_FILES)
                continue

            parsed = None
            if mt == ext_map["csv"]:
                parsed = read_csv(file["id"])
                if parsed is not None:
                    st.dataframe(parsed.head())
            elif mt == ext_map["xlsx"]:
                parsed = read_excel(file["id"])
                if parsed is not None:
                    st.dataframe(parsed.head())
            elif mt == ext_map["xls"]:
                parsed = read_excel(file["id"], engine="xlrd")
                if parsed is not None:
                    st.dataframe(parsed.head())
            elif mt == ext_map["docx"]:
                parsed = read_docx(file["id"])
                if parsed:
                    with st.expander("Preview DOCX"):
                        st.text(parsed[:1000])
            elif mt == ext_map["pdf"]:
                parsed = read_pdf_table(file["id"])
                if parsed is not None:
                    st.dataframe(parsed.head())
            elif mt in [ext_map["png"], ext_map["jpg"]]:
                parsed = read_image_table(file["id"])
                if parsed is not None:
                    st.dataframe(parsed.head())
            elif mt == ext_map["pptx"]:
                parsed = read_pptx(file["id"])
                if parsed:
                    with st.expander("Preview PPTX"):
                        st.text(parsed[:1000])
            else:
                st.warning("⏭️ Unhandled MIME type")
            progress.progress((i + 1) / MAX_FILES)
