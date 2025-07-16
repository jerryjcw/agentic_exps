"""
Markdown Table to DOCX Converter

This module provides functionality to detect markdown tables in text files
and convert them to a visually formatted DOCX document.
"""

import re
from typing import List, Tuple, Optional
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn
import argparse
import sys
import os


class MarkdownTableConverter:
    """Converts markdown tables from text files to DOCX format."""
    
    def __init__(self, max_column_width: int = 40):
        """
        Initialize the converter.
        
        Args:
            max_column_width: Maximum characters per column (default: 40)
        """
        self.max_column_width = max_column_width
    
    def detect_markdown_tables(self, text: str) -> List[Tuple[int, List[str]]]:
        """
        Detect markdown tables in text using simple line-based detection.
        
        Args:
            text: Input text to scan for tables
            
        Returns:
            List of tuples containing (start_line_number, table_lines)
        """
        lines = text.split('\n')
        tables = []
        current_table = []
        table_start_line = None
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Check if line starts with '|' (markdown table row)
            if stripped_line.startswith('|') and stripped_line.endswith('|'):
                if current_table == []:
                    table_start_line = i + 1  # 1-based line numbering
                current_table.append(stripped_line)
            else:
                # End of table or not a table line
                if current_table:
                    # Filter out separator lines (lines with only |, -, :, and spaces)
                    table_rows = []
                    for row in current_table:
                        if not re.match(r'^[\|\-\:\s]+$', row):
                            table_rows.append(row)
                    
                    if table_rows:  # Only add if there are actual data rows
                        tables.append((table_start_line, table_rows))
                    current_table = []
                    table_start_line = None
        
        # Handle table at end of file
        if current_table:
            table_rows = []
            for row in current_table:
                if not re.match(r'^[\|\-\:\s]+$', row):
                    table_rows.append(row)
            
            if table_rows:
                tables.append((table_start_line, table_rows))
        
        return tables
    
    def parse_table_row(self, row: str) -> List[str]:
        """
        Parse a markdown table row into individual cells.
        
        Args:
            row: Markdown table row string
            
        Returns:
            List of cell contents
        """
        # Remove leading and trailing |
        row = row.strip()
        if row.startswith('|'):
            row = row[1:]
        if row.endswith('|'):
            row = row[:-1]
        
        # Split by | and clean up
        cells = [cell.strip() for cell in row.split('|')]
        return cells
    
    def wrap_text(self, text: str, max_width: int) -> str:
        """
        Wrap text to fit within specified column width.
        
        Args:
            text: Text to wrap
            max_width: Maximum width per line
            
        Returns:
            Wrapped text with line breaks
        """
        if len(text) <= max_width:
            return text
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_width:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Word is longer than max_width, split it
                    while len(word) > max_width:
                        lines.append(word[:max_width])
                        word = word[max_width:]
                    current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def create_docx_table(self, doc: Document, table_data: List[List[str]], 
                         table_number: int, start_line: int) -> None:
        """
        Create a formatted table in the DOCX document.
        
        Args:
            doc: Document object
            table_data: Parsed table data
            table_number: Table number for heading
            start_line: Line number where table starts
        """
        # Add heading
        heading = doc.add_heading(f'Table {table_number} (Line {start_line})', level=2)
        
        # Determine number of columns
        max_cols = max(len(row) for row in table_data) if table_data else 0
        
        if max_cols == 0:
            return
        
        # Create table
        table = doc.add_table(rows=0, cols=max_cols)
        table.style = 'Light Grid Accent 1'
        
        # Add rows
        for row_data in table_data:
            row_cells = table.add_row().cells
            
            for i, cell_text in enumerate(row_data):
                if i < len(row_cells):
                    # Wrap text to fit column width
                    wrapped_text = self.wrap_text(cell_text, self.max_column_width)
                    row_cells[i].text = wrapped_text
                    
                    # Center align text
                    for paragraph in row_cells[i].paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add some spacing after table
        doc.add_paragraph()
    
    def convert_to_docx(self, input_file: str, output_file: str) -> bool:
        """
        Convert markdown tables from input file to DOCX format.
        
        Args:
            input_file: Path to input text file
            output_file: Path to output DOCX file
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Read input file
            with open(input_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Detect tables
            tables = self.detect_markdown_tables(text)
            
            if not tables:
                print(f"No markdown tables found in {input_file}")
                return False
            
            # Create DOCX document
            doc = Document()
            doc.add_heading('Markdown Tables Export', level=1)
            doc.add_paragraph(f'Extracted from: {os.path.basename(input_file)}')
            doc.add_paragraph(f'Total tables found: {len(tables)}')
            doc.add_paragraph()
            
            # Process each table
            for table_num, (start_line, table_lines) in enumerate(tables, 1):
                table_data = []
                for line in table_lines:
                    cells = self.parse_table_row(line)
                    table_data.append(cells)
                
                self.create_docx_table(doc, table_data, table_num, start_line)
            
            # Save document
            doc.save(output_file)
            print(f"Successfully converted {len(tables)} tables to {output_file}")
            return True
            
        except Exception as e:
            print(f"Error converting file: {e}")
            return False


def main():
    """Command line interface for the markdown table converter."""
    parser = argparse.ArgumentParser(
        description='Convert markdown tables from text files to DOCX format'
    )
    parser.add_argument('input_file', help='Input text file containing markdown tables')
    parser.add_argument('output_file', help='Output DOCX file path')
    parser.add_argument('--max-width', type=int, default=40,
                       help='Maximum characters per column (default: 40)')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)
    
    # Create converter and run conversion
    converter = MarkdownTableConverter(max_column_width=args.max_width)
    success = converter.convert_to_docx(args.input_file, args.output_file)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()