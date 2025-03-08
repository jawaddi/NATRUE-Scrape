import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("savedata-452919-69fd401a8a6d.json", scope)

def save_to_json(data, filename):
    os.makedirs("scraped_data", exist_ok=True)
    filepath = os.path.join("scraped_data", filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"Data saved in '{filepath}'")

# def save_to_json(data, filename):
#     with open(filename, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=4, ensure_ascii=False)
#     print(f"Data saved in '{filename}'")

def save_to_google_sheets(data, headers, sheet_name):

    if not data:
        print(" No data found to upload.")
        return
    client = gspread.authorize(creds)

    try:
        sheet = client.open(sheet_name).sheet1
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Google Sheet '{sheet_name}' not found.")
        return

    sheet.clear()  
    print(f"Cleared existing data in '{sheet_name}'.")

    sheet.append_row(headers)
    print(f"Headers written: {headers}")

    # Collect rows to insert in one go
    rows = []
    for item in data:
        row = [item.get(col, "") for col in headers]
        rows.append(row)
    
    if rows:
        sheet.insert_rows(rows, 2) 
        print(f"{len(rows)} rows written to the sheet.")
    
    print(f"Data saved to Google Sheets: {sheet_name}")

#  test with a smaller dataset
# test_data = [{"name": "(4 ELEMENTS FOR LIFE)", "image": "https://example.com/image.jpg", "brand_description": "Some description"}]
# save_to_json(test_data,"Brand_sheet")

def authenticate_drive():
    """Authenticate using the existing service account credentials"""
    return build("drive", "v3", credentials=creds)

def upload_to_drive(file_path, folder_id=None):
    
    drive_service = authenticate_drive()
    
    file_metadata = {"name": os.path.basename(file_path)}
    if folder_id:
        file_metadata["parents"] = [folder_id]  

    media = MediaFileUpload(file_path, mimetype="application/msword")
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    
    print(f"Uploaded {file_path} to Google Drive with file ID: {uploaded_file.get('id')}")
    return uploaded_file.get("id")
