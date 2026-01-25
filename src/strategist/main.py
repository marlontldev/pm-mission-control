import os
import logging
from flask import Flask, request, jsonify
import vertexai
from vertexai.generative_models import GenerativeModel

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "your-project-id")
LOCATION = os.environ.get("REGION", "us-central1")

# Initialize Vertex AI (Only if not in mock mode)
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel("gemini-2.5-flash") # Or "gemini-1.0-pro"
    AI_ENABLED = True
except Exception as e:
    logging.warning(f"Vertex AI could not initialize (Auth missing?): {e}")
    AI_ENABLED = False

@app.route("/", methods=["POST"])
def strategize():
    """
    Receives a Risk Alert and generates a Recovery Plan.
    """
    data = request.json
    logging.info(f"Strategist received alert: {data}")

    # 1. Extract Context (The "Observation" step)
    cpi = data.get("details", {}).get("current_value", 0.0)
    
    # 2. Mock Tool Use: Fetching Schedule Constraints
    # In production, this would query Google Sheets/Jira API
    project_context = f"""
    Project Status:
    - Current Phase: Foundation Pouring
    - CPI: {cpi} (Budget Overrun)
    - Schedule Slack: 2 days
    - Critical Path: Excavation -> Foundation -> Steel Framing
    """

    # 3. Reasoning (The "Thinking" step)
    if AI_ENABLED:
        prompt = f"""
        You are a Senior Project Manager. Analyze this situation and propose a recovery plan.
        
        CONTEXT:
        {project_context}
        
        TASK:
        Provide a concise strategy to recover costs without delaying the Critical Path.
        """
        
        response = model.generate_content(prompt)
        advice = response.text
    else:
        advice = "[MOCK] Vertex AI disabled. Strategy: Cut costs on non-critical tasks."

    # 4. Return the Artifact
    artifact = {
        "strategy_id": "plan-alpha-1",
        "target_audience": "Project Manager",
        "content": advice
    }
    
    logging.info(f"Strategy Generated: {advice[:50]}...")
    return jsonify(artifact)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8081)