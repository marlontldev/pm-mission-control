import functions_framework
import os
import json
import logging
# We import 'requests' to allow this agent to make HTTP calls to other agents.
# This is critical for our local simulation loop.
import requests  
from google.cloud import pubsub_v1

# Setup standard logging so we can see output in the Docker terminal.
logging.basicConfig(level=logging.INFO)

# --- CONFIGURATION ---
# PROJECT_ID: Used to determine if we are running locally or in Google Cloud.
PROJECT_ID = os.environ.get("PROJECT_ID", "local-test")

# TOPIC_NAME: The Pub/Sub topic name for the "Nervous System" (Cloud mode only).
TOPIC_NAME = os.environ.get("PUBSUB_TOPIC", "risk-events")

# CPI_THRESHOLD: The financial safety limit. Anything below 0.9 triggers a risk.
CPI_THRESHOLD = float(os.environ.get("CPI_THRESHOLD", 0.9))

# STRATEGIST_URL: The internal Docker address of Agent B.
# 'http://strategist:8081' works because Docker Compose creates a
# DNS entry named 'strategist' automatically for us.
STRATEGIST_URL = os.environ.get("STRATEGIST_URL", "http://strategist:8081")

@functions_framework.cloud_event
def analyze_event(cloud_event):
    """
    The entry point. This function runs every time an event occurs
    (e.g., a BigQuery job finishes or we send a manual curl command).
    """
    try:
        logging.info(f"Event Received: {cloud_event['id']}")
        
        # --- 1. SENSE (Simulated Data Collection) ---
        # In a real app, we would query BigQuery here.
        # For this test, we force the CPI to 0.82 to simulate a "Budget Breach".
        current_cpi = 0.82 
        
        logging.info(f"Sentinel Analysis: CPI={current_cpi}")

        # --- 2. THINK (Reactive Logic) ---
        # Compare the sensed data against our rule (Threshold < 0.9).
        if current_cpi < CPI_THRESHOLD:
            logging.warning(f"BREACH DETECTED: CPI {current_cpi} < {CPI_THRESHOLD}")

            # Prepare the "Risk Artifact" (JSON payload) to send to the brain.
            risk_payload = {
                "event_id": cloud_event["id"],
                "alert_type": "CPI_BREACH",
                "details": { 
                    "current_value": current_cpi, 
                    "threshold": CPI_THRESHOLD 
                }
            }

            # --- 3. ACT (Communication) ---
            # This block determines HOW we talk to the Strategist.
            
            # CONDITION: If we are running locally (Docker)
            if PROJECT_ID == "local-test" or PROJECT_ID == "pm-mission-control":
                # STRATEGY: Direct Connection (HTTP)
                # We skip Pub/Sub because it's complex to emulate locally.
                # Instead, we just POST the JSON directly to Agent B's port 8081.
                logging.info(f"[LOCAL] Triggering Strategist at {STRATEGIST_URL}...")
                try:
                    response = requests.post(STRATEGIST_URL, json=risk_payload)
                    # We log the Strategist's reply immediately to prove the loop worked.
                    logging.info(f"[LOCAL] Strategist Response: {response.json()}")
                except Exception as req_err:
                    logging.error(f"[LOCAL] Failed to call Strategist: {req_err}")
            
            # CONDITION: If we are running in the Real Cloud (GCP)
            else:
                # STRATEGY: Event-Driven (Pub/Sub)
                # We publish the message to the 'risk-events' topic.
                # The Strategist will pick it up asynchronously.
                publisher = pubsub_v1.PublisherClient()
                topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
                data_str = json.dumps(risk_payload).encode("utf-8")
                
                publisher.publish(topic_path, data_str)
                logging.info("Risk Alert Published to Pub/Sub.")
                
    except Exception as e:
        # Catch-all error handler to prevent the container from crashing silenty.
        logging.error(f"Error in Sentinel Agent: {e}")
        raise e