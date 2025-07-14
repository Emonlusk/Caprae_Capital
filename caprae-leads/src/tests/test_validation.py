import unittest
from utils.validation import validate_email, deduplicate_leads

class TestValidation(unittest.TestCase):

    def test_validate_email(self):
        valid_email = "test@example.com"
        invalid_email = "test@.com"
        self.assertTrue(validate_email(valid_email))
        self.assertFalse(validate_email(invalid_email))

    def test_deduplicate_leads(self):
        leads = [
            {"name": "Company A", "email": "contact@companya.com"},
            {"name": "Company B", "email": "contact@companyb.com"},
            {"name": "Company A", "email": "contact@companya.com"},
        ]
        deduplicated_leads = deduplicate_leads(leads)
        self.assertEqual(len(deduplicated_leads), 2)

if __name__ == '__main__':
    unittest.main()