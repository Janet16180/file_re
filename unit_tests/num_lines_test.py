import os
import unittest
from file_re import file_re


class TestNumLines(unittest.TestCase):
    
    def setUp(self):
        self.test_file = os.path.join(os.path.dirname(__file__), 'resources', 'num_lines_test.txt')
        self.multiline_file = os.path.join(os.path.dirname(__file__), 'resources', 'multiline_test.txt')
    
    def test_search_with_num_lines_basic(self):
        # Test basic functionality with num_lines=2
        result = file_re.search(r'line \d+', self.test_file, num_lines=2)
        self.assertIsNotNone(result)
        self.assertEqual(result.group(0), 'line 7')  # Should find the last match
        
    def test_search_with_num_lines_spanning_multiple_lines(self):
        # Test pattern that spans multiple lines
        result = file_re.search(r'line 3.*\nline 4', self.test_file, num_lines=2)
        self.assertIsNotNone(result)
        self.assertEqual(result.group(0), 'line 3 with pattern\nline 4')
        
    def test_search_with_num_lines_zero(self):
        # Test with num_lines=0 should return None
        result = file_re.search(r'line \d+', self.test_file, num_lines=0)
        self.assertIsNone(result)
        
    def test_search_with_num_lines_larger_than_file(self):
        # Test with num_lines larger than file length
        result = file_re.search(r'line \d+', self.test_file, num_lines=100)
        self.assertIsNotNone(result)
        self.assertEqual(result.group(0), 'line 7')  # Should still find the last match
        
    def test_findall_with_num_lines_basic(self):
        # Test findall with num_lines
        results = file_re.findall(r'line \d+', self.test_file, num_lines=2)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
    def test_findall_with_num_lines_pattern_groups(self):
        # Test findall with capturing groups and num_lines
        results = file_re.findall(r'line (\d+)', self.test_file, num_lines=3)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
    def test_findall_with_num_lines_zero(self):
        # Test findall with num_lines=0 should return empty list
        results = file_re.findall(r'line \d+', self.test_file, num_lines=0)
        self.assertEqual(results, [])
        
    def test_multiline_pattern_with_num_lines(self):
        # Test with num_lines=4 should match the pattern spanning 4 lines
        result = file_re.search(r'start\nmiddle line \d+\nmiddle line \d+\nend', self.multiline_file, num_lines=4)
        self.assertIsNotNone(result)
        self.assertIn('start\nmiddle line 1\nmiddle line 2\nend', result.group(0))
            
    def test_num_lines_precedence_over_multiline(self):
        # Test that num_lines takes precedence over multiline flag
        result1 = file_re.search(r'line 3.*\nline 4', self.test_file, multiline=True)
        result2 = file_re.search(r'line 3.*\nline 4', self.test_file, multiline=True, num_lines=2)
        
        # Both should find the pattern, but num_lines should be used when specified
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)
        self.assertEqual(result1.group(0), result2.group(0))


if __name__ == '__main__':
    unittest.main()