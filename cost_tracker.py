"""
Cost tracking module for Hugging Face API usage.

This module provides functionality to track and manage API usage costs,
ensuring that the application stays within budget constraints.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any

# Configure logging
logger = logging.getLogger('cost_tracker')

# Cost constants for different Hugging Face models
# These are estimated costs - actual costs may vary based on Hugging Face pricing
MODEL_COSTS = {
    "gpt2": {
        "request": 0.0001,  # Cost per request in USD
        "token": 0.00001    # Cost per output token in USD
    },
    "mistralai/Mistral-7B-Instruct-v0.2": {
        "request": 0.0005,  # Cost per request in USD
        "token": 0.00005    # Cost per output token in USD
    }
}

class CostTracker:
    """Tracks and manages API usage costs for Hugging Face API calls."""
    
    def __init__(self, budget_limit: float = 50.0, log_file: str = "api_usage.json"):
        """
        Initialize the cost tracker with budget and logging settings.
        
        Args:
            budget_limit: Maximum monthly budget in USD
            log_file: Path to the JSON file for storing usage data
        """
        self.budget_limit = budget_limit
        self.log_file = log_file
        self.usage_log = self._load_usage_log()
        
    def _load_usage_log(self) -> Dict[str, Any]:
        """
        Load existing usage log or create a new one if it doesn't exist.
        
        Returns:
            Dictionary containing usage log data
        """
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                logger.warning(f"Error reading log file {self.log_file}. Creating new log.")
        
        # Return a new log structure if file doesn't exist or is invalid
        return self._create_new_log()
    
    def _create_new_log(self) -> Dict[str, Any]:
        """
        Create a new usage log structure.
        
        Returns:
            Dictionary with initialized usage log structure
        """
        return {
            "monthly_usage": {},
            "total_cost": 0.0,
            "total_requests": 0,
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_usage_log(self) -> None:
        """
        Save the current usage log to the log file.
        """
        try:
            with open(self.log_file, 'w') as file:
                json.dump(self.usage_log, file, indent=2)
        except IOError as error:
            logger.error(f"Failed to save usage log: {error}")
    
    def track_request(self, model: str, output_tokens: int, purpose: Optional[str] = None) -> bool:
        """
        Track the cost of a Hugging Face API request.
        
        Args:
            model: The Hugging Face model identifier
            output_tokens: Number of tokens in the generated output
            purpose: Optional description of what the request was for
            
        Returns:
            True if within budget, False if budget exceeded
        """
        if not self._is_valid_model(model):
            return True  # Return True to avoid blocking execution
        
        total_cost = self._calculate_request_cost(model, output_tokens)
        current_month = self._get_current_month_key()
        
        self._ensure_month_exists(current_month)
        self._update_usage_data(current_month, total_cost, output_tokens, purpose)
        self._save_usage_log()
        
        return self._check_budget_limit(current_month)
    
    def _is_valid_model(self, model: str) -> bool:
        """
        Check if the model is recognized for cost tracking.
        
        Args:
            model: The model identifier to check
            
        Returns:
            True if model is valid, False otherwise
        """
        if model not in MODEL_COSTS:
            logger.warning(f"Unknown model: {model}. Cannot track cost.")
            return False
        return True
    
    def _calculate_request_cost(self, model: str, output_tokens: int) -> float:
        """
        Calculate the total cost for a single API request.
        
        Args:
            model: The Hugging Face model identifier
            output_tokens: Number of tokens in the generated output
            
        Returns:
            Total cost in USD
        """
        request_cost = MODEL_COSTS[model]["request"]
        token_cost = output_tokens * MODEL_COSTS[model]["token"]
        return request_cost + token_cost
    
    def _get_current_month_key(self) -> str:
        """
        Get the current month in YYYY-MM format for usage tracking.
        
        Returns:
            String representing current month (YYYY-MM)
        """
        return datetime.now().strftime("%Y-%m")
    
    def _ensure_month_exists(self, month_key: str) -> None:
        """
        Ensure the month entry exists in the usage log.
        
        Args:
            month_key: Month key in YYYY-MM format
        """
        if month_key not in self.usage_log["monthly_usage"]:
            self.usage_log["monthly_usage"][month_key] = {
                "cost": 0.0,
                "requests": 0,
                "tokens": {
                    "output": 0
                }
            }
    
    def _update_usage_data(self, month_key: str, cost: float, 
                           output_tokens: int, purpose: Optional[str]) -> None:
        """
        Update usage statistics with new request data.
        
        Args:
            month_key: Month key in YYYY-MM format
            cost: Total cost of the request
            output_tokens: Number of tokens in the generated output
            purpose: Optional description of what the request was for
        """
        # Update monthly data
        monthly_data = self.usage_log["monthly_usage"][month_key]
        monthly_data["cost"] += cost
        monthly_data["requests"] += 1
        monthly_data["tokens"]["output"] += output_tokens
        
        # Update totals
        self.usage_log["total_cost"] += cost
        self.usage_log["total_requests"] += 1
        self.usage_log["last_updated"] = datetime.now().isoformat()
        
        # Add purpose if provided
        if purpose:
            if "purposes" not in monthly_data:
                monthly_data["purposes"] = {}
            if purpose not in monthly_data["purposes"]:
                monthly_data["purposes"][purpose] = 0
            monthly_data["purposes"][purpose] += 1
    
    def _check_budget_limit(self, month_key: str) -> bool:
        """
        Check if the current month's usage exceeds the budget limit.
        
        Args:
            month_key: Month key in YYYY-MM format
            
        Returns:
            True if within budget, False if exceeded
        """
        monthly_cost = self.usage_log["monthly_usage"][month_key]["cost"]
        if monthly_cost > self.budget_limit:
            logger.warning(
                f"Monthly budget limit of ${self.budget_limit:.2f} exceeded! "
                f"Current usage: ${monthly_cost:.2f}"
            )
            return False
        return True
    
    def get_monthly_usage(self, month: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for a specific month or current month.
        
        Args:
            month: Month in YYYY-MM format, or None for current month
            
        Returns:
            Dictionary containing usage statistics for the month
        """
        month_key = month if month else self._get_current_month_key()
        
        if month_key in self.usage_log["monthly_usage"]:
            return self.usage_log["monthly_usage"][month_key]
        
        # Return empty stats if no data for the month
        return self._create_empty_month_stats()
    
    def _create_empty_month_stats(self) -> Dict[str, Any]:
        """
        Create empty statistics for a month with no data.
        
        Returns:
            Dictionary with zero values for all statistics
        """
        return {
            "cost": 0.0, 
            "requests": 0, 
            "tokens": {"output": 0}
        }
    
    def get_remaining_budget(self) -> float:
        """
        Calculate remaining budget for the current month.
        
        Returns:
            Remaining budget in USD (never negative)
        """
        current_month = self._get_current_month_key()
        monthly_usage = self.get_monthly_usage(current_month)
        return max(0.0, self.budget_limit - monthly_usage["cost"])
    
    def print_usage_report(self) -> None:
        """
        Print a summary of API usage and costs for the current month.
        """
        current_month = self._get_current_month_key()
        monthly_usage = self.get_monthly_usage(current_month)
        remaining_budget = self.get_remaining_budget()
        
        # Format the report
        report = self._format_usage_report(current_month, monthly_usage, remaining_budget)
        
        # Print the report
        print(report)
        logger.info(f"Usage report generated for {current_month}")
    
    def _format_usage_report(self, month: str, usage: Dict[str, Any], 
                             remaining: float) -> str:
        """
        Format the usage report as a string.
        
        Args:
            month: Month in YYYY-MM format
            usage: Usage statistics dictionary
            remaining: Remaining budget in USD
            
        Returns:
            Formatted report string
        """
        report_lines = [
            "\n===== API Usage Report =====",
            f"Current Month: {month}",
            f"Requests: {usage['requests']}",
            f"Cost: ${usage['cost']:.2f}",
            f"Budget Remaining: ${remaining:.2f}",
            f"Output Tokens: {usage['tokens']['output']}",
            "============================\n"
        ]
        
        return "\n".join(report_lines)