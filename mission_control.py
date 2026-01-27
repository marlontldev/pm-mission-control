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
DATA_SHEET_NAME = "Budget_Tracking"  # <--- NEW: The source of your data
JSON_KEYFILE = "credentials.json"

def get_spreadsheet():
    """Connects to the Spreadsheet."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
        client = gspread.authorize(creds)
        return client.open(SPREADSHEET_NAME)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def get_and_initialize_log_sheet(spreadsheet):
    """Finds/Creates the Log sheet and checks headers."""
    try:
        try:
            sheet = spreadsheet.worksheet(LOG_SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            print(f"🆕 Creating new sheet: '{LOG_SHEET_NAME}'...")
            sheet = spreadsheet.add_worksheet(title=LOG_SHEET_NAME, rows=100, cols=10)

        # Force Header Check
        if sheet.acell('A1').value != "Timestamp":
            print("🔧 Installing Headers...")
            headers = ["Timestamp", "Data Source", "CPI Value", "Project Status", "AI Recovery Strategy"]
            sheet.insert_row(headers, index=1)
            sheet.format("A1:E1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}, "horizontalAlignment": "CENTER"})
            
        return sheet
    except Exception as e:
        print(f"❌ Log Sheet Error: {e}")
        return None

def read_budget_sheet(spreadsheet):
    """
    Scans the 'Budget_Tracking' sheet to find the TOTAL PROJECT CPI.
    """
    print(f"🔍 Scanning '{DATA_SHEET_NAME}' for project health...")
    try:
        sheet = spreadsheet.worksheet(DATA_SHEET_NAME)
        all_values = sheet.get_all_values()
        
        # 1. Find the 'TOTAL PROJECT' row
        cpi = 1.0
        found = False
        
        for row in all_values:
            # Check first column (Cost Category) for the "Total" label
            if "TOTAL PROJECT" in row[0].upper():
                # Assuming CPI is in the 5th column (Index 4), as per your screenshot
                raw_cpi = row[4] 
                cpi = float(raw_cpi)
                found = True
                break
        
        if found:
            print(f"✅ Found TOTAL PROJECT CPI: {cpi}")
            return cpi, f"Auto-Read ({DATA_SHEET_NAME})"
        else:
            print("⚠️ Could not find 'TOTAL PROJECT' row. Defaulting to 1.0")
            return 1.0, "Error: Total Not Found"

    except Exception as e:
        print(f"❌ Read Error: {e}")
        return 1.0, "Error: Read Failed"

def update_dataset(sheet, data, cpi, source):
    """Appends data and applies styling."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_text = "CRITICAL" if cpi < 1.0 else "ON TRACK"
    strategy = data.get('content', 'No content')

    row_data = [timestamp, source, cpi, status_text, strategy]
    sheet.append_row(row_data)
    
    # Formatting
    last_row = len(sheet.get_all_values())
    sheet.format(f"A{last_row}:D{last_row}", {"horizontalAlignment": "CENTER"})
    sheet.format(f"D{last_row}", {
        "textFormat": {"bold": True, "foregroundColor": {"red": 1.0 if cpi < 1.0 else 0.0, "green": 0.5 if cpi >= 1.0 else 0.0, "blue": 0.0}}
    })
    sheet.format(f"E{last_row}", {"wrapStrategy": "WRAP"})
    
    # Safe Resize
    try:
        body = {"requests": [{"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 400}, "fields": "pixelSize"}}]}
        sheet.spreadsheet.batch_update(body)
    except: pass
    
    print(f"✨ Analysis logged successfully to Row {last_row}")

def consult_strategist(cpi, source, spreadsheet):
    print("\n📡 Connecting to Log Sheet...")
    sheet = get_and_initialize_log_sheet(spreadsheet)
    if not sheet: return

    print(f"🤖 Consulting Strategist Agent (CPI: {cpi})...")
    try:
        payload = {"details": {"current_value": cpi}}
        response = requests.post(AGENT_URL, json=payload)
        response.raise_for_status()
        update_dataset(sheet, response.json(), cpi, source)
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("\n" + "="*40)
    print("📊 MISSION CONTROL CENTER")
    print("1. Manual Input")
    print("2. Calculator (EV / AC)")
    print("3. 🤖 AUTO-ANALYZE 'Budget_Tracking' Sheet")  # <--- NEW OPTION
    print("="*40)
    
    choice = input("Select Option (1-3): ").strip()
    
    # Initialize Spreadsheet ONCE here to pass it around
    spreadsheet = get_spreadsheet()
    if not spreadsheet: return

    cpi = 1.0
    source = "Error"

    if choice == "1":
        try: cpi = float(input(">> Enter CPI: ")); source = "Manual Input"
        except: pass
    elif choice == "2":
        try:
            ev = float(input(">> EV ($): ")); ac = float(input(">> AC ($): "))
            cpi = round(ev/ac, 2) if ac!=0 else 0; source = f"Calc (EV:{ev}|AC:{ac})"
        except: pass
    elif choice == "3":
        # CALL THE NEW FUNCTION
        cpi, source = read_budget_sheet(spreadsheet)
    else:
        # Smart input check (if user typed "0.92" directly)
        try: cpi = float(choice); source = "Manual Input (Auto-detect)"
        except: print("Invalid input."); return

    # Run the Agent
    consult_strategist(cpi, source, spreadsheet)

if __name__ == "__main__":
    main()