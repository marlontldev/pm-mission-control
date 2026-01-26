import requests
import json
import csv
import os
from datetime import datetime

# CONFIGURATION
AGENT_URL = "http://localhost:8081/"
LOG_FILE = "mission_log.csv"

def consult_strategist(current_cpi):
    """Sends project data to the AI Agent and logs the response."""
    
    # 1. Prepare the Data
    payload = {
        "details": {
            "current_value": current_cpi
        }
    }

    try:
        # 2. Call the Agent
        print(f"📡 Contacting Strategist Agent at {AGENT_URL}...")
        response = requests.post(AGENT_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        # 3. Display Professional Output
        print("\n" + "="*60)
        print(f"🤖 STRATEGIST AGENT REPORT")
        print(f"📅 Date: {data.get('timestamp')}")
        print(f"📉 Status (CPI): {current_cpi}")
        print("-" * 60)
        print(f"📋 RECOVERY PLAN:\n")
        print(data.get('content'))
        print("="*60 + "\n")

        # 4. Log to CSV (The "Database" for your Graph)
        log_entry = [
            data.get('timestamp'),
            current_cpi,
            data.get('content').replace('\n', ' ') # Flatten for CSV
        ]
        
        save_to_log(log_entry)

    except Exception as e:
        print(f"❌ Error: {e}")

def save_to_log(entry):
    """Appends the event to a CSV file."""
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header if new file
        if not file_exists:
            writer.writerow(["Timestamp", "CPI_Value", "AI_Strategy_Summary"])
        
        writer.writerow(entry)
    print(f"✅ Recorded in {LOG_FILE}")

if __name__ == "__main__":
    # You can change this value to test different scenarios
    cpi_input = float(input("Enter current CPI (e.g., 0.85): "))
    consult_strategist(cpi_input)