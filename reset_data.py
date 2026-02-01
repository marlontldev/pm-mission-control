import gspread
from oauth2client.service_account import ServiceAccountCredentials

# CONFIG
SPREADSHEET_NAME = "Mission Control Log"
JSON_KEYFILE = "credentials.json"

def reset_sheets():
    print("🔌 Connecting to Google Sheets...")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
    client = gspread.authorize(creds)
    sh = client.open(SPREADSHEET_NAME)

    # --- 1. RESET BUDGET SHEET (Multi-Period History) ---
    print("🛠️  Creating Realistic Project History...")
    try: w = sh.worksheet("Budget_Tracking"); w.clear()
    except: w = sh.add_worksheet("Budget_Tracking", 100, 20)
    
    budget_headers = ["Project ID", "Project Name", "Status", "Report Period", "Cost Category", "Budget (BAC)", "Earned Value (EV)", "Actual Cost (AC)", "CPI (EV/AC)"]
    
    budget_data = [
        budget_headers,
        # === PROJECT A: ALPHA TOWER (The "Ignoring Advice" Scenario) ===
        # JAN: Starting to slip (CPI 0.95)
        ["PROJ-001", "Alpha Tower", "Active", "2026-01", "1.0 Civil", "$800,000", "$400,000", "$420,000", 0.95],
        ["PROJ-001", "Alpha Tower", "Active", "2026-01", "TOTAL PROJECT", "$2,500,000", "$550,000", "$580,000", 0.95],
        
        # FEB: Got worse (CPI 0.88) because Manager added more crew (wrong move)
        ["PROJ-001", "Alpha Tower", "Active", "2026-02", "1.0 Civil", "$800,000", "$600,000", "$680,000", 0.88],
        ["PROJ-001", "Alpha Tower", "Active", "2026-02", "TOTAL PROJECT", "$2,500,000", "$1,000,000", "$1,136,000", 0.88],
        
        # MAR: Crisis (CPI 0.82) - CURRENT PERIOD
        ["PROJ-001", "Alpha Tower", "Active", "2026-03", "1.0 Civil", "$800,000", "$700,000", "$850,000", 0.82],
        ["PROJ-001", "Alpha Tower", "Active", "2026-03", "3.0 Robotic Grid", "$900,000", "$100,000", "$150,000", 0.66],
        ["PROJ-001", "Alpha Tower", "Active", "2026-03", "TOTAL PROJECT", "$2,500,000", "$1,300,000", "$1,585,000", 0.82],

        # === PROJECT B: BETA BRIDGE (The "Success" Scenario) ===
        # JAN: Bad Start (CPI 0.90)
        ["PROJ-002", "Beta Bridge", "Active", "2026-01", "1.0 Piling", "$1,200,000", "$200,000", "$222,000", 0.90],
        ["PROJ-002", "Beta Bridge", "Active", "2026-01", "TOTAL PROJECT", "$5,000,000", "$200,000", "$222,000", 0.90],
        
        # FEB: Recovery (CPI 0.98) because Manager negotiated steel
        ["PROJ-002", "Beta Bridge", "Active", "2026-02", "1.0 Piling", "$1,200,000", "$600,000", "$612,000", 0.98],
        ["PROJ-002", "Beta Bridge", "Active", "2026-02", "TOTAL PROJECT", "$5,000,000", "$600,000", "$612,000", 0.98],
        
        # MAR: Success (CPI 1.02) - CURRENT PERIOD
        ["PROJ-002", "Beta Bridge", "Active", "2026-03", "1.0 Piling", "$1,200,000", "$1,000,000", "$980,000", 1.02],
        ["PROJ-002", "Beta Bridge", "Active", "2026-03", "TOTAL PROJECT", "$5,000,000", "$1,000,000", "$980,000", 1.02]
    ]
    w.update("A1", budget_data)

    # --- 2. RESET GANTT SHEET ---
    print("🛠️  Resetting 'Schedule_Gantt'...")
    try: w = sh.worksheet("Schedule_Gantt"); w.clear()
    except: w = sh.add_worksheet("Schedule_Gantt", 100, 20)

    gantt_headers = ["Project ID", "Report Period", "Task Name", "Baseline End", "Forecast End"]
    gantt_data = [
        gantt_headers,
        ["PROJ-001", "2026-03", "Robotic Grid Install", "Aug-16", "Sep-01"], # 15 days late
        ["PROJ-002", "2026-03", "Bridge Decking", "Sep-01", "Sep-01"]       # On Time
    ]
    w.update("A1", gantt_data)

    # --- 3. RESET LOG SHEET (Populating History with User Actions) ---
    print("🛠️  Seeding 'AI_Analysis_Log' with Past Manager Actions...")
    try: w = sh.worksheet("AI_Analysis_Log"); w.clear()
    except: w = sh.add_worksheet("AI_Analysis_Log", 100, 20)

    log_headers = ["Timestamp", "Project ID", "Project Name", "Period", "CPI", "AI Strategy", "Actual Action Taken"]
    
    log_data = [
        log_headers,
        # ALPHA TOWER HISTORY (Jan & Feb)
        ["2026-01-31", "PROJ-001", "Alpha Tower", "2026-01", 0.95, "Recommendation: Reduce overtime to control costs.", "Ignored. Authorized double overtime to catch up schedule."],
        ["2026-02-28", "PROJ-001", "Alpha Tower", "2026-02", 0.88, "Recommendation: Halt overtime immediately. Audit material waste.", "Reduced overtime slightly. No audit performed."],
        
        # BETA BRIDGE HISTORY (Jan & Feb)
        ["2026-01-31", "PROJ-002", "Beta Bridge", "2026-01", 0.90, "Recommendation: Renegotiate steel prices.", "Held emergency meeting with Supplier X. Secured 5% discount."],
        ["2026-02-28", "PROJ-002", "Beta Bridge", "2026-02", 0.98, "Recommendation: Continue current path.", "Maintained strict cost controls."]
    ]
    w.update("A1", log_data)
    w.format("A1:G1", {"textFormat": {"bold": True}})
    w.set_column_width(6, 400) # AI Strategy Column
    w.set_column_width(7, 300) # User Action Column

    print("✅ SUCCESS: Data Environment Ready.")

if __name__ == "__main__":
    reset_sheets()