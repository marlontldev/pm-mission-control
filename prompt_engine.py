from pydantic import BaseModel, Field, validator
from typing import List, Optional

class ExecutiveReportContext(BaseModel):
    """
    Defines the contract for the AI Prompt.
    Validates data types before generating text.
    """
    project_name: str
    cpi: float
    variance: float
    bleeding_items: List[str] = Field(default_factory=list)
    data_sources: List[str]
    
    # Simulation Data
    prev_action: Optional[str] = None
    prev_result: Optional[str] = None
    
    @validator('cpi')
    def validate_cpi(cls, v):
        if v is None: return 0.0
        return v

    def render(self) -> str:
        # 1. Format Lists
        sources_text = "\n".join(self.data_sources)
        bleeding_text = ", ".join(self.bleeding_items) if self.bleeding_items else "None"
        
        # 2. Dynamic Learning Block
        if self.prev_action:
            learning_block = f"""
            === 🛑 PREVIOUS ACTION AUDIT ===
            1. MANAGER ACTION: "{self.prev_action}"
            2. RESULT: {self.prev_result}
            """
        else:
            learning_block = "No history available (First Run)."

        # 3. Final Template
        return f"""
        You are a Senior Project Controller.
        
        --- DATA SOURCES AUDIT ---
        {sources_text}
        
        --- INPUT DATA ---
        Project: {self.project_name}
        Current CPI: {self.cpi}
        Variance: ${self.variance:,.2f}
        
        {learning_block}
        
        --- BLEEDING ITEMS ---
        {bleeding_text}
        
        --- OUTPUT FORMAT ---
        🚨 EXECUTIVE FLASH REPORT: {self.project_name}
        
        --- DATA INTEGRITY CHECK ---
        [List the lines from 'DATA SOURCES AUDIT' here]

        1. EFFECTIVENESS
        * **Action Source:** [Real User Input OR AI Simulation]
        * **Analysis:** [Critique the action]

        2. CURRENT STATUS
        * **Financials:** CPI {self.cpi}.
        * **Analysis:** [Brief comment]
        
        3. NEW STRATEGIC PLAN
        * **Corrective Action:** [Specific instruction].
        """