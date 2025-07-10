#!/usr/bin/env python3
"""
Document Q&A System using Google ADK with Two-Agent Memory Approach

This program demonstrates a two-agent architecture using InMemorySessionService and InMemoryMemoryService:
1. DocumentProcessingAgent - Reads and analyzes PDF documents, stores key information in memory
2. DocumentQAAgent - Uses google.adk.tools.load_memory to retrieve stored information and answer questions

The system processes documents from the input/papers folder and creates a searchable knowledge base.
"""

import sys
import asyncio
import logging
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner, types
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import load_memory
from utils.document_reader import DocumentReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentQASystem:
    """Interactive Q&A system using two-agent approach with memory storage."""
    
    def __init__(self, papers_folder: str = "input/papers"):
        """Initialize the Q&A system with two-agent approach."""
        self.papers_folder = Path(papers_folder)
        self.document_reader = DocumentReader()
        self.documents_content = {}
        
        # Session services
        self.session_service = None
        self.memory_service = None
        
        # Agents and runners
        self.document_agent = None
        self.qa_agent = None
        self.document_runner = None
        self.qa_runner = None
        
        # Session IDs
        self.document_session_id = "document_processing_session"
        self.qa_session_id = "qa_session"
        self.user_id = "qa_user"
        
        # Load environment variables
        load_dotenv()
        
    def load_documents(self) -> None:
        """Load all PDF documents from the papers folder."""
        logger.info(f"Loading documents from: {self.papers_folder}")
        
        if not self.papers_folder.exists():
            raise FileNotFoundError(f"Papers folder not found: {self.papers_folder}")
        
        # Find all PDF files
        pdf_files = list(self.papers_folder.glob("*.pdf"))
        
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in: {self.papers_folder}")
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Read all documents
        for pdf_file in pdf_files:
            try:
                logger.info(f"Reading: {pdf_file.name}")
                content = self.document_reader.read_document(pdf_file, as_markdown=True)
                self.documents_content[pdf_file.name] = content
                logger.info(f"Successfully loaded: {pdf_file.name} ({len(content)} characters)")
            except Exception as e:
                logger.error(f"Failed to read {pdf_file.name}: {e}")
        
        logger.info(f"Successfully loaded {len(self.documents_content)} documents")
    
    def create_document_agent(self) -> Agent:
        """Create agent for processing and storing document information."""
        system_instruction = """You are a comprehensive document processing agent that extracts and stores detailed information from any type of document.

        INSTRUCTIONS:
        1. Analyze the document thoroughly and extract ALL important information
        2. Focus on preserving FACTS, NUMBERS, STATISTICS, and SPECIFIC DETAILS
        3. Extract and organize the following categories:

        FACTUAL INFORMATION:
        - Specific numbers, percentages, amounts, quantities, dates, timeframes
        - Names, titles, organizations, locations, addresses
        - Technical specifications, measurements, dimensions
        - Rules, regulations, requirements, criteria

        STRUCTURED DATA:
        - Tables, lists, schedules, pricing information
        - Process steps, procedures, workflows
        - Categories, classifications, hierarchies
        - Contact information, references, citations

        FINDINGS & RESULTS:
        - Key conclusions, outcomes, decisions
        - Research findings, survey results, analysis outcomes
        - Performance metrics, success rates, failure rates
        - Trends, patterns, correlations identified

        CONTEXTUAL INFORMATION:
        - Background information, historical context
        - Scope, limitations, assumptions
        - Implications, consequences, recommendations
        - Related topics, cross-references

        4. PRESERVE ORIGINAL TERMINOLOGY and exact wording for important concepts
        5. MAINTAIN NUMERICAL PRECISION - include exact figures, not approximations
        6. STRUCTURE your analysis clearly with headings and bullet points
        7. Always specify the SOURCE DOCUMENT NAME
        8. Be COMPREHENSIVE - capture as much detail as possible rather than summarizing

        Your goal is to create a detailed, searchable knowledge repository that preserves the maximum amount of information from each document for future retrieval."""

        # Create LiteLLM model
        model = LiteLlm(model='openai/gpt-4o-mini', max_tokens=8192, temperature=0.75)

        # Create document processing agent
        agent = Agent(
            name="DocumentProcessingAgent",
            model=model,
            instruction=system_instruction,
            description="Agent that processes and stores document information in memory"
        )
        
        return agent
    
    def create_qa_agent(self) -> Agent:
        """Create agent for answering questions using stored memory."""
        system_instruction = """You are a research assistant that answers questions based on previously processed research papers.

        INSTRUCTIONS:
        1. Use the load_memory tool first to search for relevant information from stored documents
        2. Answer questions based ONLY on the information retrieved from memory
        3. If you cannot find relevant information, clearly state that
        4. Always cite which document(s) you're referencing when answering
        5. Provide detailed, accurate answers when the information is available
        6. If asked about topics not covered in the stored papers, politely explain that you can only answer based on the processed documents

        CRITICAL: You must use the load_memory tool to retrieve context before answering ANY question."""

        # Create LiteLLM model
        model = LiteLlm(model='openai/gpt-4o')
        
        # Create Q&A agent with memory tool
        agent = Agent(
            name="DocumentQAAgent",
            model=model,
            instruction=system_instruction,
            description="Research assistant that answers questions using stored document memories",
            tools=[load_memory]
        )
        
        logger.info(f"Created Q&A agent with {len(agent.tools)} tools: {[tool.__name__ if hasattr(tool, '__name__') else str(tool) for tool in agent.tools]}")
        
        return agent
    
    async def initialize_session(self) -> None:
        """Initialize session and memory services, create agents."""
        logger.info("Initializing session and memory services...")
        
        # Create session and memory services
        self.session_service = InMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        
        # Create agents
        self.document_agent = self.create_document_agent()
        self.qa_agent = self.create_qa_agent()
        
        # Create runners
        self.document_runner = Runner(
            app_name="DocumentProcessingSystem",
            agent=self.document_agent,
            session_service=self.session_service,
            memory_service=self.memory_service
        )
        
        self.qa_runner = Runner(
            app_name="DocumentProcessingSystem",
            agent=self.qa_agent,
            session_service=self.session_service,
            memory_service=self.memory_service
        )
        
        logger.info(f"Created Q&A runner with memory service: {self.memory_service}")
        logger.info(f"Q&A agent tools: {[str(tool) for tool in self.qa_agent.tools]}")
        
        # Create sessions
        await self.session_service.create_session(
            user_id=self.user_id,
            session_id=self.document_session_id,
            app_name="DocumentProcessingSystem"
        )
        
        await self.session_service.create_session(
            user_id=self.user_id,
            session_id=self.qa_session_id,
            app_name="DocumentProcessingSystem"
        )
        
        logger.info("Session and memory services initialized successfully")
    
    async def process_documents_to_memory(self) -> None:
        """Process each document through the document agent and store in memory."""
        if not self.document_runner:
            raise RuntimeError("System not initialized. Call initialize_session() first.")
        
        logger.info("Processing documents and storing in memory...")
        
        for filename, content in self.documents_content.items():
            logger.info(f"Processing document: {filename}")
            
            # Create message for document processing
            prompt = f"""Please analyze the following document and extract key information for storage:
            Document: {filename}
            Content:
            {content}
            Please provide a comprehensive analysis including main objectives, methodology, findings, and conclusions."""
            
            message = types.Content(role="user", parts=[{"text": prompt}])
            
            # Process document with document agent
            response_generator = self.document_runner.run(
                user_id=self.user_id,
                session_id=self.document_session_id,
                new_message=message
            )
            
            # Collect response to ensure processing completes
            response_text = ""
            for event in response_generator:
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
                    else:
                        response_text += str(event.content)
                elif hasattr(event, 'text'):
                    response_text += event.text
            logger.info(f"########$$$$ The response for {filename} is: {response_text[:4096]}... $$$$########")  # Log first 100 characters
            logger.info(f"Processed document: {filename}")
        
        # Add the completed document processing session to memory
        document_session = await self.session_service.get_session(
            user_id=self.user_id,
            session_id=self.document_session_id,
            app_name="DocumentProcessingSystem"
        )
        
        if document_session:
            logger.info(f"Document session found: {type(document_session)}")
            await self.memory_service.add_session_to_memory(document_session)
            logger.info("Document processing session added to memory")
        else:
            logger.warning("No document session found to add to memory")
        logger.info("All documents processed and stored in memory")
    
    async def ask_question(self, question: str) -> str:
        """Ask a question and get an answer from the Q&A agent."""
        if not self.qa_runner:
            raise RuntimeError("System not initialized. Call initialize_session() first.")
        
        logger.info(f"Processing question: {question}")
        
        # Debug: Check if there are memories available before asking
        try:
            if hasattr(self.memory_service, 'search_memory'):
                memory_response = await self.memory_service.search_memory(
                    user_id=self.user_id,
                    query=question,
                    app_name="DocumentProcessingSystem"
                )
                if hasattr(memory_response, 'memories'):
                    memories = memory_response.memories
                    logger.info(f"Available memories for query '{question}': {len(memories)}")
                    for i, memory in enumerate(memories[:2]):  # Show first 2 memories
                        if hasattr(memory, 'content'):
                            content = memory.content
                            if hasattr(content, 'parts'):
                                content_text = ""
                                for part in content.parts:
                                    if hasattr(part, 'text'):
                                        content_text += part.text
                                logger.info(f"Memory in part {i}: {content_text[:200]}...")
                            else:
                                logger.info(f"Memory no parts {i}: {str(content)[:200]}...")
                        else:
                            logger.info(f"Memory raw {i}: {str(memory)[:200]}...")
                else:
                    logger.info(f"Memory response has no 'memories' attribute")
            else:
                logger.warning("search_memory method not available on memory service")
        except Exception as e:
            logger.error(f"Error checking memories for question: {e}")
        
        # Create message
        message = types.Content(role="user", parts=[{"text": question}])
        
        # Run the Q&A agent
        response_generator = self.qa_runner.run(
            user_id=self.user_id,
            session_id=self.qa_session_id,
            new_message=message
        )
        
        # Collect response
        response_text = ""
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
                else:
                    response_text += str(event.content)
            elif hasattr(event, 'text'):
                response_text += event.text
        
        return response_text.strip()
    
    def get_document_summary(self) -> str:
        """Get a summary of loaded documents."""
        if not self.documents_content:
            return "No documents loaded."
        
        summary = ["📚 Loaded Documents:"]
        for filename, content in self.documents_content.items():
            word_count = len(content.split())
            summary.append(f"  • {filename} ({word_count:,} words)")
        
        return "\n".join(summary)
    
    async def interactive_mode(self) -> None:
        """Run the system in interactive mode."""
        print("🤖 Document Q&A System")
        print("=" * 50)
        print(self.get_document_summary())
        print("\nType your questions below. Type 'quit' or 'exit' to stop.")
        print("Commands:")
        print("  • 'help' - Show available commands")
        print("  • 'docs' - List loaded documents")
        print("  • 'quit' or 'exit' - Exit the system")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    print("\n📖 Available Commands:")
                    print("  • Ask any question about the loaded research papers")
                    print("  • 'docs' - List loaded documents")
                    print("  • 'quit' or 'exit' - Exit the system")
                    continue
                
                if user_input.lower() == 'docs':
                    print("\n" + self.get_document_summary())
                    continue
                
                if not user_input:
                    print("Please enter a question or command.")
                    continue
                
                # Process question
                print("🤔 Thinking...")
                try:
                    answer = await self.ask_question(user_input)
                    print(f"\n🤖 Assistant: {answer}")
                except Exception as e:
                    print(f"❌ Error processing question: {e}")
                    logger.error(f"Error processing question: {e}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                logger.error(f"Unexpected error: {e}")
    
    async def batch_mode(self, questions: List[str], output_file: str = None) -> List[Dict[str, Any]]:
        """Process questions in batch mode and return results."""
        print("🚀 Running in batch mode...")
        print(f"Processing {len(questions)} questions...")
        
        results = []
        
        for i, question in enumerate(questions, 1):
            print(f"\n📝 Question {i}/{len(questions)}: {question}")
            
            try:
                answer = await self.ask_question(question)
                result = {
                    "question": question,
                    "answer": answer,
                    "status": "success"
                }
                print(f"✅ Answered: {answer[:100]}...")
                
            except Exception as e:
                result = {
                    "question": question,
                    "answer": None,
                    "error": str(e),
                    "status": "error"
                }
                print(f"❌ Error: {e}")
                logger.error(f"Error processing question '{question}': {e}")
            
            results.append(result)
        
        # Save results to file if specified
        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {output_path}")
        
        return results
    
    async def load_questions_from_file(self, file_path: str) -> List[str]:
        """Load questions from a file (one per line or JSON format)."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Questions file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Try to parse as JSON first
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return [str(q) for q in data]
            elif isinstance(data, dict) and 'questions' in data:
                return [str(q) for q in data['questions']]
            else:
                raise ValueError("JSON format should be a list or dict with 'questions' key")
        except json.JSONDecodeError:
            # Fallback to line-by-line format
            questions = [line.strip() for line in content.split('\n') if line.strip()]
            return questions


async def main():
    """Main function to run the Document Q&A system."""
    try:
        # Initialize the system
        qa_system = DocumentQASystem()
        
        # Load documents
        print("📄 Loading documents...")
        qa_system.load_documents()
        
        # Initialize session
        print("🔧 Initializing session and memory services...")
        await qa_system.initialize_session()
        
        # Process documents to memory
        print("🧠 Processing documents and storing in memory...")
        await qa_system.process_documents_to_memory()
        
        # Run interactive mode
        await qa_system.interactive_mode()
        
    except Exception as e:
        logger.error(f"System error: {e}")
        print(f"❌ System error: {e}")
        return 1
    
    return 0


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Document Q&A System using Google ADK with Two-Agent Memory Approach",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (default)
  python document_qa_system.py
  
  # Batch mode with questions from file
  python document_qa_system.py --batch --questions questions.txt
  
  # Batch mode with inline questions
  python document_qa_system.py --batch --questions "What is the cost?" "How do I pay?"
  
  # Batch mode with output file
  python document_qa_system.py --batch --questions questions.json --output results.json
        """
    )
    
    parser.add_argument(
        "--batch", "-b",
        action="store_true",
        help="Run in batch mode instead of interactive mode"
    )
    
    parser.add_argument(
        "--questions", "-q",
        nargs="+",
        help="Questions to process (file path or inline questions)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path for batch results (JSON format)"
    )
    
    parser.add_argument(
        "--papers-folder", "-p",
        default="input/papers",
        help="Folder containing PDF documents (default: input/papers)"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    async def main_with_args():
        """Main function with command line arguments."""
        try:
            # Initialize the system
            qa_system = DocumentQASystem(papers_folder=args.papers_folder)
            
            # Load documents
            print("📄 Loading documents...")
            qa_system.load_documents()
            
            # Initialize session
            print("🔧 Initializing session and memory services...")
            await qa_system.initialize_session()
            
            # Process documents to memory
            print("🧠 Processing documents and storing in memory...")
            await qa_system.process_documents_to_memory()
            
            # Run in batch or interactive mode
            if args.batch:
                if not args.questions:
                    print("❌ Batch mode requires --questions argument")
                    return 1
                
                # Load questions
                questions = []
                for q in args.questions:
                    if len(args.questions) == 1 and Path(q).exists():
                        # Single argument that's a file path
                        questions = await qa_system.load_questions_from_file(q)
                        break
                    else:
                        # Multiple inline questions
                        questions.append(q)
                
                if not questions:
                    print("❌ No questions found to process")
                    return 1
                
                # Process questions in batch
                results = await qa_system.batch_mode(questions, args.output)
                
                # Print summary
                successful = sum(1 for r in results if r["status"] == "success")
                failed = len(results) - successful
                print(f"\n📊 Batch processing complete:")
                print(f"   ✅ Successful: {successful}")
                print(f"   ❌ Failed: {failed}")
                print(f"   📝 Total: {len(results)}")
                
            else:
                # Run interactive mode
                await qa_system.interactive_mode()
            
        except Exception as e:
            logger.error(f"System error: {e}")
            print(f"❌ System error: {e}")
            return 1
        
        return 0
    
    # Run the system
    exit_code = asyncio.run(main_with_args())
    sys.exit(exit_code)