from datetime import datetime, timedelta

def clean_currency(value_str):
    try: return float(str(value_str).replace('$', '').replace(',', '').strip())
    except: return 0.0

def parse_date(date_str):
    for fmt in ("%Y-%m-%d", "%b-%d", "%d-%b-%Y", "%Y-%m"):
        try: return datetime.strptime(date_str, fmt)
        except ValueError: pass
    return None

def get_active_projects(rows):
    projects = {}
    if not rows: return projects
    headers = rows[0]
    cols = {h: i for i, h in enumerate(headers)}
    
    try:
        idx_id = cols["Project ID"]
        idx_name = cols["Project Name"]
        idx_status = cols["Status"]
        idx_period = cols["Report Period"]
    except KeyError: return {}

    for r in rows[1:]:
        if r[idx_status].upper() == "ACTIVE":
            pid = r[idx_id]
            if pid not in projects or r[idx_period] > projects[pid]['latest_period']:
                projects[pid] = {'name': r[idx_name], 'latest_period': r[idx_period]}
    return projects

def calculate_ai_forecast(start_date_str, baseline_end_str, spi):
    """
    Calculates the AI Predicted End Date based on SPI.
    Formula: Predicted_Duration = Original_Duration / SPI
    """
    if spi <= 0: return "Unknown (SPI 0)"
    
    start_date = parse_date(start_date_str)
    base_end = parse_date(baseline_end_str)
    
    if not start_date or not base_end: return "Error (Bad Dates)"
    
    # 1. Calculate Original Duration
    original_duration = (base_end - start_date).days
    
    # 2. Calculate Forecast Duration (Inflation due to poor speed)
    # We clamp SPI at 0.5 to prevent absurd dates (e.g. year 2099)
    safe_spi = max(spi, 0.5) 
    forecast_duration = int(original_duration / safe_spi)
    
    # 3. New End Date
    ai_end_date = start_date + timedelta(days=forecast_duration)
    return ai_end_date.strftime("%Y-%m-%d")

def calculate_financials(rows, project_id, period):
    metrics = {"cpi": 0.0, "spi": 0.0, "bac": 0.0, "eac": 0.0, "variance": 0.0, "tcpi": 0.0, "root_causes": []}
    
    headers = rows[0]
    # Dynamic Mapping
    c = {h: i for i, h in enumerate(headers)}
    
    total_ev = 0
    total_ac = 0
    total_pv = 0

    for r in rows[1:]:
        if r[c["Project ID"]] == project_id and r[c["Report Period"]] == period:
            
            # Extract Values
            cat = r[c["Cost Category"]]
            ev = clean_currency(r[c["Earned Value (EV)"]])
            ac = clean_currency(r[c["Actual Cost (AC)"]])
            # NEW: Handle Missing PV Column safely
            pv = clean_currency(r[c["Planned Value (PV)"]]) if "Planned Value (PV)" in c else ev 

            # Root Cause Detection
            try:
                # Calculate row-level CPI
                row_cpi = ev / ac if ac > 0 else 0
                if row_cpi < 0.95 and "TOTAL" not in cat.upper():
                    metrics["root_causes"].append(f"{cat} (CPI: {row_cpi:.2f})")
            except: pass

            # Aggregate Totals
            if "TOTAL PROJECT" in cat.upper():
                metrics["bac"] = clean_currency(r[c["Budget (BAC)"]])
                total_ev = ev
                total_ac = ac
                total_pv = pv

    # Final Calculations
    if total_ac > 0: metrics["cpi"] = round(total_ev / total_ac, 2)
    if total_pv > 0: metrics["spi"] = round(total_ev / total_pv, 2) # NEW: SPI Calculation
    
    if metrics["cpi"] > 0:
        metrics["eac"] = metrics["bac"] / metrics["cpi"]
        metrics["variance"] = metrics["eac"] - metrics["bac"]
        
        rem_budget = metrics["bac"] - total_ac
        rem_work = metrics["bac"] - total_ev
        metrics["tcpi"] = (rem_work / rem_budget) if rem_budget != 0 else 9.99

    return metrics