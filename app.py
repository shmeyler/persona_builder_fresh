
import streamlit as st
import os
import io
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.cloud import vision
from PIL import Image
import tempfile
import mimetypes

# Basic config
st.set_page_config(page_title="Persona Builder", layout="wide")
st.title("Persona Builder")

logging.basicConfig(level=logging.INFO)

# UI input for Google Drive folder ID
folder_id = st.text_input("Enter Google Drive Folder ID to scan:")

# Load credentials
def load_gdrive_service():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    return build("drive", "v3", credentials=credentials)

def load_vision_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return vision.ImageAnnotatorClient(credentials=credentials)

# Recursively list all files
def list_drive_files(service, folder_id):
    files = []
    query = f"'{folder_id}' in parents and trashed = false"
    page_token = None
    while True:
        response = service.files().list(
            q=query,
            spaces="drive",
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
        ).execute()
        for file in response.get("files", []):
            if file["mimeType"] == "application/vnd.google-apps.folder":
                files += list_drive_files(service, file["id"])
            else:
                files.append(file)
        page_token = response.get("nextPageToken", None)
        if page_token is None:
            break
    return files

# Download a file
def download_file(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh

# OCR with Google Vision
def extract_text_from_image(image_bytes, vision_client):
    image = vision.Image(content=image_bytes)
    response = vision_client.text_detection(image=image)
    if response.error.message:
        raise Exception(response.error.message)
    return response.text_annotations[0].description if response.text_annotations else ""

# Main logic
if folder_id:
    st.write(f"📁 Scanning folder `{folder_id}`...")
    try:
        drive_service = load_gdrive_service()
        vision_client = load_vision_client()
        all_files = list_drive_files(drive_service, folder_id)
        st.success(f"✅ Found {len(all_files)} files")

        for file in all_files:
            try:
                name = file["name"]
                mime = file["mimeType"]
                st.write(f"🔍 Processing `{name}` ({mime})")

                if mime.startswith("image/"):
                    img_bytes = download_file(drive_service, file["id"]).read()
                    text = extract_text_from_image(img_bytes, vision_client)
                    st.text_area(f"📄 Extracted text from {name}:", text, height=200)

                else:
                    st.warning(f"⏭️ Unsupported MIME type: {mime}")

            except Exception as file_err:
                st.error(f"❌ Failed to process {file['name']}: {file_err}")

    except Exception as e:
        st.error(f"❌ Error initializing services or accessing folder: {e}")
