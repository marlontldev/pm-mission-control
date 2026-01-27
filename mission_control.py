
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
JSON_KEYFILE = "credentials.json"

def get_worksheet():
    """Authenticates and returns the first sheet (Tab 1) of the spreadsheet."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
        client = gspread.authorize(creds)
        
        # Open the spreadsheet and get the first tab
        return client.open(SPREADSHEET_NAME).sheet1
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def update_dataset(sheet, data, cpi, source):
    """Appends a new analysis row and formats it professionally."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_text = "CRITICAL" if cpi < 1.0 else "ON TRACK"
    strategy = data.get('content', 'No content')

    # 1. Check if Header Exists (First Run Only)
    if sheet.row_count < 2 or sheet.acell('A1').value == "":
        print("🆕 First run detected. Creating headers...")
        headers = ["Timestamp", "Data Source", "CPI Value", "Project Status", "AI Recovery Strategy"]
        sheet.insert_row(headers, index=1)
        # Format Headers (Bold, Grey Background)
        sheet.format("A1:E1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
        })

    # 2. Append the New Data Row
    row_data = [timestamp, source, cpi, status_text, strategy]
    sheet.append_row(row_data)
    
    # 3. Apply Professional Formatting to the New Row
    # We find the row number we just added
    last_row = len(sheet.get_all_values()) 
    
    # Define Formats
    fmt_wrap = {"wrapStrategy": "WRAP"} # Keep long text readable
    fmt_center = {"horizontalAlignment": "CENTER"}
    fmt_status_color = {
        "textFormat": {
            "bold": True, 
            "foregroundColor": {"red": 1.0 if cpi < 1.0 else 0.0, "green": 0.5 if cpi >= 1.0 else 0.0, "blue": 0.0}
        }
    }

    # Apply Formats range by range for efficiency
    # Center align Timestamp, Source, CPI, Status (Cols A-D)
    sheet.format(f"A{last_row}:D{last_row}", fmt_center)
    
    # Color the Status Cell (Column D) Red or Green
    sheet.format(f"D{last_row}", fmt_status_color)
    
    # Wrap the Strategy Text (Column E) so it doesn't overflow
    sheet.format(f"E{last_row}", fmt_wrap)

    print(f"✨ Dataset updated successfully at Row {last_row}")

def consult_strategist(current_cpi, data_source):
    print("\n📡 Connecting to Google Sheets...")
    sheet = get_worksheet()
    if not sheet: return

    print(f"🤖 Consulting Strategist Agent (CPI: {current_cpi})...")
    payload = {"details": {"current_value": current_cpi}}
    
    try:
        response = requests.post(AGENT_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Update the Dataset
        update_dataset(sheet, data, current_cpi, data_source)

    except Exception as e:
        print(f"❌ Error during analysis: {e}")

def get_project_data():
    print("\n" + "="*40)
    print("📊 DATA INPUT MODE")
    print("1. Direct Input (I know the CPI)")
    print("2. Raw Data (Calculate from EV & AC)")
    print("="*40)
    
    choice = input("Select Option (1 or 2): ").strip()
    
    if choice == "1":
        try:
            val = float(input(">> Enter current CPI (e.g., 0.85): "))
            return val, "Manual Input"
        except:
            return 1.0, "Error"
    elif choice == "2":
        try:
            ev = float(input(">> Earned Value ($): "))
            ac = float(input(">> Actual Cost ($): "))
            cpi = round(ev / ac, 2) if ac != 0 else 0
            return cpi, f"Calc (EV:{ev}|AC:{ac})"
        except:
            return 1.0, "Error"
    return 1.0, "Error"

if __name__ == "__main__":
    cpi, source = get_project_data()
    consult_strategist(cpi, source)