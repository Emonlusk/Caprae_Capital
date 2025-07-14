import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_mock_leads(n_samples=100):
    """Generate mock lead data"""
    industries = ['SaaS', 'Fintech', 'Healthcare', 'E-commerce', 'Manufacturing']
    tech_stacks = [['aws', 'salesforce'], ['azure', 'hubspot'], ['gcp', 'zendesk'],
                   ['aws', 'marketo'], ['azure', 'jira']]
    
    data = {
        'company_name': [f"Company_{i}" for i in range(n_samples)],
        'industry': np.random.choice(industries, n_samples),
        'revenue': np.random.randint(100000, 10000000, n_samples),
        'employees': np.random.randint(10, 1000, n_samples),
        'tech_stack': [str(np.random.choice(tech_stacks)) for _ in range(n_samples)],
        'growth_signals': np.random.randint(1, 100, n_samples),
        'last_updated': [(datetime.now() - timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d') 
                        for _ in range(n_samples)]
    }
    
    df = pd.DataFrame(data)
    
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(__file__))
    os.makedirs(data_dir, exist_ok=True)
    
    # Save to CSV
    output_path = os.path.join(data_dir, 'leads.csv')
    df.to_csv(output_path, index=False)
    print(f"Generated mock data saved to {output_path}")
    return df

if __name__ == "__main__":
    generate_mock_leads()