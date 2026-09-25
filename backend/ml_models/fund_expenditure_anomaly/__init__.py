"""
Phase 4.3 — Model 3: Fund & Expenditure Anomaly Detection Package
AI-Powered MPLADS Monitoring and Analytics Platform (MPLADS PS 190942)
"""

from .config import Model3Config
from .pipeline import run_fund_expenditure_pipeline

__all__ = ["Model3Config", "run_fund_expenditure_pipeline"]
