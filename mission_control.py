
import json
import csv
import os


import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURATION ---
AGENT_URL = "http://localhost:8081/"
SHEET_NAME = "Mission Control Log"
JSON_KEYFILE = "credentials.json"

def get_google_sheet():
    """Authenticates and connects to the Google Sheet."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

def calculate_cpi(earned_value, actual_cost):
    """Calculates CPI safely."""
    try:
        if actual_cost == 0:
            return 0.0 # Avoid division by zero
        return round(earned_value / actual_cost, 2)
    except Exception:
        return 0.0

def get_project_data():
    """Asks user for input method and returns the calculated CPI."""
    print("\n" + "="*40)
    print("📊 DATA INPUT MODE")
    print("1. Direct Input (I know the CPI)")
    print("2. Raw Data (Calculate from EV & AC)")
    print("="*40)
    
    choice = input("Select Option (1 or 2): ").strip()
    
    if choice == "1":
        # Option 1: You know the status already
        cpi = float(input(">> Enter current CPI (e.g., 0.85): "))
        return cpi, "Manual Input"
        
    elif choice == "2":
        # Option 2: You have the receipts and progress logs
        print("\n--- Enter Financials ---")
        ev = float(input(">> Earned Value ($) - Value of work completed: "))
        ac = float(input(">> Actual Cost ($) - Money spent so far: "))
        
        calculated_cpi = calculate_cpi(ev, ac)
        
        print(f"\n⚡ CALCULATED RESULT: ${ev} / ${ac} = CPI {calculated_cpi}")
        if calculated_cpi < 1.0:
            print("⚠️  WARNING: Project is over budget.")
        else:
            print("✅ STATUS: Project is under budget.")
            
        return calculated_cpi, f"Calc (EV:{ev}|AC:{ac})"
    
    else:
        print("Invalid selection. Defaulting to 1.0")
        return 1.0, "Error"

def consult_strategist(current_cpi, data_source):
    # 1. Connect to Sheets
    print("\n📡 Connecting to Google Sheets...")
    sheet = get_google_sheet()

    # 2. Call AI Agent
    print(f"🤖 Consulting Strategist Agent (CPI: {current_cpi})...")
    payload = {"details": {"current_value": current_cpi}}
    
    try:
        response = requests.post(AGENT_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        strategy_content = data.get('content', 'No content')

        # 3. Display Report
        print("\n" + "="*60)
        print(f"✅ STRATEGIC ANALYSIS COMPLETE")
        print(f"📅 Time: {timestamp}")
        print(f"📉 CPI Status: {current_cpi}")
        print("-" * 60)
        print(f"📋 ADVICE:\n{strategy_content}")
        print("="*60)

        # 4. Update Graph (Now includes the Data Source)
        # Columns: [Timestamp, CPI, Strategy, Data Source]
        sheet.append_row([timestamp, current_cpi, strategy_content, data_source])
        print("✨ Google Sheet & Graph updated successfully.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    cpi_value, source_note = get_project_data()
    consult_strategist(cpi_value, source_note)