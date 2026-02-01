import json
import csv
import os

import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import project_metrics # Uses your existing metrics module

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
    # Standard slippage fetch
    slippage = []
    try:
        rows = sh.worksheet(GANTT_SHEET).get_all_values()
        headers = rows[0]
        idx_id, idx_period, idx_task, idx_base, idx_fcst = [
            headers.index(c) for c in ["Project ID", "Report Period", "Task Name", "Baseline End", "Forecast End"]
        ]
        for r in rows[1:]:
            if r[idx_id] == project_id and r[idx_period] == period and r[idx_base] != r[idx_fcst]:
                slippage.append(f"Task '{r[idx_task]}' slipped ({r[idx_base]} -> {r[idx_fcst]})")
    except: pass
    return slippage

def fetch_previous_learning(sh, pid, current_period):
    """
    Retrieves the LAST log entry to find what the Human Manager actually DID.
    """
    try:
        w = sh.worksheet(LOG_SHEET)
        rows = w.get_all_values()
        if len(rows) < 2: return None
        
        headers = rows[0]
        idx_pid = headers.index("Project ID")
        idx_period = headers.index("Period")
        idx_strat = headers.index("AI Strategy")
        idx_action = headers.index("Actual Action Taken") # <--- Critical Column
        idx_cpi = headers.index("CPI")
        
        # Look backwards for the most recent DIFFERENT period
        for r in reversed(rows[1:]):
            if r[idx_pid] == pid and r[idx_period] < current_period:
                return {
                    "period": r[idx_period],
                    "prev_cpi": float(r[idx_cpi]),
                    "ai_advice": r[idx_strat][:150] + "...",
                    "human_action": r[idx_action] if len(r) > idx_action and r[idx_action] else "No action recorded."
                }
    except: return None
    return None

def generate_report_skeleton(metrics, slippage, history, pname, pid, period):
    """
    PYTHON WRITES THE FACTS (Sections 1 & 2). 
    This guarantees consistent formatting and perfect math.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Header
    report = f"🚨 EXECUTIVE FLASH REPORT: {current_time}\n\n"
    
    # Section 1: Learning Loop (The Gap Analysis)
    report += "1. MANAGER EFFECTIVENESS (Learning Loop)\n"
    if history:
        delta = metrics['cpi'] - history['prev_cpi']
        result_str = "IMPROVED" if delta > 0 else "DEGRADED"
        report += f"* Context: Last month ({history['period']}), the Manager reported: '{history['human_action']}'.\n"
        report += f"* Result: Project {result_str} (CPI {history['prev_cpi']} -> {metrics['cpi']}).\n"
        report += "* Insight: [AI_INSERT_INSIGHT_HERE]\n" # AI will fill this placeholder
    else:
        report += "* Status: First month of analysis. No manager history to evaluate.\n"
        
    # Section 2: Current Findings (Math based)
    report += "\n2. CURRENT STATUS\n"
    if metrics['cpi'] < 1.0:
        report += f"* Financials: CRITICAL. CPI {metrics['cpi']}. Overrun ${metrics['variance']:,.2f}.\n"
        if metrics['root_causes']:
            report += f"* Bleeding Items: {', '.join(metrics['root_causes'])}.\n"
    else:
        report += f"* Financials: STABLE. CPI {metrics['cpi']}. Under Budget by ${metrics['variance']:,.2f}.\n"
        
    if slippage:
        report += f"* Schedule: DELAYED. {slippage[0]}\n"
    else:
        report += "* Schedule: ON TRACK.\n"

    return report

def consult_agent_for_strategy(skeleton, metrics, history):
    """
    AI FILLS THE STRATEGY & INSIGHTS (Section 3 + Insight Placeholder).
    """
    
    # We explicitly ask the AI to analyze the "Actual Action Taken"
    human_action_context = history['human_action'] if history else "N/A"
    prev_result = "Project got worse" if history and metrics['cpi'] < history['prev_cpi'] else "Project improved"
    
    prompt = f"""
    You are a Project Control Director.
    
    --- INPUT DATA ---
    REPORT SKELETON:
    {skeleton}
    
    MANAGER'S PREVIOUS ACTION: "{human_action_context}"
    RESULT: {prev_result}
    
    --- TASK ---
    1. Provide a 1-sentence "Insight" on whether the Manager's action was effective.
    2. Write "3. STRATEGIC RECOVERY PLAN".
       If the Manager failed/ignored advice, be strict.
       If the Manager succeeded, validate them.
       
    --- OUTPUT FORMAT ---
    Insight: [Your sentence here]
    
    3. STRATEGIC RECOVERY PLAN
    A. Immediate Actions
    [Bullets]
    B. Structural Correction
    [Bullets]
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
    
    print(f"   🤖 Analyzing {pid} ({period})...")
    
    # 1. Get Data (Math + History)
    metrics = project_metrics.calculate_financials(budget_rows, pid, period)
    slippage = fetch_slippage(sh, pid, period)
    history = fetch_previous_learning(sh, pid, period)
    
    # 2. Python Builds the Skeleton (Facts)
    skeleton = generate_report_skeleton(metrics, slippage, history, pname, pid, period)
    
    # 3. AI Fills the Strategy
    ai_response = consult_agent_for_strategy(skeleton, metrics, history)
    
    # 4. Merge Logic (Simple String Replacement)
    # We split the AI response to inject the "Insight" into the right place
    try:
        parts = ai_response.split("3. STRATEGIC RECOVERY PLAN")
        insight_text = parts[0].replace("Insight:", "").strip()
        strategy_text = "3. STRATEGIC RECOVERY PLAN" + parts[1]
        
        final_report = skeleton.replace("[AI_INSERT_INSIGHT_HERE]", insight_text) + "\n" + strategy_text
    except:
        # Fallback if AI messes up format
        final_report = skeleton + "\n\n" + ai_response

    # 5. Log
    log_to_sheet(sh, pid, pname, period, metrics["cpi"], final_report)

def log_to_sheet(sh, pid, pname, period, cpi, content):
    try:
        w = sh.worksheet(LOG_SHEET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        # We append a new row with empty "Actual Action Taken" for the human to fill next
        w.append_row([timestamp, pid, pname, period, cpi, content, ""])
        
        last_row = len(w.get_all_values())
        w.format(f"F{last_row}", {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"})
        print("   ✅ Report Logged.")
    except Exception as e:
        print(f"   ❌ Logging Error: {e}")

def main():
    sh = get_sh()
    print("\n🚀 MISSION CONTROL: CLOSED LOOP SYSTEM")
    try: budget_rows = sh.worksheet(BUDGET_SHEET).get_all_values()
    except: print("❌ Error reading Budget Sheet."); return

    active_projects = project_metrics.get_active_projects(budget_rows)
    print(f"📋 Found {len(active_projects)} Active Projects (Analyzing Latest Period)...\n")

    for pid, info in active_projects.items():
        # Force the period to 2026-03 (Current) for this test, 
        # or use info['latest_period'] if you want auto-detection.
        project_info = {'id': pid, 'name': info['name'], 'period': '2026-03'}
        run_analysis(project_info, sh, budget_rows)
        print("-" * 20)

if __name__ == "__main__":
    main()