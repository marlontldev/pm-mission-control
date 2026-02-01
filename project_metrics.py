from datetime import datetime

def clean_currency(value_str):
    try: return float(str(value_str).replace('$', '').replace(',', '').strip())
    except: return 0.0

def get_active_projects(rows):
    """
    Scans the budget sheet to find unique Active projects and their LATEST period.
    """
    projects = {}
    if not rows: return projects
    
    headers = rows[0]
    try:
        idx_id = headers.index("Project ID")
        idx_name = headers.index("Project Name")
        idx_status = headers.index("Status")
        idx_period = headers.index("Report Period")
    except ValueError:
        return {} 

    for r in rows[1:]:
        pid = r[idx_id]
        status = r[idx_status]
        period = r[idx_period]
        
        if status.upper() == "ACTIVE":
            if pid not in projects:
                projects[pid] = {'name': r[idx_name], 'latest_period': period}
            else:
                if period > projects[pid]['latest_period']:
                    projects[pid]['latest_period'] = period
                    
    return projects

def get_project_lifecycle(rows, project_id):
    """
    Extracts the FULL history of CPIs for a project, sorted by date.
    Returns: A list of dicts [{'period': '2026-01', 'cpi': 1.0}, ...]
    """
    history = []
    headers = rows[0]
    idx_id = headers.index("Project ID")
    idx_period = headers.index("Report Period")
    idx_cat = headers.index("Cost Category")
    idx_cpi = headers.index("CPI (EV/AC)")

    for r in rows[1:]:
        # We only care about the "TOTAL PROJECT" row for the high-level trend
        if r[idx_id] == project_id and "TOTAL PROJECT" in r[idx_cat].upper():
            try:
                history.append({
                    'period': r[idx_period],
                    'cpi': float(r[idx_cpi])
                })
            except: pass
            
    # Sort by period to ensure time order (Jan -> Feb -> Mar)
    history.sort(key=lambda x: x['period'])
    return history

def calculate_financials(rows, project_id, period):
    # (Same function as before, calculating specific metrics for ONE period)
    metrics = {"cpi": 0.0, "bac": 0.0, "eac": 0.0, "variance": 0.0, "tcpi": 0.0, "root_causes": []}
    
    headers = rows[0]
    idx_id, idx_period, idx_cat, idx_bac, idx_ev, idx_ac, idx_cpi = [
        headers.index(col) for col in ["Project ID", "Report Period", "Cost Category", "Budget (BAC)", "Earned Value (EV)", "Actual Cost (AC)", "CPI (EV/AC)"]
    ]
    
    total_ev = 0
    total_ac = 0

    for r in rows[1:]:
        if r[idx_id] == project_id and r[idx_period] == period:
            try:
                val = float(r[idx_cpi])
                if val < 0.95 and "TOTAL PROJECT" not in r[idx_cat].upper():
                    metrics["root_causes"].append(f"{r[idx_cat]} (CPI: {val})")
            except: pass

            if "TOTAL PROJECT" in r[idx_cat].upper():
                metrics["cpi"] = float(r[idx_cpi])
                metrics["bac"] = clean_currency(r[idx_bac])
                total_ev = clean_currency(r[idx_ev])
                total_ac = clean_currency(r[idx_ac])

    if metrics["cpi"] > 0:
        metrics["eac"] = metrics["bac"] / metrics["cpi"]
        metrics["variance"] = metrics["eac"] - metrics["bac"]
        rem_budget = metrics["bac"] - total_ac
        rem_work = metrics["bac"] - total_ev
        metrics["tcpi"] = (rem_work / rem_budget) if rem_budget != 0 else 9.99

    return metrics