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

    # --- 1. RESET BUDGET SHEET (With Project ID) ---
    print("🛠️  Resetting 'Budget_Tracking' with Multi-Project Data...")
    try: w = sh.worksheet("Budget_Tracking"); w.clear()
    except: w = sh.add_worksheet("Budget_Tracking", 100, 20)
    
    # We add "Project ID" and "Status" columns
    budget_headers = ["Project ID", "Project Name", "Status", "Report Period", "Cost Category", "Budget (BAC)", "Earned Value (EV)", "Actual Cost (AC)", "CPI (EV/AC)"]
    
    budget_data = [
        budget_headers,
        # PROJECT A: Active (Bad Performance)
        ["PROJ-001", "Alpha Tower", "Active", "2026-02", "1.0 Civil", "$800,000", "$800,000", "$850,000", 0.94],
        ["PROJ-001", "Alpha Tower", "Active", "2026-02", "3.0 Robotic Grid", "$900,000", "$100,000", "$160,000", 0.62],
        ["PROJ-001", "Alpha Tower", "Active", "2026-02", "TOTAL PROJECT", "$2,500,000", "$1,300,000", "$1,400,000", 0.92],
        
        # PROJECT B: Active (Good Performance)
        ["PROJ-002", "Beta Bridge", "Active", "2026-02", "1.0 Piling", "$1,200,000", "$1,200,000", "$1,150,000", 1.04],
        ["PROJ-002", "Beta Bridge", "Active", "2026-02", "TOTAL PROJECT", "$5,000,000", "$1,200,000", "$1,150,000", 1.04],

        # PROJECT C: Closed (Should be ignored by Agent)
        ["PROJ-003", "Gamma Road", "Closed", "2025-12", "TOTAL PROJECT", "$1,000,000", "$1,000,000", "$1,000,000", 1.00]
    ]
    w.update("A1", budget_data)

    # --- 2. RESET GANTT SHEET (With Project ID) ---
    print("🛠️  Resetting 'Schedule_Gantt'...")
    try: w = sh.worksheet("Schedule_Gantt"); w.clear()
    except: w = sh.add_worksheet("Schedule_Gantt", 100, 20)

    gantt_headers = ["Project ID", "Report Period", "Task Name", "Baseline End", "Forecast End"]
    gantt_data = [
        gantt_headers,
        ["PROJ-001", "2026-02", "Robotic Grid Install", "Aug-16", "Aug-26"], # Slipped
        ["PROJ-002", "2026-02", "Bridge Decking", "Sep-01", "Sep-01"]       # On Time
    ]
    w.update("A1", gantt_data)

    print("✅ SUCCESS: Multi-Project Dataset Created.")

if __name__ == "__main__":
    reset_sheets()