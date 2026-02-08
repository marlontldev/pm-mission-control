import gspread
from oauth2client.service_account import ServiceAccountCredentials

# CONFIGURATION
SPREADSHEET_NAME = "Mission Control Log"
JSON_KEYFILE = "credentials.json"

def reset_sheets():
    print("🔌 Connecting to Google Sheets...")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
    client = gspread.authorize(creds)
    
    try:
        sh = client.open(SPREADSHEET_NAME)
    except gspread.SpreadsheetNotFound:
        print(f"❌ Error: Spreadsheet '{SPREADSHEET_NAME}' not found.")
        return

    # ==========================================
    # 1. RESET BUDGET SHEET (With Full History)
    # ==========================================
    print("🛠️  Resetting 'Budget_Tracking'...")
    try: w = sh.worksheet("Budget_Tracking"); w.clear()
    except: w = sh.add_worksheet("Budget_Tracking", 100, 20)
    
    budget_headers = [
        "Project ID", "Project Name", "Status", "Report Period", "Cost Category", 
        "Budget (BAC)", "Planned Value (PV)", "Earned Value (EV)", "Actual Cost (AC)", "CPI (EV/AC)"
    ]
    
    budget_data = [budget_headers]

    # --- HISTORY: Oct 2025 to Feb 2026 (Context for Trend Analysis) ---
    # Alpha Tower (Degrading Trend)
    budget_data.append(["PROJ-001", "Alpha Tower", "Active", "2025-10", "TOTAL PROJECT", "$2,500,000", "$200,000", "$200,000", "$200,000", 1.00])
    budget_data.append(["PROJ-001", "Alpha Tower", "Active", "2025-11", "TOTAL PROJECT", "$2,500,000", "$500,000", "$480,000", "$500,000", 0.96])
    budget_data.append(["PROJ-001", "Alpha Tower", "Active", "2025-12", "TOTAL PROJECT", "$2,500,000", "$900,000", "$850,000", "$910,000", 0.93])
    budget_data.append(["PROJ-001", "Alpha Tower", "Active", "2026-01", "TOTAL PROJECT", "$2,500,000", "$1,200,000", "$1,000,000", "$1,090,000", 0.92])
    budget_data.append(["PROJ-001", "Alpha Tower", "Active", "2026-02", "TOTAL PROJECT", "$2,500,000", "$1,500,000", "$1,200,000", "$1,363,000", 0.88])

    # --- CURRENT PERIOD: March 2026 (The detailed breakdown from your image) ---
    # Alpha Tower (Critical Issues)
    budget_data.append(["PROJ-001", "Alpha Tower", "Active", "2026-03", "1.0 Civil", "$800,000", "$750,000", "$700,000", "$850,000", 0.82])
    budget_data.append(["PROJ-001", "Alpha Tower", "Active", "2026-03", "3.0 Robotic Grid", "$900,000", "$200,000", "$100,000", "$150,000", 0.66])
    budget_data.append(["PROJ-001", "Alpha Tower", "Active", "2026-03", "TOTAL PROJECT", "$2,500,000", "$1,800,000", "$1,300,000", "$1,585,000", 0.82])

    # Beta Bridge (Performing Well)
    budget_data.append(["PROJ-002", "Beta Bridge", "Active", "2026-03", "1.0 Piling", "$1,200,000", "$1,000,000", "$1,000,000", "$980,000", 1.02])
    budget_data.append(["PROJ-002", "Beta Bridge", "Active", "2026-03", "TOTAL PROJECT", "$5,000,000", "$1,500,000", "$1,500,000", "$1,470,000", 1.02])

    w.update("A1", budget_data)
    w.format("A1:J1", {"textFormat": {"bold": True}})

    # ==========================================
    # 2. RESET GANTT SHEET (Complex Structure)
    # ==========================================
    print("🛠️  Resetting 'Schedule_Gantt' with Complex Dependencies...")
    try: w = sh.worksheet("Schedule_Gantt"); w.clear()
    except: w = sh.add_worksheet("Schedule_Gantt", 100, 20)

    # 11 Columns to match your screenshot
    gantt_headers = [
        "Project ID", "Report Period", "Task ID", "Task Name", "Status", 
        "Baseline Start", "Baseline End", "Forecast Start", "Forecast End", 
        "Critical?", "Dependency"
    ]
    
    gantt_data = [gantt_headers]

    # --- PROJ-001: Alpha Tower (2026-03) ---
    # Matches the complexity of your screenshot: Delayed items, Blocked items, Critical Path
    gantt_data.append(["PROJ-001", "2026-03", "1.1", "Excavation & Shoring", "Done", "2026-01-01", "2026-02-15", "2026-01-01", "2026-02-15", "No", "-"])
    gantt_data.append(["PROJ-001", "2026-03", "1.2", "Concrete Foundation", "Done", "2026-02-16", "2026-03-10", "2026-02-16", "2026-03-10", "No", "1.1"])
    gantt_data.append(["PROJ-001", "2026-03", "2.1", "Structural Steel Frame", "In Progress", "2026-03-11", "2026-05-01", "2026-03-11", "2026-05-05", "Yes", "1.2"]) # 4 Days Slip
    gantt_data.append(["PROJ-001", "2026-03", "2.2", "MEP Rough-In", "In Progress", "2026-04-01", "2026-06-01", "2026-04-05", "2026-06-05", "No", "2.1"])
    gantt_data.append(["PROJ-001", "2026-03", "3.1", "Super-Flat Floor Pour", "Delayed", "2026-05-02", "2026-05-20", "2026-05-10", "2026-05-30", "Yes", "2.1"]) # 10 Days Slip
    gantt_data.append(["PROJ-001", "2026-03", "3.2", "Robotic Grid Install", "Blocked", "2026-05-21", "2026-07-15", "2026-06-01", "2026-08-01", "Yes", "3.1"]) # Major Slip
    gantt_data.append(["PROJ-001", "2026-03", "4.1", "Digital Twin Sim", "Pending", "2026-06-01", "2026-08-01", "2026-06-01", "2026-08-01", "No", "-"])

    # --- PROJ-002: Beta Bridge (2026-03) ---
    gantt_data.append(["PROJ-002", "2026-03", "1.0", "Site Mobilization", "Done", "2026-01-01", "2026-01-15", "2026-01-01", "2026-01-15", "No", "-"])
    gantt_data.append(["PROJ-002", "2026-03", "1.1", "Riverbed Piling", "Done", "2026-01-16", "2026-03-01", "2026-01-16", "2026-02-28", "Yes", "1.0"]) # Early Finish
    gantt_data.append(["PROJ-002", "2026-03", "2.1", "Pier Cap Casting", "In Progress", "2026-03-02", "2026-04-15", "2026-03-02", "2026-04-15", "Yes", "1.1"])
    gantt_data.append(["PROJ-002", "2026-03", "2.2", "Girder Launching", "Pending", "2026-04-16", "2026-06-01", "2026-04-16", "2026-06-01", "Yes", "2.1"])

    w.update("A1", gantt_data)
    w.format("A1:K1", {"textFormat": {"bold": True}})
    w.set_column_width(4, 200) # Task Name
    w.set_column_width(6, 120) # Dates
    w.set_column_width(7, 120)
    w.set_column_width(8, 120)
    w.set_column_width(9, 120)

    # ==========================================
    # 3. RESET LOG SHEET (Seeding History)
    # ==========================================
    print("🛠️  Resetting 'AI_Analysis_Log'...")
    try: w = sh.worksheet("AI_Analysis_Log"); w.clear()
    except: w = sh.add_worksheet("AI_Analysis_Log", 100, 20)

    log_headers = [
        "Timestamp", "Project ID", "Project Name", "Period", "CPI", 
        "AI Strategy", "Actual Action Taken"
    ]
    
    # Seeding Feb 2026 history so the "Learning Loop" works for the March 2026 report
    log_data = [
        log_headers,
        [
            "2026-02-28 10:00:00", "PROJ-001", "Alpha Tower", "2026-02", "0.88", 
            "Critical Alert: CPI degrading. Recommending freeze on overtime.", 
            "Partial implementation. Overtime reduced but not frozen."
        ]
    ]
    w.update("A1", log_data)
    w.format("A1:G1", {"textFormat": {"bold": True}})
    w.set_column_width(6, 400) 
    w.set_column_width(7, 300)

    print("✅ SUCCESS: Complex Gantt Structure & Historical Data Loaded.")

if __name__ == "__main__":
    reset_sheets()