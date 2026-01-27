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

    # --- 1. RESET BUDGET SHEET ---
    print("🛠️  Resetting 'Budget_Tracking'...")
    try:
        w = sh.worksheet("Budget_Tracking")
        w.clear()
    except:
        w = sh.add_worksheet("Budget_Tracking", 100, 20)
    
    budget_data = [
        ["Report Period", "Report Date", "Cost Category", "Budget (BAC)", "Earned Value (EV)", "Actual Cost (AC)", "CPI (EV/AC)"],
        ["2026-01", "2026-01-31", "1.0 Civil / Structure", "$800,000", "$400,000", "$400,000", 1.00],
        ["2026-01", "2026-01-31", "TOTAL PROJECT", "$2,500,000", "$550,000", "$550,000", 1.00],
        ["2026-02", "2026-02-28", "1.0 Civil / Structure", "$800,000", "$800,000", "$850,000", 0.94],
        ["2026-02", "2026-02-28", "TOTAL PROJECT", "$2,500,000", "$1,300,000", "$1,400,000", 0.92]
    ]
    w.update("A1", budget_data)

    # --- 2. RESET GANTT SHEET ---
    print("🛠️  Resetting 'Schedule_Gantt'...")
    try:
        w = sh.worksheet("Schedule_Gantt")
        w.clear()
    except:
        w = sh.add_worksheet("Schedule_Gantt", 100, 20)

    gantt_data = [
        ["Report Period", "Report Date", "Task ID", "Task Name", "Status", "Baseline Start", "Baseline End", "Forecast Start", "Forecast End", "Critical?", "Dependency"],
        ["2026-01", "2026-01-31", "1.1", "Excavation", "Done", "Jan-01", "Mar-15", "Jan-01", "Mar-15", "No", "-"],
        ["2026-02", "2026-02-28", "3.2", "Robotic Grid Install", "Blocked", "Aug-16", "Oct-01", "Aug-26", "Oct-10", "Yes", "3.1"]
    ]
    w.update("A1", gantt_data)

    print("✅ SUCCESS: Sheets have been formatted correctly.")

if __name__ == "__main__":
    reset_sheets()