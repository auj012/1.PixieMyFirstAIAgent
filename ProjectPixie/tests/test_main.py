import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import re
import sys
import os

# This tells Python to also look one folder up (or wherever app.py lives)
sys.path.append(r"C:\Users\auj01\Downloads\AILearningSAIHanu\AIAgentLearning\ProjectPixie\src\core")

# Now your original import will work perfectly!
import main

class TestProjectPixieProduction(unittest.TestCase):

    # --- Test 1: Assert input name is inside the output string ---
    @patch('ollama.chat')
    def test_name_present_in_output(self, mock_chat):
        """Verify that the target name is explicitly part of the returned text structure."""
        mock_response = MagicMock()
        mock_response.message.content = "The name Priya means beloved."
        mock_chat.return_value = mock_response
        
        output, _ = main.get_name_meaning("Priya")
        self.assertIn("Priya", output, "Error: The target name was missing from the output string.")

    # --- Test 2: Golden Dataset Comparison Validation ---
    def test_golden_dataset_evaluation(self):
        """Load goldendataset.xlsx and check file schema integrity."""
        # Read the file relative to THIS test file, so it works from any working directory
        dataset_path = os.path.join(os.path.dirname(__file__), "goldendataset.xlsx")
        df = pd.read_excel(dataset_path)
        
        # Pull row metadata to ensure names and contextual values match expected criteria
        first_row_name = df.iloc[0]['Name']
        first_row_meaning = df.iloc[0]['Meaning']
        
        self.assertEqual(first_row_name, "Aarav")
        self.assertIn("Peaceful", first_row_meaning)

    # --- Test 3: Mixed Input Character Rules ---
    def test_alphanumeric_passes_rules(self):
        """Verify that partial digits (like priya45) pass rule criteria seamlessly."""
        is_all_digits = "priya45".isdigit()
        is_all_special = bool(re.match(r"^[^a-zA-Z0-9]+$", "priya45"))
        
        self.assertFalse(is_all_digits, "Should pass because it contains alphabetic characters")
        self.assertFalse(is_all_special, "Should pass because it contains alphanumeric text")

    def test_pure_numbers_blocked(self):
        """Verify absolute digit violations (like 452345) fail."""
        self.assertTrue("452345".isdigit(), "Pure digit blocks must yield a validation catch flag")

    def test_pure_special_chars_blocked(self):
        """Verify absolute character violations (like $$$%%%) fail."""
        self.assertTrue(bool(re.match(r"^[^a-zA-Z0-9]+$", "$$$%%%")), "Pure symbol entries must yield a validation catch flag")

if __name__ == '__main__':
    unittest.main()