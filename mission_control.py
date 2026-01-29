import json
import csv
import os

import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import project_metrics # Import logic

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

def fetch_slippage(sh, project_id, period):
    slippage = []
    try:
        rows = sh.worksheet(GANTT_SHEET).get_all_values()
        headers = rows[0]
        # Indexes
        idx_id = headers.index("Project ID")
        idx_period = headers.index("Report Period")
        idx_task = headers.index("Task Name")
        idx_base = headers.index("Baseline End")
        idx_fcst = headers.index("Forecast End")
        
        for r in rows[1:]:
            if r[idx_id] == project_id and r[idx_period] == period:
                if r[idx_base] != r[idx_fcst]:
                    slippage.append(f"Task '{r[idx_task]}' slipped ({r[idx_base]} -> {r[idx_fcst]})")
    except: pass
    return slippage

def run_agent_analysis(metrics, slippage, project_info, sh):
    pid = project_info['id']
    pname = project_info['name']
    period = project_info['period']
    
    print(f"   🤖 Analyzing {pid}: {pname}...")

    # Data Formatting
    root_cause_text = "\n".join([f"- 🔴 {item}" for item in metrics["root_causes"]]) or "- 🟢 Stable."
    slippage_text = "\n".join(slippage) or "No schedule slippage."

    prompt = f"""
    YOU ARE A PORTFOLIO DIRECTOR. ANALYZE THIS SPECIFIC PROJECT.
    
    PROJECT: {pname} (ID: {pid})
    PERIOD: {period}
    
    --- METRICS ---
    - Budget: ${metrics['bac']:,.0f}
    - CPI: {metrics['cpi']} (Target 1.0)
    - Projected Variance: ${metrics['variance']:,.0f}
    - TCPI: {metrics['tcpi']:.2f}
    
    --- ISSUES ---
    FAILING ITEMS:
    {root_cause_text}
    
    SCHEDULE DELAYS:
    {slippage_text}
    
    --- OUTPUT FORMAT ---
    # PROJECT STATUS: {pname}
    * **Health:** [Critical/Stable]
    * **Findings:** [1 sentence summary of root cause]
    * **Directive:** [1 strategic instruction to the PM]
    """

    payload = {"details": {"current_value": metrics["cpi"], "project_context": prompt}}
    
    try:
        resp = requests.post(AGENT_URL, json=payload)
        resp.raise_for_status()
        
        # Log Result
        log_to_sheet(sh, pid, pname, period, metrics["cpi"], resp.json().get('content'))
    except Exception as e:
        print(f"   ❌ Error: {e}")

def log_to_sheet(sh, pid, pname, period, cpi, content):
    try:
        try: w = sh.worksheet(LOG_SHEET)
        except: 
            w = sh.add_worksheet(LOG_SHEET, 100, 10)
            w.append_row(["Timestamp", "Project ID", "Project Name", "Period", "CPI", "AI Analysis"])
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        w.append_row([timestamp, pid, pname, period, cpi, content])
        
        # Format (Last Row, Column F)
        last_row = len(w.get_all_values())
        w.format(f"F{last_row}", {"wrapStrategy": "WRAP"})
        print("   ✅ Logged.")
    except: pass

def main():
    sh = get_sh()
    print("\n🚀 MISSION CONTROL: PORTFOLIO SCANNER")
    print("="*40)
    
    # 1. READ ALL DATA ONCE
    try:
        budget_rows = sh.worksheet(BUDGET_SHEET).get_all_values()
    except:
        print("❌ Error reading Budget Sheet."); return

    # 2. IDENTIFY ACTIVE PROJECTS
    # Returns: {'PROJ-001': {'name': 'Alpha', 'latest_period': '2026-02'}, ...}
    active_projects = project_metrics.get_active_projects(budget_rows)
    
    print(f"📋 Found {len(active_projects)} Active Projects. Starting Analysis...\n")

    # 3. LOOP THROUGH PROJECTS
    for pid, info in active_projects.items():
        pname = info['name']
        period = info['latest_period']
        
        print(f"🔹 Processing {pid} ({period})...")
        
        # A. Get Metrics
        metrics = project_metrics.calculate_financials(budget_rows, pid, period)
        
        # B. Get Schedule
        slippage = fetch_slippage(sh, pid, period)
        
        # C. Run AI
        project_data = {'id': pid, 'name': pname, 'period': period}
        run_agent_analysis(metrics, slippage, project_data, sh)
        print("-" * 20)

    print("\n✅ Portfolio Scan Complete.")

if __name__ == "__main__":
    main()