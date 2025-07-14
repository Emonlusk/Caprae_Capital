import logging
from dataclasses import dataclass
from typing import Dict, Any
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
from scipy.stats import zscore

logger = logging.getLogger(__name__)

@dataclass
class ScoreWeights:
    revenue: float = 0.30
    company_size: float = 0.20
    tech_stack: float = 0.20
    market_fit: float = 0.15
    growth_potential: float = 0.15

class PredictiveLeadScorer:
    def __init__(self):
        self.weights = ScoreWeights()
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self._initialize_baselines()

    def _initialize_baselines(self):
        """Initialize scoring baselines"""
        self.revenue_ranges = {
            "Under $1M": 20,
            "$1M-$10M": 40,
            "$10M-$50M": 60,
            "$50M-$100M": 80,
            "Over $100M": 100,
            "Unknown": 30
        }
        
        self.size_ranges = {
            "1-10": 20,
            "11-50": 40,
            "51-200": 60,
            "201-1000": 80,
            "1000+": 100,
            "Unknown": 30
        }

    def calculate_lead_score(self, company_data: Dict[str, Any]) -> float:
        """Calculate comprehensive lead score"""
        try:
            # 1. Revenue Score
            revenue_score = self._calculate_revenue_score(company_data.get('revenue_range', 'Unknown'))
            
            # 2. Company Size Score
            size_score = self._calculate_size_score(company_data.get('company_size', 'Unknown'))
            
            # 3. Technology Score
            tech_score = self._calculate_tech_score(company_data.get('technologies', []))
            
            # 4. Market Fit Score
            market_score = self._calculate_market_fit(
                company_data.get('business_type', 'Unknown'),
                company_data.get('target_market', 'Unknown')
            )
            
            # 5. Growth Potential Score
            growth_score = self._calculate_growth_potential(
                company_data.get('company_stage', 'Unknown'),
                company_data.get('industry', 'Unknown')
            )
            
            # Calculate weighted average
            final_score = (
                revenue_score * self.weights.revenue +
                size_score * self.weights.company_size +
                tech_score * self.weights.tech_stack +
                market_score * self.weights.market_fit +
                growth_score * self.weights.growth_potential
            )
            
            # Normalize to 0-100 range
            normalized_score = min(max(round(final_score), 0), 100)
            
            logger.info(f"Calculated lead score: {normalized_score}")
            return normalized_score
            
        except Exception as e:
            logger.error(f"Error calculating lead score: {str(e)}")
            return 50  # Default middle score

    def _calculate_revenue_score(self, revenue_range: str) -> float:
        """Score based on revenue range"""
        return self.revenue_ranges.get(revenue_range, 30)

    def _calculate_size_score(self, size_range: str) -> float:
        """Score based on company size"""
        return self.size_ranges.get(size_range, 30)

    def _calculate_tech_score(self, technologies: list) -> float:
        """Score based on technology stack"""
        if not technologies:
            return 30
            
        # Weight different technology types
        tech_weights = {
            'cloud': 1.2,
            'analytics': 1.1,
            'crm': 1.0,
            'other': 0.8
        }
        
        score = 0
        for tech in technologies:
            tech_type = self._categorize_technology(tech)
            score += tech_weights.get(tech_type, 0.8) * 20
            
        return min(score, 100)

    def _calculate_market_fit(self, business_type: str, target_market: str) -> float:
        """Score based on market fit"""
        # B2B companies get higher scores
        type_scores = {
            'B2B': 100,
            'Both': 80,
            'B2C': 60,
            'Unknown': 50
        }
        
        return type_scores.get(business_type, 50)

    def _calculate_growth_potential(self, stage: str, industry: str) -> float:
        """Score based on growth potential"""
        stage_scores = {
            'Startup': 90,
            'Growth': 100,
            'Enterprise': 70,
            'Unknown': 50
        }
        
        return stage_scores.get(stage, 50)

    def _categorize_technology(self, tech: str) -> str:
        """Categorize technology into types"""
        tech = tech.lower()
        if any(x in tech for x in ['aws', 'azure', 'gcp', 'cloud']):
            return 'cloud'
        elif any(x in tech for x in ['analytics', 'tableau', 'power bi']):
            return 'analytics'
        elif any(x in tech for x in ['salesforce', 'hubspot', 'crm']):
            return 'crm'
        return 'other'