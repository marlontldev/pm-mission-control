import json
import csv
import os

import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import project_metrics # Import your math module

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
        idx_id = headers.index("Project ID")
        idx_period = headers.index("Report Period")
        idx_task = headers.index("Task Name")
        idx_base = headers.index("Baseline End")
        idx_fcst = headers.index("Forecast End")
        
        for r in rows[1:]:
            if r[idx_id] == project_id and r[idx_period] == period and r[idx_base] != r[idx_fcst]:
                slippage.append(f"Task '{r[idx_task]}' slipped ({r[idx_base]} -> {r[idx_fcst]})")
    except: pass
    return slippage

def generate_report_sections(metrics, slippage, pname, pid, period):
    """
    PYTHON GENERATES THE FACTS (SECTIONS 1 & 2).
    This guarantees the format is perfect and math is accurate.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    is_critical = metrics['cpi'] < 1.0 or len(slippage) > 0
    
    # --- HEADER ---
    report_text = f"🚨 EXECUTIVE FLASH REPORT: {current_time}\n\n"
    
    # --- SECTION 1: FINDINGS ---
    if is_critical:
        report_text += "1. FINDINGS (The Bleeding Wounds)\n"
        # Findings Logic
        if metrics["root_causes"]:
            failures = ", ".join(metrics["root_causes"])
            report_text += f"* Specific Failure: {failures}. This category is driving the deficit.\n"
        else:
            report_text += "* Specific Failure: General efficiency loss across all categories.\n"
            
        loss_per_dollar = round(1.0 - metrics['cpi'], 2)
        report_text += f"* Severity: CPI of {metrics['cpi']} means losing ${loss_per_dollar} for every dollar spent.\n"
        
        if slippage:
            report_text += f"* Schedule Impact: {len(slippage)} tasks delayed. {slippage[0]}.\n"
        else:
            report_text += "* Schedule Impact: No delays yet, but cost is critical.\n"
            
    else:
        # Healthy Project Logic
        report_text += "1. FINDINGS (Performance Highlights)\n"
        report_text += f"* Status: Project {pname} is performing efficiently (CPI {metrics['cpi']}).\n"
        report_text += "* Schedule: On Track.\n"

    # --- SECTION 2: TREND ---
    report_text += "\n2. PROJECT TREND (The Trajectory)\n"
    if metrics['variance'] < 0:
        report_text += f"* Financial Trajectory: 📉 Projected to finish ${abs(metrics['variance']):,.2f} OVER budget.\n"
    else:
        report_text += f"* Financial Trajectory: 📈 Projected to finish ${metrics['variance']:,.2f} UNDER budget.\n"
        
    report_text += f"* Recovery Reality: Team must operate at {metrics['tcpi']:.2f} efficiency (TCPI) to hit targets.\n"

    return report_text

def consult_agent_for_strategy(report_facts, metrics, slippage):
    """
    AI GENERATES ONLY SECTION 3 (STRATEGY).
    """
    prompt = f"""
    You are a Senior Project Director. 
    Read the following Project Status Report Findings:
    
    {report_facts}
    
    --- TASK ---
    Write **ONLY** Section 3: "STRATEGIC RECOVERY PLAN".
    Do not repeat the findings. Do not write an intro.
    
    Format Requirements:
    3. STRATEGIC RECOVERY PLAN
    A. Stop the Bleeding (Immediate)
    [Bullet points: Specific tactical actions based on the failing items]
    
    B. Structural Correction (Next 30 Days)
    [Bullet points: Strategic scope/engineering changes]
    """
    
    payload = {"details": {"current_value": metrics["cpi"], "project_context": prompt}}
    try:
        resp = requests.post(AGENT_URL, json=payload)
        resp.raise_for_status()
        return resp.json().get('content')
    except:
        return "AI Connection Failed."

def run_analysis(project_info, sh, budget_rows):
    pid = project_info['id']
    pname = project_info['name']
    period = project_info['period']
    
    print(f"   🤖 Analyzing {pid}...")
    
    # 1. Get Data
    metrics = project_metrics.calculate_financials(budget_rows, pid, period)
    slippage = fetch_slippage(sh, pid, period)
    
    # 2. Python Writes the Facts (Sec 1 & 2)
    fact_section = generate_report_sections(metrics, slippage, pname, pid, period)
    
    # 3. AI Writes the Strategy (Sec 3)
    strategy_section = consult_agent_for_strategy(fact_section, metrics, slippage)
    
    # 4. Combine & Log
    full_report = fact_section + "\n" + strategy_section
    log_to_sheet(sh, pid, pname, period, metrics["cpi"], full_report)

def log_to_sheet(sh, pid, pname, period, cpi, content):
    try:
        try: w = sh.worksheet(LOG_SHEET)
        except: 
            w = sh.add_worksheet(LOG_SHEET, 100, 10)
            w.append_row(["Timestamp", "Project ID", "Project Name", "Period", "CPI", "Executive Report"])
            w.format("A1:F1", {"textFormat": {"bold": True}})
            w.set_column_width(6, 600)
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        w.append_row([timestamp, pid, pname, period, cpi, content])
        
        # Wrap Text
        last_row = len(w.get_all_values())
        w.format(f"F{last_row}", {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"})
        
        print("   ✅ Report Generated & Logged.")
    except Exception as e:
        print(f"   ❌ Logging Error: {e}")

def main():
    sh = get_sh()
    print("\n🚀 MISSION CONTROL: PORTFOLIO SCANNER")
    try: budget_rows = sh.worksheet(BUDGET_SHEET).get_all_values()
    except: print("❌ Error reading Budget Sheet."); return

    active_projects = project_metrics.get_active_projects(budget_rows)
    print(f"📋 Found {len(active_projects)} Active Projects.\n")

    for pid, info in active_projects.items():
        project_info = {'id': pid, 'name': info['name'], 'period': info['latest_period']}
        run_analysis(project_info, sh, budget_rows)
        print("-" * 20)

if __name__ == "__main__":
    main()