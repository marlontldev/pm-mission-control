import functions_framework
import os
import json
import logging
import requests
import google.auth
import gspread
from google.cloud import pubsub_v1

logging.basicConfig(level=logging.INFO)

# --- CONFIGURATION ---
PROJECT_ID = os.environ.get("PROJECT_ID", "local-test")
TOPIC_NAME = os.environ.get("PUBSUB_TOPIC", "risk-events")
CPI_THRESHOLD = float(os.environ.get("CPI_THRESHOLD", 0.9))
STRATEGIST_URL = os.environ.get("STRATEGIST_URL", "http://strategist:8081")

# Sheets Config (No more CPI_CELL)
SHEET_NAME = os.environ.get("SHEET_NAME", "Project_Alpha_Master")
TAB_NAME = os.environ.get("TAB_NAME", "Budget_Tracking")

def find_critical_tasks():
    """
    Scans the entire Budget_Tracking sheet.
    Returns the task with the LOWEST CPI if it is below the threshold.
    """
    try:
        # 1. Authenticate & Open
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds, _ = google.auth.default(scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).worksheet(TAB_NAME)

        # 2. Fetch All Data (Returns a list of dictionaries)
        # Expected Headers: ['Cost Category', 'Budget (BAC)', 'Earned (EV)', 'Actual (AC)', 'CPI']
        all_records = sheet.get_all_records()
        
        logging.info(f"Scanned {len(all_records)} project rows.")

        critical_task = None
        min_cpi = 100.0 # Start high

        # 3. Analyze Each Row
        for row in all_records:
            task_name = row.get("Cost Category", "Unknown Task")
            raw_cpi = row.get("CPI")

            # Skip header rows or empty lines
            if raw_cpi == "" or raw_cpi is None:
                continue

            try:
                cpi_value = float(raw_cpi)
            except ValueError:
                continue # Skip if CPI is text

            logging.info(f"Analyzing {task_name}: CPI={cpi_value}")

            # Logic: Track the 'worst' CPI that is below threshold
            if cpi_value < CPI_THRESHOLD:
                if cpi_value < min_cpi:
                    min_cpi = cpi_value
                    critical_task = {
                        "task_name": task_name,
                        "cpi": cpi_value,
                        "budget": row.get("Budget (BAC)")
                    }

        return critical_task

    except Exception as e:
        logging.error(f"Failed to scan Google Sheet: {e}")
        return None

@functions_framework.cloud_event
def analyze_event(cloud_event):
    try:
        logging.info(f"Event Received: {cloud_event['id']}")
        
        # --- 1. SENSE (Dynamic Scanning) ---
        logging.info("Scanning project for critical risks...")
        worst_offender = find_critical_tasks()

        if worst_offender:
            current_cpi = worst_offender['cpi']
            task_name = worst_offender['task_name']
            
            logging.warning(f"CRITICAL BREACH FOUND: {task_name} (CPI {current_cpi})")

            # --- 2. THINK (Prepare Context) ---
            risk_payload = {
                "event_id": cloud_event["id"],
                "alert_type": "CPI_BREACH",
                "details": { 
                    "current_value": current_cpi, 
                    "threshold": CPI_THRESHOLD,
                    "failing_task": task_name, # Identifying WHO is failing
                    "source": f"Sheet: {SHEET_NAME}"
                }
            }

            # --- 3. ACT (Trigger Strategist) ---
            if PROJECT_ID == "local-test" or PROJECT_ID == "pm-mission-control":
                logging.info(f"[LOCAL] Triggering Strategist for {task_name}...")
                requests.post(STRATEGIST_URL, json=risk_payload)
            else:
                publisher = pubsub_v1.PublisherClient()
                topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
                data_str = json.dumps(risk_payload).encode("utf-8")
                publisher.publish(topic_path, data_str)
        else:
            logging.info("Scan complete. All tasks are healthy.")
                
    except Exception as e:
        logging.error(f"Error in Sentinel Agent: {e}")
        raise e