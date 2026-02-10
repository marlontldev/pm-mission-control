from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import google.generativeai as genai
from google.oauth2 import service_account

# CONFIG
HOST_NAME = "0.0.0.0" # Listen on all interfaces for Docker
SERVER_PORT = 8081
CREDENTIALS_FILE = "credentials.json"

class BrainHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. SETUP AUTH (The Official Way)
            creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
            
            # Configure the library with your credentials
            # Note: The library usually looks for API_KEY, but with Vertex/Enterprise
            # we configure it via Google Cloud directly. 
            # For simplicity in this specific library version, we stick to the 
            # REST method IF using Service Accounts, OR use the API Key method.
            
            # ... [Wait] ...
            # Actually, for PURE Service Account usage without an API Key, 
            # the REST method I gave you previously is STILL the most robust 
            # "No-Magic" way. The official library is optimized for API Keys.
            
            # LET'S STICK TO THE REST API VERSION FOR STABILITY 
            # UNLESS YOU HAVE A "VERTEX AI" ENDPOINT SET UP.
            
            # (Keeping your current brain_server.py is perfectly fine and standard).
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"content": "Brain is running on Python 3.11!"}')

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

if __name__ == "__main__":
    print(f"🧠 ENTERPRISE BRAIN (Python 3.11) STARTED on port {SERVER_PORT}")
    server = HTTPServer((HOST_NAME, SERVER_PORT), BrainHandler)
    server.serve_forever()