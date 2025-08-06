import pytest
from pathlib import Path
from file_re import file_re
import tempfile
import os
ROOT = Path(__file__).parent


class TestNumLinesFeature:
    def test_basic_num_lines_functionality(self):
        """Test basic num_lines functionality with hi\\nword pattern"""
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(r"hi\nword", test_file, num_lines=2)

        assert match is not None
        assert match.group(0) == "hi\nword"
        
    def test_longest_possible_match(self):
        """Test that num_lines finds the longest possible match"""
        # Test the example from the requirement
        test_file = Path(ROOT, "resources", "multiline_test_1.txt")

        match = file_re.search(r"(hi\n)+", test_file, num_lines=3)

        assert match is not None
        # Should match the last sequence of hi's (3 of them)
        expected = "hi\nhi\nhi\n"
        assert match.group(0) == expected
    
    def test_num_lines_with_groups(self):
        """Test num_lines with capturing groups"""
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(r"(hi)\n(word)", test_file, num_lines=2)

        assert match is not None
        assert match.group(0) == "hi\nword"
        assert match.group(1) == "hi"
        assert match.group(2) == "word"
    
    def test_num_lines_with_named_groups(self):
        """Test num_lines with named capturing groups"""
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(r"(?P<greeting>hi)\n(?P<noun>word)", test_file, num_lines=2)
        
        assert match is not None
        assert match.group(0) == "hi\nword"
        assert match.group("greeting") == "hi"
        assert match.group("noun") == "word"
        assert match.groupdict() == {"greeting": "hi", "noun": "word"}
    
    def test_num_lines_no_match(self):
        """Test num_lines when no match is found"""
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(r"nonexistent\npattern", test_file, num_lines=2)
        
        assert match is None
    
    def test_num_lines_larger_than_file(self):
        """Test num_lines when num_lines is larger than file line count"""
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(r"hi\nword", test_file, num_lines=10)
        
        assert match is not None
        assert match.group(0) == "hi\nword"
    
    def test_num_lines_equals_one(self):
        """Test num_lines=1 (should work like single line mode)"""
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        
        match = file_re.search(r"some", test_file, num_lines=1)
        assert match is not None
        assert match.group(0) == "some"
        
        # Should not match across lines with num_lines=1
        match = file_re.search(r"text\nhi", test_file, num_lines=1)
        assert match is None
    
    def test_num_lines_validation(self):
        """Test parameter validation for num_lines"""
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        # Test num_lines <= 0
        with pytest.raises(ValueError, match="num_lines must be greater than 0"):
            file_re.search(r"test", test_file, num_lines=0)
        
        with pytest.raises(ValueError, match="num_lines must be greater than 0"):
            file_re.search(r"test", test_file, num_lines=-1)
        
        # Test conflicting parameters
        with pytest.raises(ValueError, match="Cannot use both multiline=True and num_lines"):
            file_re.search(r"test", test_file, multiline=True, num_lines=2)
    
    def test_findall_num_lines(self):
        """Test findall with num_lines"""
        test_file = Path(ROOT, "resources", "multiline_test_3.txt")
        
        matches = file_re.findall(r"hi\nworld", test_file, num_lines=2)
        
        # Should find the occurrence
        assert len(matches) >= 1  # At least one match due to sliding window
        assert "hi\nworld" in matches
    
    def test_findall_num_lines_with_groups(self):
        """Test findall with num_lines and capturing groups"""
        test_file = Path(ROOT, "resources", "multiline_test_3.txt")
        
        matches = file_re.findall(r"(hi)\n(world)", test_file, num_lines=2)
        
        # Should find matches with groups
        assert len(matches) >= 1
        # Check that we get tuples for multiple groups
        if matches:
            assert isinstance(matches[0], tuple)
            assert len(matches[0]) == 2
    
    def test_num_lines_position_tracking(self):
        """Test that positions are correctly calculated with num_lines"""
        test_file = Path(ROOT, "resources", "multiline_test_2.txt")
        match = file_re.search(r"hi\nword", test_file, num_lines=2)
        
        assert match is not None
        start_pos = match.start()
        end_pos = match.end()
        
        # Verify positions make sense
        assert start_pos >= 0
        assert end_pos > start_pos
        assert (end_pos - start_pos) == len("hi\nword")
    
    def test_num_lines_compressed_files(self):
        """Test num_lines with compressed files"""
        # This would require creating compressed test files
        # For now, we'll skip this test but it should be implemented
        # when compressed file support is needed
        pytest.skip("Compressed file testing not implemented yet")