#!/usr/bin/env python3
"""
Document Reader - Universal document reading utility.

This module provides a comprehensive document reader that supports multiple file formats:
- PDF files (.pdf)
- Word documents (.docx)
- PowerPoint presentations (.pptx)
- Text files (.txt)
- Markdown files (.md)
- CSV files (.csv)
- Excel files (.xlsx)
"""

import os
import logging
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Union, Optional, Tuple

# Document format dependencies
import PyPDF2
from docx import Document
from pptx import Presentation
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


class DocumentReader:
    """
    Universal document reader supporting multiple file formats.
    
    Supported formats:
    - PDF (.pdf) - using PyPDF2
    - Word (.docx) - using python-docx
    - PowerPoint (.pptx) - using python-pptx
    - Text (.txt) - native Python
    - Markdown (.md) - native Python
    - CSV (.csv) - using pandas
    - Excel (.xlsx) - using pandas
    """
    
    def __init__(self):
        """Initialize the DocumentReader with format handlers."""
        self.supported_formats = {
            '.pdf': self._read_pdf,
            '.docx': self._read_docx,
            '.pptx': self._read_pptx,
            '.txt': self._read_text,
            '.md': self._read_text,
            '.csv': self._read_csv,
            '.xlsx': self._read_xlsx
        }
    
    def read_document(self, file_path: Union[str, Path], as_markdown: bool = False) -> str:
        """
        Read a single document and return its content as string.
        
        Args:
            file_path: Path to the document file
            as_markdown: If True, format output as markdown preserving structure
            
        Returns:
            str: Document content as text or markdown
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}. "
                           f"Supported formats: {list(self.supported_formats.keys())}")
        
        try:
            content = self.supported_formats[file_extension](file_path, as_markdown)
            logger.info(f"Successfully read {file_extension} file: {file_path.name}")
            return content
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            raise
    
    def read_multiple_documents(self, file_paths: List[Union[str, Path]], as_markdown: bool = False) -> Dict[str, Dict[str, str]]:
        """
        Read multiple documents and return a mapping of results.
        
        Args:
            file_paths: List of paths to document files
            as_markdown: If True, format output as markdown preserving structure
            
        Returns:
            Dict[str, Dict[str, str]]: Dictionary mapping file names to their metadata:
                {
                    "filename.pdf": {
                        "file_type": "pdf",
                        "content": "document content...",
                        "status": "success"
                    },
                    "failed_file.doc": {
                        "file_type": "doc", 
                        "content": "",
                        "status": "error",
                        "error": "error message"
                    }
                }
        """
        results = {}
        
        for file_path in file_paths:
            file_path = Path(file_path)
            file_name = file_path.name
            file_type = file_path.suffix.lower().lstrip('.')
            
            try:
                content = self.read_document(file_path, as_markdown)
                results[file_name] = {
                    "file_type": file_type,
                    "content": content,
                    "status": "success"
                }
            except Exception as e:
                results[file_name] = {
                    "file_type": file_type,
                    "content": "",
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"Failed to read {file_name}: {e}")
        
        return results
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.
        
        Returns:
            List[str]: List of supported file extensions
        """
        return list(self.supported_formats.keys())
    
    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """
        Check if a file format is supported.
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if format is supported
        """
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.supported_formats
    
    def _detect_list_item(self, line: str) -> Optional[str]:
        """
        Detect if a line is a list item and return the formatted markdown version.
        
        This method uses a systematic approach to detect various bullet point and numbering patterns:
        - Unicode bullet characters (General_Category = Symbol other)
        - Common ASCII bullet patterns 
        - Numbered lists with various delimiters
        - Lettered lists
        - Roman numerals
        - Indented patterns
        
        Args:
            line: The line to analyze
            
        Returns:
            str: Formatted markdown list item, or None if not a list item
        """
        line = line.strip()
        if not line:
            return None
        
        # Pattern 1: Unicode bullet characters (comprehensive)
        # Check if the first character is a bullet-like symbol
        first_char = line[0]
        if len(line) > 1:
            # Unicode categories that typically contain bullet characters
            char_category = unicodedata.category(first_char)
            if char_category in ['So', 'Sm', 'Sc']:  # Symbol other, Symbol math, Symbol currency
                # Additional check: common bullet Unicode ranges
                char_code = ord(first_char)
                bullet_ranges = [
                    (0x2022, 0x2043),  # General Punctuation bullets
                    (0x25A0, 0x25FF),  # Geometric Shapes 
                    (0x2190, 0x21FF),  # Arrows
                    (0x2600, 0x26FF),  # Miscellaneous Symbols
                    (0x2700, 0x27BF),  # Dingbats
                ]
                if any(start <= char_code <= end for start, end in bullet_ranges):
                    return f"- {line[1:].strip()}"
        
        # Pattern 2: ASCII bullet patterns with regex
        ascii_bullet_pattern = r'^[-*+•◦▪▫‣⁃] '
        if re.match(ascii_bullet_pattern, line):
            bullet_char = line[0]
            return f"- {line[1:].strip()}"
        
        # Pattern 3: Numbered lists (comprehensive)
        # Arabic numerals: 1. 1) 1: 1- 1/ 1\
        numbered_pattern = r'^(\d+)[.)\-:/\\]\s+'
        match = re.match(numbered_pattern, line)
        if match:
            return f"1. {line[len(match.group(0)):].strip()}"
        
        # Pattern 4: Lettered lists: a. A. a) A) a: A:
        letter_pattern = r'^([a-zA-Z])[.)\-:]\s+'
        match = re.match(letter_pattern, line)
        if match:
            return f"1. {line[len(match.group(0)):].strip()}"
        
        # Pattern 5: Roman numerals: i. I. ii. II. iii. III. iv. IV. v. V.
        roman_pattern = r'^([ivxlcdmIVXLCDM]+)[.)\-:]\s+'
        match = re.match(roman_pattern, line)
        if match:
            # Verify it's actually a roman numeral
            roman_chars = set('ivxlcdmIVXLCDM')
            if all(c in roman_chars for c in match.group(1)):
                return f"1. {line[len(match.group(0)):].strip()}"
        
        # Pattern 6: Indented bullet points (no explicit bullet character)
        # Lines that start with 2+ spaces followed by text could be sub-bullets
        indent_pattern = r'^(\s{2,})([^\s].*)'
        match = re.match(indent_pattern, line)
        if match:
            indent_level = len(match.group(1)) // 2  # 2 spaces = 1 indent level
            prefix = "  " * max(0, indent_level - 1)  # Markdown nested list format
            return f"{prefix}- {match.group(2)}"
        
        # Pattern 7: Special characters that commonly serve as bullets
        special_bullets = ['→', '➤', '▶', '►', '‣', '⁃', '⦿', '⦾', '○', '●', '◯', '◉']
        if any(line.startswith(bullet + ' ') for bullet in special_bullets):
            for bullet in special_bullets:
                if line.startswith(bullet + ' '):
                    return f"- {line[len(bullet):].strip()}"
        
        return None
    
    # Format-specific readers
    
    def _read_pdf(self, file_path: Path, as_markdown: bool = False) -> str:
        """Read PDF file using PyPDF2."""
        content = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            if as_markdown:
                                # Format as markdown with page headers
                                formatted_text = self._format_pdf_text_as_markdown(text, page_num + 1)
                                content.append(formatted_text)
                            else:
                                content.append(f"--- Page {page_num + 1} ---\n{text}")
                    except Exception as e:
                        logger.warning(f"Could not extract text from page {page_num + 1}: {e}")
                        if as_markdown:
                            content.append(f"## Page {page_num + 1}\n\n*[Text extraction failed]*")
                        else:
                            content.append(f"--- Page {page_num + 1} ---\n[Text extraction failed]")
        except Exception as e:
            raise Exception(f"Error reading PDF file: {e}")
        
        return "\n\n".join(content) if content else "[No readable text found in PDF]"
    
    def _format_pdf_text_as_markdown(self, text: str, page_num: int) -> str:
        """Format PDF text as markdown with advanced structure detection."""
        lines = text.split('\n')
        formatted_lines = [f"## Page {page_num}"]
        
        for line in lines:
            original_line = line
            line = line.strip()
            if not line:
                continue
                
            # Detect potential headings (all caps, short lines)
            if len(line) < 80 and line.isupper() and len(line) > 3:
                formatted_lines.append(f"\n### {line.title()}")
            else:
                # Use systematic list detection
                list_item = self._detect_list_item(original_line)
                if list_item:
                    formatted_lines.append(list_item)
                else:
                    # Regular paragraph text
                    formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_docx_paragraph_as_markdown(self, paragraph) -> str:
        """Format a Word paragraph as markdown based on its style."""
        text = paragraph.text.strip()
        if not text:
            return ""
            
        # Check paragraph style for headings
        style_name = paragraph.style.name.lower() if paragraph.style else ""
        
        # Handle headings
        if 'heading 1' in style_name or 'title' in style_name:
            return f"# {text}"
        elif 'heading 2' in style_name:
            return f"## {text}"
        elif 'heading 3' in style_name:
            return f"### {text}"
        elif 'heading 4' in style_name:
            return f"#### {text}"
        elif 'heading 5' in style_name:
            return f"##### {text}"
        elif 'heading 6' in style_name:
            return f"###### {text}"
        
        # Handle lists using systematic detection
        list_item = self._detect_list_item(text)
        if list_item:
            return list_item
        
        # Check for bold/italic formatting in runs
        formatted_text = ""
        for run in paragraph.runs:
            run_text = run.text
            if run.bold and run.italic:
                formatted_text += f"***{run_text}***"
            elif run.bold:
                formatted_text += f"**{run_text}**"
            elif run.italic:
                formatted_text += f"*{run_text}*"
            else:
                formatted_text += run_text
        
        return formatted_text if formatted_text.strip() else text
    
    def _format_table_as_markdown(self, table) -> str:
        """Format a table as markdown."""
        if not table.rows:
            return ""
            
        rows = []
        for i, row in enumerate(table.rows):
            cells = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
            rows.append("| " + " | ".join(cells) + " |")
            
            # Add header separator after first row
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(cells)) + " |"
                rows.append(separator)
        
        return "\n".join(rows)
    
    def _format_pptx_text_as_markdown(self, text: str) -> str:
        """Format PowerPoint text as markdown with advanced list detection."""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            original_line = line
            line = line.strip()
            if not line:
                continue
                
            # Detect potential slide titles (usually first non-empty line or all caps)
            if len(line) < 100 and (line.isupper() or len(formatted_lines) == 0):
                formatted_lines.append(f"### {line}")
            else:
                # Use systematic list detection
                list_item = self._detect_list_item(original_line)
                if list_item:
                    formatted_lines.append(list_item)
                else:
                    # Regular text
                    formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_pptx_table_as_markdown(self, table) -> str:
        """Format a PowerPoint table as markdown."""
        if not table.rows:
            return ""
            
        rows = []
        for i, row in enumerate(table.rows):
            cells = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
            rows.append("| " + " | ".join(cells) + " |")
            
            # Add header separator after first row
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(cells)) + " |"
                rows.append(separator)
        
        return "\n".join(rows)
    
    def _read_docx(self, file_path: Path, as_markdown: bool = False) -> str:
        """Read Word document using python-docx."""
        try:
            doc = Document(file_path)
            content = []
            
            # Extract paragraphs with style information for markdown
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    if as_markdown:
                        formatted_text = self._format_docx_paragraph_as_markdown(paragraph)
                        content.append(formatted_text)
                    else:
                        content.append(paragraph.text)
            
            # Extract tables
            for table in doc.tables:
                if as_markdown:
                    markdown_table = self._format_table_as_markdown(table)
                    content.append(markdown_table)
                else:
                    table_content = []
                    for row in table.rows:
                        row_content = []
                        for cell in row.cells:
                            row_content.append(cell.text.strip())
                        table_content.append(" | ".join(row_content))
                    if table_content:
                        content.append("--- Table ---\n" + "\n".join(table_content))
            
            return "\n\n".join(content) if content else "[No readable text found in document]"
            
        except Exception as e:
            raise Exception(f"Error reading Word document: {e}")
    
    def _read_pptx(self, file_path: Path, as_markdown: bool = False) -> str:
        """Read PowerPoint presentation using python-pptx."""
        try:
            prs = Presentation(file_path)
            content = []
            
            for slide_num, slide in enumerate(prs.slides, 1):
                if as_markdown:
                    slide_content = [f"## Slide {slide_num}"]
                else:
                    slide_content = [f"--- Slide {slide_num} ---"]
                
                # Extract text from shapes
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        if as_markdown:
                            # Format slide text with basic markdown
                            formatted_text = self._format_pptx_text_as_markdown(shape.text)
                            slide_content.append(formatted_text)
                        else:
                            slide_content.append(shape.text)
                    elif shape.has_table:
                        # Extract table content
                        if as_markdown:
                            markdown_table = self._format_pptx_table_as_markdown(shape.table)
                            slide_content.append(markdown_table)
                        else:
                            table_content = []
                            for row in shape.table.rows:
                                row_content = []
                                for cell in row.cells:
                                    row_content.append(cell.text.strip())
                                table_content.append(" | ".join(row_content))
                            if table_content:
                                slide_content.append("Table:\n" + "\n".join(table_content))
                
                if len(slide_content) > 1:  # More than just the slide header
                    content.append("\n".join(slide_content))
            
            return "\n\n".join(content) if content else "[No readable text found in presentation]"
            
        except Exception as e:
            raise Exception(f"Error reading PowerPoint presentation: {e}")
    
    def _read_text(self, file_path: Path, as_markdown: bool = False) -> str:
        """Read text file (.txt, .md)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            # Try with different encodings
            encodings = ['latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                        logger.warning(f"File read with {encoding} encoding instead of UTF-8")
                        break
                except UnicodeDecodeError:
                    continue
            else:
                raise Exception(f"Could not decode text file with any supported encoding")
        except Exception as e:
            raise Exception(f"Error reading text file: {e}")
        
        # Apply markdown formatting to .txt files (but not .md files which are already markdown)
        if as_markdown and file_path.suffix.lower() == '.txt':
            return self._format_text_as_markdown(content)
        
        return content
    
    def _format_text_as_markdown(self, text: str) -> str:
        """Format plain text as markdown with list detection."""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if not line.strip():
                formatted_lines.append(line)  # Preserve empty lines
                continue
            
            # Use systematic list detection
            list_item = self._detect_list_item(line)
            if list_item:
                formatted_lines.append(list_item)
            else:
                # Regular text line
                formatted_lines.append(line.rstrip())
        
        return '\n'.join(formatted_lines)
    
    def _read_csv(self, file_path: Path, as_markdown: bool = False) -> str:
        """Read CSV file using pandas."""
        try:
            # Try to read CSV with various parameters
            try:
                df = pd.read_csv(file_path)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin-1')
            except pd.errors.EmptyDataError:
                return "[Empty CSV file]"
            
            # Convert to string representation
            content = []
            
            if as_markdown:
                content.append(f"# CSV File: {file_path.name}")
                content.append(f"**Shape:** {df.shape[0]} rows, {df.shape[1]} columns")
                content.append(f"**Columns:** {', '.join(df.columns.tolist())}")
                content.append("")
                # Convert DataFrame to markdown table
                markdown_table = self._dataframe_to_markdown(df, max_rows=100)
                content.append(markdown_table)
                
                if len(df) > 100:
                    content.append(f"\n*... and {len(df) - 100} more rows*")
            else:
                content.append(f"CSV File: {file_path.name}")
                content.append(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
                content.append(f"Columns: {', '.join(df.columns.tolist())}")
                content.append("\n--- Data ---")
                content.append(df.to_string(index=False, max_rows=100))
                
                if len(df) > 100:
                    content.append(f"\n... and {len(df) - 100} more rows")
            
            return "\n".join(content)
            
        except Exception as e:
            raise Exception(f"Error reading CSV file: {e}")
    
    def _read_xlsx(self, file_path: Path, as_markdown: bool = False) -> str:
        """Read Excel file using pandas."""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            content = []
            if as_markdown:
                content.append(f"# Excel File: {file_path.name}")
                content.append(f"**Sheets:** {', '.join(excel_file.sheet_names)}")
            else:
                content.append(f"Excel File: {file_path.name}")
                content.append(f"Sheets: {', '.join(excel_file.sheet_names)}")
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    if not df.empty:
                        if as_markdown:
                            content.append(f"\n## Sheet: {sheet_name}")
                            content.append(f"**Shape:** {df.shape[0]} rows, {df.shape[1]} columns")
                            content.append(f"**Columns:** {', '.join(df.columns.astype(str).tolist())}")
                            content.append("")
                            markdown_table = self._dataframe_to_markdown(df, max_rows=50)
                            content.append(markdown_table)
                            
                            if len(df) > 50:
                                content.append(f"\n*... and {len(df) - 50} more rows*")
                        else:
                            content.append(f"\n--- Sheet: {sheet_name} ---")
                            content.append(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
                            content.append(f"Columns: {', '.join(df.columns.astype(str).tolist())}")
                            content.append(df.to_string(index=False, max_rows=50))
                            
                            if len(df) > 50:
                                content.append(f"... and {len(df) - 50} more rows")
                    else:
                        if as_markdown:
                            content.append(f"\n## Sheet: {sheet_name}")
                            content.append("*[Empty sheet]*")
                        else:
                            content.append(f"\n--- Sheet: {sheet_name} ---")
                            content.append("[Empty sheet]")
                except Exception as sheet_error:
                    if as_markdown:
                        content.append(f"\n## Sheet: {sheet_name}")
                        content.append(f"*[Error reading sheet: {sheet_error}]*")
                    else:
                        content.append(f"\n--- Sheet: {sheet_name} ---")
                        content.append(f"[Error reading sheet: {sheet_error}]")
            
            return "\n".join(content)
            
        except Exception as e:
            raise Exception(f"Error reading Excel file: {e}")
    
    def _dataframe_to_markdown(self, df, max_rows: int = None) -> str:
        """Convert pandas DataFrame to markdown table format."""
        if df.empty:
            return "*[Empty table]*"
        
        # Limit rows if specified
        display_df = df.head(max_rows) if max_rows else df
        
        # Convert all columns to string to handle various data types
        display_df = display_df.astype(str)
        
        # Create header row
        headers = list(display_df.columns)
        header_row = "| " + " | ".join(headers) + " |"
        
        # Create separator row
        separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
        
        # Create data rows
        data_rows = []
        for _, row in display_df.iterrows():
            # Clean cell values (remove newlines, limit length)
            cells = [str(cell).replace('\n', ' ').replace('|', '\\|')[:100] for cell in row]
            data_row = "| " + " | ".join(cells) + " |"
            data_rows.append(data_row)
        
        # Combine all rows
        return "\n".join([header_row, separator_row] + data_rows)
    
    def save_markdown(self, markdown_content: str, output_path: Union[str, Path]) -> None:
        """
        Save markdown content to a file.
        
        Args:
            markdown_content: The markdown-formatted content to save
            output_path: Path where the markdown file should be saved
            
        Raises:
            IOError: If the file cannot be written
            ValueError: If markdown_content is empty or None
        """
        if not markdown_content:
            raise ValueError("Markdown content cannot be empty or None")
        
        output_path = Path(output_path)
        
        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure the file has .md extension
        if output_path.suffix.lower() != '.md':
            output_path = output_path.with_suffix('.md')
        
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(markdown_content)
            logger.info(f"Successfully saved markdown content to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving markdown file {output_path}: {e}")
            raise IOError(f"Failed to save markdown file: {e}")
    
    def read_and_save_as_markdown(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> str:
        """
        Read a document and save it as markdown in one operation.
        
        Args:
            input_path: Path to the input document
            output_path: Path where the markdown file should be saved
            
        Returns:
            str: The markdown content that was saved
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If file format is not supported
            IOError: If the output file cannot be written
        """
        # Read the document as markdown
        markdown_content = self.read_document(input_path, as_markdown=True)
        
        # Save the markdown content
        self.save_markdown(markdown_content, output_path)
        
        return markdown_content


# Convenience functions for direct usage
def read_document(file_path: Union[str, Path], as_markdown: bool = False) -> str:
    """
    Convenience function to read a single document.
    
    Args:
        file_path: Path to the document
        as_markdown: If True, format output as markdown preserving structure
        
    Returns:
        str: Document content as text or markdown
    """
    reader = DocumentReader()
    return reader.read_document(file_path, as_markdown)


def read_multiple_documents(file_paths: List[Union[str, Path]], as_markdown: bool = False) -> Dict[str, Dict[str, str]]:
    """
    Convenience function to read multiple documents.
    
    Args:
        file_paths: List of file paths
        as_markdown: If True, format output as markdown preserving structure
        
    Returns:
        Dict: Results mapping
    """
    reader = DocumentReader()
    return reader.read_multiple_documents(file_paths, as_markdown)


def get_supported_formats() -> List[str]:
    """
    Get list of supported file formats.
    
    Returns:
        List[str]: Supported file extensions
    """
    reader = DocumentReader()
    return reader.get_supported_formats()


def read_documents(file_paths):
    """Convenience function to read PDF documents."""
    reader = DocumentReader()
    content = reader.read_multiple_documents(file_paths, as_markdown=True)
    return content


# Example usage
if __name__ == "__main__":
    # Example usage
    reader = DocumentReader()
    
    print("Supported formats:", reader.get_supported_formats())
    content = read_documents(["tests/resources/test.pdf", "tests/resources/test.docx"])
    print(content['test.pdf'])
    reader.save_markdown(content['test.docx']['content'], "output/test_docx.md")
    # Example: read a single file
    # content = reader.read_document("example.pdf")
    # print(content[:500])  # Print first 500 characters
    
    # Example: read multiple files
    # file_paths = ["doc1.pdf", "doc2.docx", "data.csv"]
    # results = reader.read_multiple_documents(file_paths)
    # for filename, info in results.items():
    #     print(f"{filename}: {info['status']}")