import os
import json
from datetime import datetime
from typing import Dict, Optional

# Approximate cost per request for different Hugging Face models
# These are estimated costs - actual costs may vary based on Hugging Face pricing
MODEL_COSTS = {
    "gpt2": {
        "request": 0.0001,  # Estimated cost per request
        "token": 0.00001    # Estimated cost per token
    },
    "mistralai/Mistral-7B-Instruct-v0.2": {
        "request": 0.0005,  # Estimated cost per request
        "token": 0.00005    # Estimated cost per token
    }
}

class CostTracker:
    def __init__(self, budget_limit: float = 50.0, log_file: str = "api_usage.json"):
        self.budget_limit = budget_limit
        self.log_file = log_file
        self.usage_log = self._load_usage_log()
        
    def _load_usage_log(self) -> Dict:
        """Load existing usage log or create a new one."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading log file. Creating new log.")
        
        # Initialize with empty structure
        return {
            "monthly_usage": {},
            "total_cost": 0.0,
            "total_requests": 0,
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_usage_log(self):
        """Save the usage log to file."""
        with open(self.log_file, 'w') as f:
            json.dump(self.usage_log, f, indent=2)
    
    def track_request(self, model: str, output_tokens: int, purpose: Optional[str] = None):
        """Track the cost of a Hugging Face API request."""
        # Calculate cost
        if model not in MODEL_COSTS:
            print(f"Unknown model: {model}. Cannot track cost.")
            return
        
        # For Hugging Face, we estimate based on request and token count
        request_cost = MODEL_COSTS[model]["request"]
        token_cost = output_tokens * MODEL_COSTS[model]["token"]
        total_cost = request_cost + token_cost
        
        # Get current month
        current_month = datetime.now().strftime("%Y-%m")
        
        # Update monthly usage
        if current_month not in self.usage_log["monthly_usage"]:
            self.usage_log["monthly_usage"][current_month] = {
                "cost": 0.0,
                "requests": 0,
                "tokens": {
                    "output": 0
                }
            }
        
        monthly_data = self.usage_log["monthly_usage"][current_month]
        monthly_data["cost"] += total_cost
        monthly_data["requests"] += 1
        monthly_data["tokens"]["output"] += output_tokens
        
        # Update totals
        self.usage_log["total_cost"] += total_cost
        self.usage_log["total_requests"] += 1
        self.usage_log["last_updated"] = datetime.now().isoformat()
        
        # Save to file
        self._save_usage_log()
        
        # Check budget limit
        if monthly_data["cost"] > self.budget_limit:
            print(f"WARNING: Monthly budget limit of ${self.budget_limit:.2f} exceeded!")
            return False
        
        return True
    
    def get_monthly_usage(self, month: Optional[str] = None) -> Dict:
        """Get usage statistics for a specific month or current month."""
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        
        if month in self.usage_log["monthly_usage"]:
            return self.usage_log["monthly_usage"][month]
        else:
            return {"cost": 0.0, "requests": 0, "tokens": {"input": 0, "output": 0}}
    
    def get_remaining_budget(self) -> float:
        """Get remaining budget for the current month."""
        current_month = datetime.now().strftime("%Y-%m")
        monthly_usage = self.get_monthly_usage(current_month)
        return max(0, self.budget_limit - monthly_usage["cost"])
    
    def print_usage_report(self):
        """Print a summary of API usage."""
        current_month = datetime.now().strftime("%Y-%m")
        monthly_usage = self.get_monthly_usage(current_month)
        
        print("\n===== API Usage Report =====")
        print(f"Current Month: {current_month}")
        print(f"Requests: {monthly_usage['requests']}")
        print(f"Cost: ${monthly_usage['cost']:.2f}")
        print(f"Budget Remaining: ${self.get_remaining_budget():.2f}")
        print(f"Output Tokens: {monthly_usage['tokens']['output']}")
        print("============================\n") 