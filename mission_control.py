import warnings
warnings.filterwarnings("ignore", category=FutureWarning) # Fixes the console spam

import requests
import gspread
# Replace the old imports
from google.oauth2.service_account import Credentials # Modern library
# from oauth2client.service_account import ServiceAccountCredentials # Remove this line

from datetime import datetime
import project_metrics 
from prompt_engine import ExecutiveReportContext # Import the new module

# CONFIG
AGENT_URL = "http://localhost:8081/"
SPREADSHEET_NAME = "Mission Control Log"
JSON_KEYFILE = "credentials.json"

def get_sh():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # This reads your credentials.json perfectly
    creds = Credentials.from_service_account_file(JSON_KEYFILE, scopes=scope)
    return gspread.authorize(creds).open(SPREADSHEET_NAME)

def generate_simulated_manager_action(ai_advice, project_name):
    """Roleplays the Operations Manager if data is missing."""
    prompt = f"""
    ROLE: Operations Director for {project_name}.
    CONTEXT: Last month AI advised: "{ai_advice}"
    TASK: Write a 1-sentence "Actual Action Taken". 
    SCENARIO: You had conflicting site priorities.
    OUTPUT: Just the action sentence.
    """
    try:
        payload = {"details": {"current_value": 0, "project_context": prompt}}
        resp = requests.post(AGENT_URL, json=payload)
        return "Simulated: " + resp.json().get('content').strip()
    except: return "Simulated: Manager unavailable."

def fetch_previous_learning(sh, pid, current_period, simulate_mode):
    try:
        w = sh.worksheet("AI_Analysis_Log")
        rows = w.get_all_values()
        if len(rows) < 2: return None
        
        headers = rows[0]
        cols = {h: i for i, h in enumerate(headers)}
        
        # Robust check to ensure columns exist
        if "Project ID" not in cols or "Actual Action Taken" not in cols:
            return None

        for r_idx, r in enumerate(rows):
            if r_idx == 0: continue
            
            # Logic: Find the row for this project from a DIFFERENT period
            if r[cols["Project ID"]] == pid and r[cols["Period"]] != current_period:
                action_taken = r[cols["Actual Action Taken"]]
                data_source = "User Input (Verified)"
                
                # --- SIMULATION LOGIC ---
                if not action_taken or action_taken.strip() == "":
                    if simulate_mode:
                        print(f"      🤖 Simulation Active: Roleplaying Manager for {r[cols['Period']]}...")
                        simulated_action = generate_simulated_manager_action(r[cols["AI Strategy"]], pid)
                        # Write back to Sheet so we remember it next time
                        w.update_cell(r_idx + 1, cols["Actual Action Taken"] + 1, simulated_action)
                        action_taken = simulated_action
                        data_source = "⚠️ MISSING DATA (AI Simulation Triggered)"
                    else:
                        action_taken = "No action recorded."
                        data_source = "⚠️ MISSING DATA (Empty Cell)"
                # ------------------------

                return {
                    "prev_cpi": float(r[cols["CPI"]]),
                    "human_action": action_taken,
                    "source_status": data_source
                }
    except Exception as e:
        print(f"      ❌ History Read Error: {e}")
    return None

def run_agent_analysis(metrics, slippage, project_info, sh, simulate_mode):
    pid = project_info['id']
    pname = project_info['name']
    period = project_info['period']
    
    # 1. FETCH MEMORY
    memory = fetch_previous_learning(sh, pid, period, simulate_mode)
    
    # 2. BUILD AUDIT LIST
    audit_list = [f"1. Budget Data: FOUND (Period {period})"]
    
    prev_action_text = None
    prev_result_text = None

    if memory:
        audit_list.append(f"2. Manager Action: {memory['source_status']}")
        delta = metrics['cpi'] - memory['prev_cpi']
        res_type = "SUCCESS" if delta > 0 else "FAILURE"
        prev_action_text = memory['human_action']
        prev_result_text = f"{res_type} (CPI {memory['prev_cpi']} -> {metrics['cpi']})"
    else:
        audit_list.append("2. Manager Action: NOT FOUND (First Run)")

    # 3. USE PROMPT ENGINE (Pydantic)
    try:
        context = ExecutiveReportContext(
            project_name=pname,
            cpi=metrics['cpi'],
            variance=metrics['variance'],
            bleeding_items=metrics['root_causes'],
            data_sources=audit_list,
            prev_action=prev_action_text,
            prev_result=prev_result_text
        )
        final_prompt = context.render()
        
    except Exception as e:
        print(f"❌ Pydantic Validation Error: {e}")
        return

    # 4. SEND TO AI
    try:
        payload = {"details": {"current_value": metrics["cpi"], "project_context": final_prompt}}
        resp = requests.post(AGENT_URL, json=payload)
        
        # Log to Sheet
        w = sh.worksheet("AI_Analysis_Log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        w.append_row([timestamp, pid, pname, period, metrics["cpi"], resp.json().get('content'), ""])
        print("   ✅ Report Logged.")
    except Exception as e:
        print(f"❌ AI Error: {e}")

def main():
    sh = get_sh()
    print("\n🚀 MISSION CONTROL: SIMULATION CENTER")
    
    user_input = input("🤖 Enable AI Manager Simulation? (y/n): ").strip().lower()
    simulate_mode = (user_input == 'y')

    try: budget_rows = sh.worksheet("Budget_Tracking").get_all_values()
    except: print("❌ Error reading Budget Sheet."); return

    active_projects = project_metrics.get_active_projects(budget_rows)
    
    for pid, info in active_projects.items():
        print(f"\n🔹 Processing {info['name']} ({info['latest_period']})...")
        metrics = project_metrics.calculate_financials(budget_rows, pid, info['latest_period'])
        run_agent_analysis(metrics, [], {'id': pid, 'name': info['name'], 'period': info['latest_period']}, sh, simulate_mode)

if __name__ == "__main__":
    main()