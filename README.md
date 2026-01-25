🚀 PM Mission Control (Agentic AI System)

PM Mission Control is an autonomous, "Loop-in-the-Loop" agentic system designed to monitor Project Management KPIs (like CPI and SPI) and generate strategic recovery plans using Generative AI.

Unlike passive dashboards, this system features active agents that perceive project risks and reason through solutions using Google Vertex AI.
🏗️ Architecture

The system consists of two primary agents running as microservices:

    Agent A: The Sentinel (Reactive Layer)

        Role: The Nervous System.

        Function: Monitors raw event data (simulated BigQuery/Logs). If a threshold is breached (e.g., CPI < 0.9), it instantly flags a risk.

        Tech: Python, Cloud Functions logic.

    Agent B: The Strategist (Deliberative Layer)

        Role: The Brain.

        Function: Receives risk alerts, retrieves project context (Critical Path, Schedule), and uses Gemini 1.5 Flash to generate a recovery strategy.

        Tech: Python, Flask, Vertex AI.

Code snippet

graph TD
    User([User / Event Source]) -->|1. HTTP POST| Sentinel[Agent A: Sentinel]
    Sentinel -->|2. Detect Breach| Sentinel
    Sentinel -->|3. Trigger (HTTP)| Strategist[Agent B: Strategist]
    Strategist -->|4. Reason| VertexAI[Google Vertex AI]
    VertexAI -- Strategy --> Strategist
    Strategist -- JSON Plan --> Sentinel
    Sentinel -- Log Output --> User

🛠️ Prerequisites

Before running the system, ensure you have the following installed in your WSL/Linux environment:

    Docker & Docker Compose

    Google Cloud SDK (gcloud)

    Python 3.11+ (for local scripts, optional)

Critical Setup Step

You must authenticate with Google Cloud locally so the Docker containers can access Vertex AI:
Bash

gcloud auth application-default login

🚀 Quick Start
1. Clone & Configure

Navigate to the project directory:
Bash

cd ~/Repos/pm-mission-control

2. Build & Launch

Use Docker Compose to build the images and start the agent network:
Bash

docker-compose up --build

You will see logs from both sentinel-live and strategist-live indicating they are listening on ports 8080 and 8081.
3. Trigger the Simulation

Open a new terminal tab and trigger the Sentinel with a mock "BigQuery" event. This starts the autonomous loop:
Bash

curl -X POST localhost:8080 \
  -H "Content-Type: application/json" \
  -H "ce-id: 12345" \
  -H "ce-specversion: 1.0" \
  -H "ce-type: google.cloud.audit.log.v1.written" \
  -H "ce-source: //cloudaudit.googleapis.com/projects/my-project/logs/activity" \
  -d '{"protoPayload": {"serviceName": "bigquery.googleapis.com"}}'

4. Verify Output

Switch back to your Docker terminal. You should see:

    Sentinel: BREACH DETECTED: CPI 0.82 < 0.9

    Sentinel: [LOCAL] Triggering Strategist...

    Strategist: Strategist received alert...

    Sentinel: [LOCAL] Strategist Response: { "content": "Okay, Project Team..." }

📂 Project Structure
Plaintext

pm-mission-control/
├── docker-compose.yml       # Local orchestration
├── infrastructure/          # Terraform (Cloud Deployment)
│   ├── main.tf
│   └── iam.tf
├── src/
│   ├── sentinel/            # Agent A Source Code
│   │   ├── main.py
│   │   └── requirements.txt
│   └── strategist/          # Agent B Source Code
│       ├── main.py          # Flask App + Vertex AI Logic
│       ├── Dockerfile
│       └── requirements.txt
└── README.md

⚠️ Configuration

The system behavior is controlled by environment variables in docker-compose.yml:
Variable	Description	Default
PROJECT_ID	Controls mode. Set to local-test for HTTP loop, or real ID for Pub/Sub.	pm-mission-control
CPI_THRESHOLD	The financial KPI limit.	0.9
REGION	GCP Region for Vertex AI calls.	us-central1
📜 License

Private / Proprietary.