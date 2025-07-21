"""
File processor utility for handling quote uploads in different formats.
Supports .txt, .csv, and .json formats for quote extraction.
"""
import os
import json
import pandas as pd
from typing import List, Optional, Tuple


class FileProcessor:
    """
    Processes uploaded files for quote extraction.
    Supports .txt, .csv, and .json formats.
    """
    
    def __init__(self, theme_engine=None):
        """
        Initialize the FileProcessor.
        
        Args:
            theme_engine: Optional theme engine for mafia-themed error messages
        """
        self.theme_engine = theme_engine
    
    def process_file(self, file_path: str) -> Tuple[List[str], Optional[str]]:
        """
        Process a file and extract quotes based on file format.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Tuple containing:
                - List of extracted quotes
                - Error message if any, None otherwise
        """
        if not os.path.exists(file_path):
            error_msg = self._get_error_message("file_not_found")
            return [], error_msg
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.txt':
                return self.parse_txt(file_path), None
            elif file_ext == '.csv':
                return self.parse_csv(file_path), None
            elif file_ext == '.json':
                return self.parse_json(file_path), None
            else:
                error_msg = self._get_error_message("unsupported_format")
                return [], error_msg
        except Exception as e:
            error_msg = self._get_error_message("processing_error", str(e))
            return [], error_msg
    
    def parse_txt(self, file_path: str) -> List[str]:
        """
        Parse a .txt file, treating each line as a separate quote.
        
        Args:
            file_path: Path to the .txt file
            
        Returns:
            List of quotes extracted from the file
        """
        quotes = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:  # Skip empty lines
                    quotes.append(line)
        
        return self.validate_quotes(quotes)
    
    def parse_csv(self, file_path: str) -> List[str]:
        """
        Parse a .csv file, extracting quotes from the 'quote' column.
        
        Args:
            file_path: Path to the .csv file
            
        Returns:
            List of quotes extracted from the file
        """
        try:
            df = pd.read_csv(file_path)
            
            # Check if 'quote' column exists
            if 'quote' not in df.columns:
                raise ValueError("CSV file must contain a 'quote' column")
            
            # Extract quotes from the 'quote' column
            quotes = df['quote'].dropna().tolist()
            return self.validate_quotes(quotes)
            
        except Exception as e:
            raise ValueError(f"Error parsing CSV file: {str(e)}")
    
    def parse_json(self, file_path: str) -> List[str]:
        """
        Parse a .json file, extracting quotes from a JSON array.
        
        Args:
            file_path: Path to the .json file
            
        Returns:
            List of quotes extracted from the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Check if data is a list
            if not isinstance(data, list):
                raise ValueError("JSON file must contain an array of quotes")
            
            # Extract quotes from the JSON array
            quotes = [str(quote) for quote in data if quote]
            return self.validate_quotes(quotes)
            
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")
        except Exception as e:
            raise ValueError(f"Error parsing JSON file: {str(e)}")
    
    def validate_quotes(self, quotes: List[str]) -> List[str]:
        """
        Validate quotes and filter out invalid ones.
        
        Args:
            quotes: List of quotes to validate
            
        Returns:
            List of valid quotes
        """
        valid_quotes = []
        for quote in quotes:
            # Skip empty quotes
            if not quote or not quote.strip():
                continue
                
            # Trim whitespace
            quote = quote.strip()
            
            # Skip quotes that are too short (less than 5 characters)
            if len(quote) < 5:
                continue
                
            valid_quotes.append(quote)
        
        return valid_quotes
    
    def _get_error_message(self, error_type: str, details: str = "") -> str:
        """
        Get a mafia-themed error message based on the error type.
        
        Args:
            error_type: Type of error
            details: Additional error details
            
        Returns:
            Mafia-themed error message
        """
        if self.theme_engine:
            # If theme engine is available, use it to generate the message
            return self.theme_engine.get_error_message(error_type, details)
        
        # Default mafia-themed error messages
        error_messages = {
            "file_not_found": "Capo, no puedo encontrar ese archivo. ¿Estás seguro de que existe?",
            "unsupported_format": "Ese formato no es de la familia, capo. Solo acepto .txt, .csv o .json.",
            "processing_error": f"Hubo un problema procesando el archivo, capo. {details}",
            "empty_file": "El archivo está vacío, capo. Necesito frases para motivar a la familia."
        }
        
        return error_messages.get(error_type, f"Error desconocido: {details}")