import json
import csv
import os
import warnings
# Suppress the Google Auth FutureWarnings
warnings.filterwarnings("ignore", category=FutureWarning)

import warnings
# 1. FIX: Suppress the Google Auth warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import project_metrics 

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

def generate_simulated_manager_action(ai_advice, project_name):
    prompt = f"""
    ROLE: Operations Director for {project_name}.
    CONTEXT: Last month AI advised: "{ai_advice}"
    TASK: Write a 1-sentence "Actual Action Taken". 
    SCENARIO: You ignored the AI or faced a new site reality.
    OUTPUT: Just the action sentence.
    """
    payload = {"details": {"current_value": 0, "project_context": prompt}}
    try:
        resp = requests.post(AGENT_URL, json=payload)
        return "Simulated: " + resp.json().get('content').strip()
    except: return "Simulated: Manager unavailable."

def fetch_previous_learning(sh, pid, current_period, simulate_mode):
    try:
        w = sh.worksheet(LOG_SHEET)
        rows = w.get_all_values()
        if len(rows) < 2: return None
        
        headers = rows[0]
        cols = {h: i for i, h in enumerate(headers)}
        
        for r_idx, r in enumerate(rows):
            if r_idx == 0: continue
            
            # Find Previous Entry
            if r[cols["Project ID"]] == pid and r[cols["Period"]] != current_period:
                action_taken = r[cols["Actual Action Taken"]]
                data_source = "User Input (Verified)"
                
                # --- SIMULATION LOGIC ---
                if not action_taken:
                    if simulate_mode:
                        print(f"      🤖 Simulation Active for {r[cols['Period']]}...")
                        simulated_action = generate_simulated_manager_action(r[cols["AI Strategy"]], pid)
                        w.update_cell(r_idx + 1, cols["Actual Action Taken"] + 1, simulated_action)
                        action_taken = simulated_action
                        data_source = "⚠️ MISSING DATA (AI Simulation Triggered)"
                    else:
                        action_taken = "No action recorded."
                        data_source = "⚠️ MISSING DATA (Empty Cell)"
                # ------------------------

                return {
                    "period": r[cols["Period"]],
                    "prev_cpi": float(r[cols["CPI"]]),
                    "ai_advice": r[cols["AI Strategy"]],
                    "human_action": action_taken,
                    "source_status": data_source
                }
    except Exception as e:
        print(f"      ❌ History Error: {e}")
    return None

def fetch_slippage(sh, project_id, period):
    slippage = []
    try:
        rows = sh.worksheet(GANTT_SHEET).get_all_values()
        headers = rows[0]
        cols = {h: i for i, h in enumerate(headers)}
        for r in rows[1:]:
            if r[cols["Project ID"]] == project_id and r[cols["Report Period"]] == period:
                if r[cols["Baseline End"]] != r[cols["Forecast End"]]:
                    slippage.append(f"Task '{r[cols['Task Name']]}' slipped")
    except: pass
    return slippage

def run_agent_analysis(metrics, slippage, project_info, sh, simulate_mode):
    pid = project_info['id']
    pname = project_info['name']
    period = project_info['period']
    
    # 1. FETCH MEMORY
    memory = fetch_previous_learning(sh, pid, period, simulate_mode)
    
    # 2. BUILD DATA MANIFESTO (The List of Sources)
    data_audit_lines = []
    data_audit_lines.append(f"1. Budget Data: FOUND (Period {period})")
    data_audit_lines.append(f"2. Schedule Data: {'FOUND' if slippage else 'CHECKED (No Slippage)'}")
    
    learning_block = "No history."
    if memory:
        data_audit_lines.append(f"3. Manager Action: {memory['source_status']}")
        delta = metrics['cpi'] - memory['prev_cpi']
        result_type = "SUCCESS" if delta > 0 else "FAILURE"
        learning_block = f"""
        === PREVIOUS ACTION AUDIT ===
        Period: {memory['period']}
        1. AI Advice: "{memory['ai_advice'][:100]}..."
        2. MANAGER ACTION: "{memory['human_action']}"
        3. RESULT: {result_type} (CPI {memory['prev_cpi']} -> {metrics['cpi']})
        """
    else:
        data_audit_lines.append("3. Manager Action: NOT FOUND (First Run)")

    data_manifesto = "\n".join(data_audit_lines)

    # 3. THE PROMPT
    prompt = f"""
    You are a Senior Project Controller.
    
    --- DATA SOURCES AUDIT ---
    {data_manifesto}
    
    --- INPUT DATA ---
    Project: {pname}
    Current CPI: {metrics['cpi']}
    Variance: ${metrics['variance']:,.2f}
    
    {learning_block}
    
    --- BLEEDING ITEMS ---
    {", ".join(metrics["root_causes"]) if metrics["root_causes"] else "None"}
    
    --- OUTPUT FORMAT ---
    
    🚨 EXECUTIVE FLASH REPORT: {pname}
    
    --- DATA INTEGRITY CHECK ---
    [List the lines from 'DATA SOURCES AUDIT' here explicitly]

    1. MANAGER EFFECTIVENESS
    * **Action Source:** [State if this was Real User Input or AI Simulation]
    * **Analysis:** [Critique the action]

    2. CURRENT STATUS
    * **Financials:** CPI {metrics['cpi']}.
    * **Analysis:** [Brief comment]
    
    3. NEW STRATEGIC PLAN
    * **Corrective Action:** [Specific instruction].
    """

    payload = {"details": {"current_value": metrics["cpi"], "project_context": prompt}}
    try:
        resp = requests.post(AGENT_URL, json=payload)
        resp.raise_for_status()
        log_to_sheet(sh, pid, pname, period, metrics["cpi"], resp.json().get('content'))
    except Exception as e:
        print(f"❌ Agent Error: {e}")

def log_to_sheet(sh, pid, pname, period, cpi, content):
    try:
        try: w = sh.worksheet(LOG_SHEET)
        except: w = sh.add_worksheet(LOG_SHEET, 100, 10)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        w.append_row([timestamp, pid, pname, period, cpi, content, ""])
        print("   ✅ Report Logged.")
    except: pass

def main():
    sh = get_sh()
    print("\n" + "="*50)
    print("🚀 MISSION CONTROL: SIMULATION CENTER")
    print("="*50)
    
    # USER SELECTS SIMULATION
    user_input = input("🤖 Enable AI Manager Simulation? (y/n): ").strip().lower()
    simulate_mode = (user_input == 'y')

    try: budget_rows = sh.worksheet(BUDGET_SHEET).get_all_values()
    except: print("❌ Error reading Budget Sheet."); return

    active_projects = project_metrics.get_active_projects(budget_rows)
    
    for pid, info in active_projects.items():
        print(f"\n🔹 Processing {info['name']} ({info['latest_period']})...")
        metrics = project_metrics.calculate_financials(budget_rows, pid, info['latest_period'])
        slippage = fetch_slippage(sh, pid, info['latest_period'])
        run_agent_analysis(metrics, slippage, {'id': pid, 'name': info['name'], 'period': info['latest_period']}, sh, simulate_mode)

if __name__ == "__main__":
    main()