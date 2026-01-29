def clean_currency(value_str):
    try: return float(str(value_str).replace('$', '').replace(',', '').strip())
    except: return 0.0

def get_active_projects(rows):
    """
    Scans the budget sheet to find unique Active projects and their LATEST period.
    Returns: Dict {'PROJ-001': {'name': 'Alpha Tower', 'latest_period': '2026-02'}}
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
        return {} # Missing columns

    for r in rows[1:]:
        pid = r[idx_id]
        status = r[idx_status]
        period = r[idx_period]
        
        if status.upper() == "ACTIVE":
            if pid not in projects:
                projects[pid] = {'name': r[idx_name], 'latest_period': period}
            else:
                # Update if we find a newer period (Simple string comparison works for YYYY-MM)
                if period > projects[pid]['latest_period']:
                    projects[pid]['latest_period'] = period
                    
    return projects

def calculate_financials(rows, project_id, period):
    """
    Calculates metrics for a SPECIFIC Project ID in a SPECIFIC Period.
    """
    metrics = {"cpi": 0.0, "bac": 0.0, "eac": 0.0, "variance": 0.0, "tcpi": 0.0, "root_causes": []}
    
    headers = rows[0]
    idx_id = headers.index("Project ID")
    idx_period = headers.index("Report Period")
    idx_cat = headers.index("Cost Category")
    idx_bac = headers.index("Budget (BAC)")
    idx_ev = headers.index("Earned Value (EV)")
    idx_ac = headers.index("Actual Cost (AC)")
    idx_cpi = headers.index("CPI (EV/AC)")

    total_ev = 0
    total_ac = 0

    for r in rows[1:]:
        # FILTER: Must match BOTH Project ID and the Period
        if r[idx_id] == project_id and r[idx_period] == period:
            
            # Root Cause Logic
            try:
                val = float(r[idx_cpi])
                if val < 0.95 and "TOTAL PROJECT" not in r[idx_cat].upper():
                    metrics["root_causes"].append(f"{r[idx_cat]} (CPI: {val})")
            except: pass

            # Totals
            if "TOTAL PROJECT" in r[idx_cat].upper():
                metrics["cpi"] = float(r[idx_cpi])
                metrics["bac"] = clean_currency(r[idx_bac])
                total_ev = clean_currency(r[idx_ev])
                total_ac = clean_currency(r[idx_ac])

    # Advanced Calculations
    if metrics["cpi"] > 0:
        metrics["eac"] = metrics["bac"] / metrics["cpi"]
        metrics["variance"] = metrics["eac"] - metrics["bac"]
        
        rem_budget = metrics["bac"] - total_ac
        rem_work = metrics["bac"] - total_ev
        metrics["tcpi"] = (rem_work / rem_budget) if rem_budget != 0 else 9.99

    return metrics