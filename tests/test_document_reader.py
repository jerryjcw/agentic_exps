#!/usr/bin/env python3
"""
Tests for DocumentReader utility.
"""

import unittest
import tempfile
import os
from pathlib import Path

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
utils_dir = os.path.join(project_root, 'utils')
import sys
sys.path.extend([project_root, utils_dir])

from utils.document_reader import DocumentReader, read_document, read_multiple_documents


class TestDocumentReader(unittest.TestCase):
    """Test cases for DocumentReader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reader = DocumentReader()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_supported_formats(self):
        """Test that all expected formats are supported."""
        expected_formats = ['.pdf', '.docx', '.pptx', '.txt', '.md', '.csv', '.xlsx']
        supported = self.reader.get_supported_formats()
        
        for fmt in expected_formats:
            self.assertIn(fmt, supported)
    
    def test_is_supported(self):
        """Test format support checking."""
        self.assertTrue(self.reader.is_supported('document.pdf'))
        self.assertTrue(self.reader.is_supported('document.txt'))
        self.assertFalse(self.reader.is_supported('document.unknown'))
    
    def test_read_text_file(self):
        """Test reading text files."""
        # Create a test text file
        test_content = "This is a test text file.\nWith multiple lines."
        test_file = Path(self.temp_dir) / "test.txt"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        content = self.reader.read_document(test_file)
        self.assertEqual(content, test_content)
    
    def test_read_markdown_file(self):
        """Test reading markdown files."""
        test_content = "# Test Markdown\n\nThis is **bold** text."
        test_file = Path(self.temp_dir) / "test.md"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        content = self.reader.read_document(test_file)
        self.assertEqual(content, test_content)
    
    def test_file_not_found(self):
        """Test handling of non-existent files."""
        with self.assertRaises(FileNotFoundError):
            self.reader.read_document("nonexistent.txt")
    
    def test_unsupported_format(self):
        """Test handling of unsupported file formats."""
        test_file = Path(self.temp_dir) / "test.unknown"
        test_file.touch()  # Create empty file
        
        with self.assertRaises(ValueError):
            self.reader.read_document(test_file)
    
    def test_read_multiple_documents_success(self):
        """Test reading multiple documents successfully."""
        # Create test files
        test_files = []
        
        # Text file
        txt_file = Path(self.temp_dir) / "test1.txt"
        with open(txt_file, 'w') as f:
            f.write("Text file content")
        test_files.append(txt_file)
        
        # Markdown file
        md_file = Path(self.temp_dir) / "test2.md"
        with open(md_file, 'w') as f:
            f.write("# Markdown content")
        test_files.append(md_file)
        
        results = self.reader.read_multiple_documents(test_files)
        
        self.assertEqual(len(results), 2)
        self.assertIn("test1.txt", results)
        self.assertIn("test2.md", results)
        
        # Check text file result
        txt_result = results["test1.txt"]
        self.assertEqual(txt_result["status"], "success")
        self.assertEqual(txt_result["file_type"], "txt")
        self.assertEqual(txt_result["content"], "Text file content")
        
        # Check markdown file result
        md_result = results["test2.md"]
        self.assertEqual(md_result["status"], "success")
        self.assertEqual(md_result["file_type"], "md")
        self.assertEqual(md_result["content"], "# Markdown content")
    
    def test_read_multiple_documents_with_errors(self):
        """Test reading multiple documents with some failures."""
        test_files = [
            Path(self.temp_dir) / "existing.txt",
            Path(self.temp_dir) / "nonexistent.txt"
        ]
        
        # Create only the first file
        with open(test_files[0], 'w') as f:
            f.write("Existing content")
        
        results = self.reader.read_multiple_documents(test_files)
        
        self.assertEqual(len(results), 2)
        
        # Check successful read
        self.assertEqual(results["existing.txt"]["status"], "success")
        self.assertEqual(results["existing.txt"]["content"], "Existing content")
        
        # Check failed read
        self.assertEqual(results["nonexistent.txt"]["status"], "error")
        self.assertIn("error", results["nonexistent.txt"])
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Create test file
        test_file = Path(self.temp_dir) / "convenience.txt"
        test_content = "Convenience function test"
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Test single file function
        content = read_document(test_file)
        self.assertEqual(content, test_content)
        
        # Test multiple files function
        results = read_multiple_documents([test_file])
        self.assertIn("convenience.txt", results)
        self.assertEqual(results["convenience.txt"]["content"], test_content)


class TestDocumentReaderWithMockDependencies(unittest.TestCase):
    """Test DocumentReader with mocked dependencies."""
    
    def test_initialization(self):
        """Test DocumentReader initialization."""
        reader = DocumentReader()
        # Test that reader initializes properly
        self.assertIsInstance(reader.supported_formats, dict)
        self.assertEqual(len(reader.supported_formats), 7)  # 7 supported formats
    
    def test_pdf_file_error(self):
        """Test PDF reading with non-existent file."""
        reader = DocumentReader()
        
        with self.assertRaises(Exception) as context:
            reader._read_pdf(Path("nonexistent.pdf"))
        self.assertIn("Error reading PDF file", str(context.exception))
    
    def test_docx_file_error(self):
        """Test Word document reading with non-existent file."""
        reader = DocumentReader()
        
        with self.assertRaises(Exception) as context:
            reader._read_docx(Path("nonexistent.docx"))
        self.assertIn("Error reading Word document", str(context.exception))


class TestDocumentReaderIntegration(unittest.TestCase):
    """Integration tests for DocumentReader (require dependencies)."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.reader = DocumentReader()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_csv_reading_with_pandas(self):
        """Test CSV reading when pandas is available."""
        csv_content = "name,age,city\nJohn,30,NYC\nJane,25,LA"
        csv_file = Path(self.temp_dir) / "test.csv"
        
        with open(csv_file, 'w') as f:
            f.write(csv_content)
        
        content = self.reader.read_document(csv_file)
        
        # Should contain CSV metadata
        self.assertIn("CSV File:", content)
        self.assertIn("Shape:", content)
        self.assertIn("Columns:", content)
        self.assertIn("John", content)
        self.assertIn("Jane", content)
    
    def test_pdf_reading_with_test_file(self):
        """Test PDF reading with the actual test PDF file."""
        pdf_path = Path(__file__).parent / "resources" / "test2.pdf"
        
        if not pdf_path.exists():
            self.skipTest("Test PDF file not found at tests/resources/test2.pdf")
        
        content = self.reader.read_document(pdf_path)
        
        # Basic validations for the test PDF
        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 0)
        
        # Should contain page marker
        self.assertIn("--- Page 1 ---", content)
        
        # Should contain some expected content from UK HBAI government report
        self.assertIn("HBAI", content)
        self.assertIn("Households Below Average Income", content)
        self.assertIn("UK", content)
        self.assertIn("income", content)
        self.assertIn("National Statistics", content)
        self.assertIn("DWP", content)
        
        # Should have reasonable content length for government report
        self.assertGreater(len(content), 10000)
        self.assertLess(len(content), 50000)  # Reasonable upper bound for government report PDF
        
        print(f"✅ PDF test successful: {len(content)} characters extracted")
    
    def test_text_encoding_fallback(self):
        """Test text file reading with encoding fallback."""
        # Create a file with latin-1 encoding
        test_content = "Café résumé naïve"
        test_file = Path(self.temp_dir) / "encoded.txt"
        
        with open(test_file, 'w', encoding='latin-1') as f:
            f.write(test_content)
        
        # Should successfully read with fallback encoding
        content = self.reader.read_document(test_file)
        self.assertEqual(content, test_content)


class TestDocumentReaderMarkdown(unittest.TestCase):
    """Test markdown formatting functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reader = DocumentReader()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_text_file_markdown_passthrough(self):
        """Test that text files pass through unchanged in markdown mode."""
        test_content = "# This is already markdown\n\n- Item 1\n- Item 2"
        test_file = Path(self.temp_dir) / "test.md"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Markdown mode should return same content for .md files
        content_regular = self.reader.read_document(test_file, as_markdown=False)
        content_markdown = self.reader.read_document(test_file, as_markdown=True)
        
        self.assertEqual(content_regular, test_content)
        self.assertEqual(content_markdown, test_content)
    
    def test_csv_markdown_formatting(self):
        """Test CSV markdown table formatting."""
        csv_content = "name,age,city\nJohn,30,NYC\nJane,25,LA"
        csv_file = Path(self.temp_dir) / "test.csv"
        
        with open(csv_file, 'w') as f:
            f.write(csv_content)
        
        content_markdown = self.reader.read_document(csv_file, as_markdown=True)
        
        # Should contain markdown headers and table format
        self.assertIn("# CSV File:", content_markdown)
        self.assertIn("**Shape:**", content_markdown)
        self.assertIn("| name | age | city |", content_markdown)
        self.assertIn("| --- | --- | --- |", content_markdown)
        self.assertIn("| John | 30 | NYC |", content_markdown)
    
    def test_markdown_parameter_in_multiple_documents(self):
        """Test markdown parameter in multiple document reading."""
        # Create test files
        txt_file = Path(self.temp_dir) / "test.txt"
        with open(txt_file, 'w') as f:
            f.write("Simple text content")
        
        csv_file = Path(self.temp_dir) / "test.csv"
        with open(csv_file, 'w') as f:
            f.write("col1,col2\nval1,val2")
        
        results = self.reader.read_multiple_documents([txt_file, csv_file], as_markdown=True)
        
        # Check that both files were processed
        self.assertEqual(len(results), 2)
        self.assertIn("test.txt", results)
        self.assertIn("test.csv", results)
        
        # CSV should have markdown formatting
        csv_result = results["test.csv"]["content"]
        self.assertIn("# CSV File:", csv_result)
        self.assertIn("| col1 | col2 |", csv_result)
    
    def test_convenience_functions_with_markdown(self):
        """Test convenience functions with markdown parameter."""
        test_file = Path(self.temp_dir) / "convenience.txt"
        test_content = "Test content for convenience function"
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Test single file convenience function
        from utils.document_reader import read_document, read_multiple_documents
        
        content = read_document(test_file, as_markdown=True)
        self.assertEqual(content, test_content)
        
        # Test multiple files convenience function
        results = read_multiple_documents([test_file], as_markdown=True)
        self.assertIn("convenience.txt", results)
        self.assertEqual(results["convenience.txt"]["content"], test_content)
    
    def test_save_markdown_basic(self):
        """Test basic markdown saving functionality."""
        markdown_content = "# Test Document\n\nThis is **bold** text.\n\n- Item 1\n- Item 2"
        output_file = Path(self.temp_dir) / "output.md"
        
        self.reader.save_markdown(markdown_content, output_file)
        
        # Verify file was created and content is correct
        self.assertTrue(output_file.exists())
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        self.assertEqual(saved_content, markdown_content)
    
    def test_save_markdown_auto_extension(self):
        """Test that .md extension is automatically added."""
        markdown_content = "# Test\n\nContent here."
        output_file = Path(self.temp_dir) / "output"  # No extension
        
        self.reader.save_markdown(markdown_content, output_file)
        
        # Should create output.md
        expected_file = Path(self.temp_dir) / "output.md"
        self.assertTrue(expected_file.exists())
        self.assertFalse(output_file.exists())  # Original path without extension shouldn't exist
    
    def test_save_markdown_create_directories(self):
        """Test that parent directories are created automatically."""
        markdown_content = "# Test\n\nContent."
        output_file = Path(self.temp_dir) / "subdir" / "nested" / "output.md"
        
        self.reader.save_markdown(markdown_content, output_file)
        
        # Directory should be created and file should exist
        self.assertTrue(output_file.exists())
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, markdown_content)
    
    def test_save_markdown_empty_content_error(self):
        """Test error handling for empty content."""
        output_file = Path(self.temp_dir) / "output.md"
        
        with self.assertRaises(ValueError) as context:
            self.reader.save_markdown("", output_file)
        self.assertIn("cannot be empty", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            self.reader.save_markdown(None, output_file)
        self.assertIn("cannot be empty", str(context.exception))
    
    def test_read_and_save_as_markdown(self):
        """Test the combined read and save operation."""
        # Create a test CSV file
        csv_content = "name,age\nJohn,30\nJane,25"
        csv_file = Path(self.temp_dir) / "test.csv"
        with open(csv_file, 'w') as f:
            f.write(csv_content)
        
        output_file = Path(self.temp_dir) / "output.md"
        
        # Read and save as markdown
        markdown_content = self.reader.read_and_save_as_markdown(csv_file, output_file)
        
        # Verify file exists and content is correct
        self.assertTrue(output_file.exists())
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        
        self.assertEqual(saved_content, markdown_content)
        self.assertIn("# CSV File:", markdown_content)
        self.assertIn("| name | age |", markdown_content)
    
    def test_comprehensive_bullet_detection(self):
        """Test the comprehensive bullet point detection system."""
        # Test various bullet point patterns
        test_content = """Meeting Notes
• Standard bullet point
◦ Hollow circle bullet
▪ Black square bullet
‣ Triangular bullet
→ Arrow bullet
★ Star bullet
✓ Checkmark item

Action Items:
1. First numbered item
2) Second with parenthesis
a. Letter item
i. Roman numeral

  • Indented bullet
    ◦ Double indented
"""
        
        test_file = Path(self.temp_dir) / "test_bullets.txt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Test without markdown formatting
        regular_content = self.reader.read_document(test_file, as_markdown=False)
        self.assertIn("• Standard bullet point", regular_content)
        self.assertIn("◦ Hollow circle bullet", regular_content)
        
        # Test with markdown formatting
        markdown_content = self.reader.read_document(test_file, as_markdown=True)
        
        # Should convert various bullets to markdown format
        self.assertIn("- Standard bullet point", markdown_content)
        self.assertIn("- Hollow circle bullet", markdown_content)
        self.assertIn("- Black square bullet", markdown_content)
        self.assertIn("- Triangular bullet", markdown_content)
        self.assertIn("- Arrow bullet", markdown_content)
        self.assertIn("- Star bullet", markdown_content)
        self.assertIn("- Checkmark item", markdown_content)
        
        # Should convert numbered lists
        self.assertIn("1. First numbered item", markdown_content)
        self.assertIn("1. Second with parenthesis", markdown_content)
        self.assertIn("1. Letter item", markdown_content)
        self.assertIn("1. Roman numeral", markdown_content)
        
        # Should handle indented bullets
        self.assertIn("- Indented bullet", markdown_content)
        self.assertIn("- Double indented", markdown_content)
    
    def test_bullet_detection_edge_cases(self):
        """Test edge cases for bullet point detection."""
        reader = self.reader
        
        # Test individual bullet detection
        test_cases = [
            ("• Regular bullet", "- Regular bullet"),
            ("1. Numbered list", "1. Numbered list"),
            ("a) Letter list", "1. Letter list"),
            ("i. Roman numeral", "1. Roman numeral"),
            ("→ Arrow", "- Arrow"),
            ("★ Star", "- Star"),
            ("  • Indented", "- Indented"),
            ("Regular text", None),  # Should not be detected
            ("", None),  # Empty line
        ]
        
        for input_line, expected in test_cases:
            result = reader._detect_list_item(input_line)
            if expected:
                self.assertEqual(result, expected, f"Failed for input: '{input_line}'")
            else:
                self.assertIsNone(result, f"Should not detect bullet for: '{input_line}'")


if __name__ == '__main__':
    unittest.main()