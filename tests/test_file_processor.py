"""
Tests for the FileProcessor utility.
"""
import os
import json
import tempfile
import pytest
from utils.file_processor import FileProcessor


class TestFileProcessor:
    """Test suite for FileProcessor class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.processor = FileProcessor()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def teardown_method(self):
        """Clean up after each test."""
        self.temp_dir.cleanup()
    
    def create_temp_file(self, content, extension):
        """Helper to create temporary test files."""
        file_path = os.path.join(self.temp_dir.name, f"test_file{extension}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_process_nonexistent_file(self):
        """Test processing a file that doesn't exist."""
        quotes, error = self.processor.process_file("nonexistent_file.txt")
        assert quotes == []
        assert "no puedo encontrar ese archivo" in error
    
    def test_process_unsupported_format(self):
        """Test processing a file with unsupported format."""
        file_path = self.create_temp_file("test content", ".pdf")
        quotes, error = self.processor.process_file(file_path)
        assert quotes == []
        assert "Solo acepto .txt, .csv o .json" in error
    
    def test_parse_txt_valid(self):
        """Test parsing a valid .txt file."""
        content = "Quote 1\nQuote 2\nQuote 3"
        file_path = self.create_temp_file(content, ".txt")
        
        quotes = self.processor.parse_txt(file_path)
        assert quotes == ["Quote 1", "Quote 2", "Quote 3"]
    
    def test_parse_txt_with_empty_lines(self):
        """Test parsing a .txt file with empty lines."""
        content = "Quote 1\n\nQuote 2\n\n\nQuote 3"
        file_path = self.create_temp_file(content, ".txt")
        
        quotes = self.processor.parse_txt(file_path)
        assert quotes == ["Quote 1", "Quote 2", "Quote 3"]
    
    def test_parse_csv_valid(self):
        """Test parsing a valid .csv file with quote column."""
        content = "id,quote,author\n1,Quote 1,Author 1\n2,Quote 2,Author 2"
        file_path = self.create_temp_file(content, ".csv")
        
        quotes = self.processor.parse_csv(file_path)
        assert quotes == ["Quote 1", "Quote 2"]
    
    def test_parse_csv_missing_column(self):
        """Test parsing a .csv file without quote column."""
        content = "id,text,author\n1,Text 1,Author 1"
        file_path = self.create_temp_file(content, ".csv")
        
        with pytest.raises(ValueError) as excinfo:
            self.processor.parse_csv(file_path)
        assert "must contain a 'quote' column" in str(excinfo.value)
    
    def test_parse_json_valid_array(self):
        """Test parsing a valid JSON array."""
        content = json.dumps(["Quote 1", "Quote 2", "Quote 3"])
        file_path = self.create_temp_file(content, ".json")
        
        quotes = self.processor.parse_json(file_path)
        assert quotes == ["Quote 1", "Quote 2", "Quote 3"]
    
    def test_parse_json_not_array(self):
        """Test parsing a JSON file that's not an array."""
        content = json.dumps({"quotes": ["Quote 1", "Quote 2"]})
        file_path = self.create_temp_file(content, ".json")
        
        with pytest.raises(ValueError) as excinfo:
            self.processor.parse_json(file_path)
        assert "must contain an array of quotes" in str(excinfo.value)
    
    def test_parse_json_invalid_format(self):
        """Test parsing an invalid JSON file."""
        content = '{"quotes": ["Quote 1", "Quote 2]'  # Missing closing quote
        file_path = self.create_temp_file(content, ".json")
        
        with pytest.raises(ValueError) as excinfo:
            self.processor.parse_json(file_path)
        assert "Invalid JSON format" in str(excinfo.value)
    
    def test_validate_quotes(self):
        """Test quote validation."""
        quotes = ["", "   ", "Hi", "Valid quote", "  Another valid quote  "]
        valid_quotes = self.processor.validate_quotes(quotes)
        assert valid_quotes == ["Valid quote", "Another valid quote"]
    
    def test_process_file_integration(self):
        """Integration test for process_file method."""
        # Test TXT
        txt_content = "Quote 1\nQuote 2\nQuote 3"
        txt_path = self.create_temp_file(txt_content, ".txt")
        txt_quotes, txt_error = self.processor.process_file(txt_path)
        assert txt_quotes == ["Quote 1", "Quote 2", "Quote 3"]
        assert txt_error is None
        
        # Test CSV
        csv_content = "id,quote,author\n1,Quote 1,Author 1\n2,Quote 2,Author 2"
        csv_path = self.create_temp_file(csv_content, ".csv")
        csv_quotes, csv_error = self.processor.process_file(csv_path)
        assert csv_quotes == ["Quote 1", "Quote 2"]
        assert csv_error is None
        
        # Test JSON
        json_content = json.dumps(["Quote 1", "Quote 2", "Quote 3"])
        json_path = self.create_temp_file(json_content, ".json")
        json_quotes, json_error = self.processor.process_file(json_path)
        assert json_quotes == ["Quote 1", "Quote 2", "Quote 3"]
        assert json_error is None