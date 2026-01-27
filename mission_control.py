import json
import csv
import os

import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# CONFIG
AGENT_URL = "http://localhost:8081/"
SPREADSHEET_NAME = "Mission Control Log"
BUDGET_SHEET = "Budget_Tracking"
GANTT_SHEET = "Schedule_Gantt"
LOG_SHEET = "AI_Analysis_Log"
JSON_KEYFILE = "credentials.json"

def get_sh():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
    return gspread.authorize(creds).open(SPREADSHEET_NAME)

def fetch_data(sh, period):
    # 1. GET BUDGET (Safety Net Added)
    cpi = 1.0 # Default value to prevent crash
    try:
        w = sh.worksheet(BUDGET_SHEET)
        rows = w.get_all_values()
        # Find column indexes dynamically
        headers = rows[0]
        idx_period = headers.index("Report Period")
        idx_cpi = headers.index("CPI (EV/AC)")
        idx_cat = headers.index("Cost Category")
        
        # Search for Total Project in this period
        for r in rows[1:]:
            if r[idx_period] == period and "TOTAL PROJECT" in r[idx_cat].upper():
                cpi = float(r[idx_cpi])
                break
    except Exception as e:
        print(f"⚠️  Budget Read Warning: {e}")

    # 2. GET SCHEDULE (Safety Net Added)
    slippage = []
    try:
        w = sh.worksheet(GANTT_SHEET)
        rows = w.get_all_values()
        headers = rows[0]
        idx_period = headers.index("Report Period")
        idx_base = headers.index("Baseline End")
        idx_fcst = headers.index("Forecast End")
        idx_task = headers.index("Task Name")

        for r in rows[1:]:
            if r[idx_period] == period:
                if r[idx_base] != r[idx_fcst]:
                    slippage.append(f"Task '{r[idx_task]}' slipped (Base: {r[idx_base]} -> Fcst: {r[idx_fcst]})")
    except Exception as e:
        print(f"⚠️  Gantt Read Warning: {e}")

    return cpi, slippage

def consult_agent(cpi, slippage, period, sh):
    print(f"🤖 Analyzing Period {period} (CPI: {cpi})...")
    
    # Check/Create Log Sheet
    try:
        w = sh.worksheet(LOG_SHEET)
    except:
        w = sh.add_worksheet(LOG_SHEET, 100, 10)
        w.append_row(["Timestamp", "Period", "CPI", "Status", "Strategy"])

    # Prepare AI Context
    context = {
        "details": {
            "current_value": cpi,
            "project_context": f"Period: {period}\nCPI: {cpi}\nDelays: {slippage}"
        }
    }

    try:
        resp = requests.post(AGENT_URL, json=context)
        resp.raise_for_status()
        content = resp.json().get('content', 'No strategy')
        
        # Log it
        status = "CRITICAL" if (cpi < 1.0 or slippage) else "ON TRACK"
        w.append_row([str(datetime.now()), period, cpi, status, content])
        print("✅ Analysis Logged successfully.")
    except Exception as e:
        print(f"❌ AI Error: {e}")

if __name__ == "__main__":
    sh = get_sh()
    period = input("Enter Period (e.g., 2026-02): ").strip()
    cpi, slippage = fetch_data(sh, period)
    consult_agent(cpi, slippage, period, sh)