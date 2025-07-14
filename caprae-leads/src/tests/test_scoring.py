import unittest
from utils.scoring import calculate_score

class TestScoring(unittest.TestCase):

    def test_calculate_score(self):
        # Test case 1: High revenue, many employees, strong growth signals
        company_data = {
            'revenue': 1000000,
            'employees': 200,
            'tech_stack': ['AWS', 'CRM'],
            'growth_signals': 5
        }
        expected_score = 80  # Example expected score based on the weighted algorithm
        self.assertEqual(calculate_score(company_data), expected_score)

        # Test case 2: Low revenue, few employees, weak growth signals
        company_data = {
            'revenue': 10000,
            'employees': 5,
            'tech_stack': ['None'],
            'growth_signals': 1
        }
        expected_score = 20  # Example expected score based on the weighted algorithm
        self.assertEqual(calculate_score(company_data), expected_score)

        # Test case 3: Medium revenue, average employees, moderate growth signals
        company_data = {
            'revenue': 500000,
            'employees': 50,
            'tech_stack': ['Azure'],
            'growth_signals': 3
        }
        expected_score = 50  # Example expected score based on the weighted algorithm
        self.assertEqual(calculate_score(company_data), expected_score)

if __name__ == '__main__':
    unittest.main()