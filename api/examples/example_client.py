#!/usr/bin/env python3
"""
Example client script for the Flexible Agent API.
This script demonstrates how to call the API with the simple_code_improvement configuration.
"""

import requests
import json
import time
from pathlib import Path

# API endpoint
API_URL = "http://localhost:8000/workflow/run"

def load_config_file(file_path):
    """Load configuration file content."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def call_workflow_api(job_config, agent_config, template_config):
    """Call the workflow API with configurations."""
    payload = {
        "job_config": job_config,
        "agent_config": agent_config,
        "template_config": template_config
    }
    
    try:
        print("🚀 Calling API...")
        print(f"📡 URL: {API_URL}")
        print(f"📄 Job config length: {len(job_config)} characters")
        print(f"🤖 Agent config length: {len(agent_config)} characters")
        print(f"📝 Template config length: {len(template_config)} characters")
        print("-" * 60)
        
        response = requests.post(API_URL, json=payload, timeout=600)  # 10 minute timeout
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Error details: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
        return None
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - is the server running?")
        return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def save_response_to_file(response_data, output_file):
    """Save the API response to a file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(response_data, f, indent=2)
        print(f"💾 Response saved to: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving response: {e}")
        return False

def main():
    """Main function to run the example."""
    print("🎯 Flexible Agent API Example Client")
    print("=" * 60)
    
    # Configuration file paths
    project_root = Path(__file__).parent.parent
    job_config_path = project_root / "config/job/yaml_examples/simple_code_improvement.yaml"
    agent_config_path = project_root / "config/agent/yaml_examples/simple_code_improvement.yaml"
    template_config_path = project_root / "config/template/simple_code_improvement.yaml"
    
    # Load configurations
    print("📚 Loading configuration files...")
    job_config = load_config_file(job_config_path)
    agent_config = load_config_file(agent_config_path)
    template_config = load_config_file(template_config_path)
    
    if not all([job_config, agent_config, template_config]):
        print("❌ Failed to load one or more configuration files")
        return 1
    
    print("✅ All configuration files loaded successfully")
    
    # Call the API
    start_time = time.time()
    response_data = call_workflow_api(job_config, agent_config, template_config)
    end_time = time.time()
    
    if response_data:
        print(f"✅ API call completed in {end_time - start_time:.2f} seconds")
        print(f"📊 Response status: {response_data.get('status', 'unknown')}")
        
        # Print response summary
        if response_data.get('status') == 'completed':
            print("🎉 Workflow completed successfully!")
            if response_data.get('output_file'):
                print(f"📄 Output file: {response_data['output_file']}")
            if response_data.get('json_file'):
                print(f"📋 JSON file: {response_data['json_file']}")
            if response_data.get('events_generated'):
                print(f"📨 Events generated: {response_data['events_generated']}")
            if response_data.get('response_length'):
                print(f"📏 Response length: {response_data['response_length']} characters")
        else:
            print(f"⚠️  Workflow status: {response_data.get('status', 'unknown')}")
            if response_data.get('error_message'):
                print(f"❌ Error: {response_data['error_message']}")
        
        # Save response to file
        output_file = project_root / "api/example_response.json"
        save_response_to_file(response_data, output_file)
        
        # If execution results are available, save them separately
        if response_data.get('execution_results'):
            results_file = project_root / "api/execution_results.json"
            try:
                with open(results_file, 'w') as f:
                    json.dump(response_data['execution_results'], f, indent=2)
                print(f"📊 Execution results saved to: {results_file}")
            except Exception as e:
                print(f"❌ Error saving execution results: {e}")
        
        return 0
    else:
        print("❌ API call failed")
        return 1

if __name__ == "__main__":
    exit(main())