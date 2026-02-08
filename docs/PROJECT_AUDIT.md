# Project Audit

## Python File Documentation Audit

| File Path | Summary | Docstring Status |
| :--- | :--- | :--- |
| `mission_control.py` | Orchestrates the simulation loop by fetching project data from Google Sheets, calculating metrics, and triggering AI analysis via the Strategist agent. | **MISSING** (No module or function docstrings) |
| `project_metrics.py` | Provides utility functions for financial calculations (CPI, SPI, EAC), date parsing, and identifying active projects. | **PARTIAL** (Module docstring missing; `calculate_ai_forecast` has a docstring) |
| `reset_data.py` | Resets the Google Sheets (Budget, Gantt, Log) to a baseline state with sample historical data for testing purposes. | **MISSING** (No module or function docstrings) |
| `src/sentinel/main.py` | Implements the Sentinel agent as a Cloud Function to scan for risk events (CPI breaches) and trigger the Strategist. | **PARTIAL** (Module docstring missing; `find_critical_tasks` has a docstring) |
| `src/sentinel/__init__.py` | Marks the directory as a Python package. | **MISSING** (Empty file) |
| `src/strategist/main.py` | Implements the Strategist agent as a Flask application that uses Vertex AI to generate recovery strategies for detected risks. | **PARTIAL** (Module docstring missing; `strategize` has a docstring) |

## Recommended Improvements

1.  **Centralized Configuration:**
    *   **Observation:** Files like `mission_control.py`, `reset_data.py`, and `src/sentinel/main.py` contain hardcoded configuration values such as spreadsheet names ("Mission Control Log"), API URLs ("http://localhost:8081/"), and threshold values.
    *   **Recommendation:** Move these constants into a centralized configuration file (e.g., `config.py`) or use environment variables (via `.env` file). This improves security, makes the application easier to deploy in different environments (dev/prod), and reduces code duplication.

2.  **Root-level Dependency Management:**
    *   **Observation:** The root directory contains scripts like `mission_control.py` and `reset_data.py` that depend on external libraries (`gspread`, `requests`, `oauth2client`), but there is no `requirements.txt` file in the root directory to document these dependencies.
    *   **Recommendation:** Create a `requirements.txt` file in the project root listing all necessary packages to run the local simulation scripts. This ensures reproducibility and simplifies the setup process for new developers.

3.  **Type Hinting:**
    *   **Observation:** The codebase largely lacks Python type hints. Functions like `calculate_financials` in `project_metrics.py` take arguments like `rows` and return `metrics`, but the expected types (e.g., `List[List[str]]`, `Dict[str, float]`) are not explicit.
    *   **Recommendation:** Add type hints to all function signatures and complex variable declarations. This will improve code readability, serve as inline documentation, and enable the use of static analysis tools (like `mypy`) to catch potential type-related errors early.
