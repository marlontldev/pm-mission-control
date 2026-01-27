import json
import csv
import os

import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURATION ---
AGENT_URL = "http://localhost:8081/"
SPREADSHEET_NAME = "Mission Control Log"
LOG_SHEET_NAME = "AI_Analysis_Log"
JSON_KEYFILE = "credentials.json"

def get_and_initialize_sheet():
    """
    Connects to the sheet AND guarantees Headers exist.
    This is the self-healing logic.
    """
    try:
        # 1. Connect
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        # 2. Get or Create Tab
        try:
            sheet = spreadsheet.worksheet(LOG_SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            print(f"🆕 Creating new sheet: '{LOG_SHEET_NAME}'...")
            sheet = spreadsheet.add_worksheet(title=LOG_SHEET_NAME, rows=100, cols=10)

        # 3. FORCE CHECK: Do Headers exist?
        # We read cell A1. If it's not "Timestamp", we wipe row 1 and write headers.
        first_cell = sheet.acell('A1').value
        
        if first_cell != "Timestamp":
            print("🔧 Headers missing. Installing Headers now...")
            headers = ["Timestamp", "Data Source", "CPI Value", "Project Status", "AI Recovery Strategy"]
            
            # Use insert_row at index 1 to force it to the top
            sheet.insert_row(headers, index=1)
            
            # Format the Headers immediately
            sheet.format("A1:E1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                "horizontalAlignment": "CENTER"
            })
            
        return sheet

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def update_dataset(sheet, data, cpi, source):
    """Appends data and applies styling."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_text = "CRITICAL" if cpi < 1.0 else "ON TRACK"
    strategy = data.get('content', 'No content')

    # 1. Append the Data (Headers are guaranteed to exist now)
    row_data = [timestamp, source, cpi, status_text, strategy]
    sheet.append_row(row_data)
    
    # 2. Format the new row
    last_row = len(sheet.get_all_values())
    
    # Center Align Metadata (Cols A-D)
    sheet.format(f"A{last_row}:D{last_row}", {"horizontalAlignment": "CENTER"})
    
    # Status Color (Red/Green)
    sheet.format(f"D{last_row}", {
        "textFormat": {
            "bold": True, 
            "foregroundColor": {"red": 1.0 if cpi < 1.0 else 0.0, "green": 0.5 if cpi >= 1.0 else 0.0, "blue": 0.0}
        }
    })
    
    # Wrap Strategy Text
    sheet.format(f"E{last_row}", {"wrapStrategy": "WRAP"})

    # Safe Resize Column E
    try:
        body = {
            "requests": [{"updateDimensionProperties": {
                "range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5},
                "properties": {"pixelSize": 400},
                "fields": "pixelSize"
            }}]
        }
        sheet.spreadsheet.batch_update(body)
    except:
        pass

    print(f"✨ Analysis logged successfully to Row {last_row}")

def consult_strategist(current_cpi, data_source):
    print("\n📡 Connecting to Google Sheets...")
    # This function now handles the header check automatically
    sheet = get_and_initialize_sheet()
    if not sheet: return

    print(f"🤖 Consulting Strategist Agent (CPI: {current_cpi})...")
    try:
        payload = {"details": {"current_value": current_cpi}}
        response = requests.post(AGENT_URL, json=payload)
        response.raise_for_status()
        
        update_dataset(sheet, response.json(), current_cpi, data_source)

    except Exception as e:
        print(f"❌ Error: {e}")

def get_project_data():
    print("\n" + "="*40)
    print("📊 DATA INPUT MODE")
    print("1. Direct Input (I know the CPI)")
    print("2. Raw Data (Calculate from EV & AC)")
    print("="*40)
    choice = input("Select Option (1 or 2): ").strip()
    if choice == "1":
        try: return float(input(">> CPI: ")), "Manual Input"
        except: return 1.0, "Error"
    elif choice == "2":
        try:
            ev = float(input(">> EV ($): ")); ac = float(input(">> AC ($): "))
            return (round(ev/ac, 2) if ac!=0 else 0), f"Calc (EV:{ev}|AC:{ac})"
        except: return 1.0, "Error"
    return 1.0, "Error"

if __name__ == "__main__":
    cpi, source = get_project_data()
    consult_strategist(cpi, source)