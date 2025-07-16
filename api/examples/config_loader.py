#!/usr/bin/env python3
"""
Configuration loader script that generates API payload JSON for the simple_code_improvement workflow.
This script reads the existing configuration files and creates a JSON payload ready for the API server.
"""

import json
import sys
import yaml
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def load_config_file(file_path):
    """Load YAML configuration file and parse it into a Python object."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def create_api_payload(job_name: str = "simple_code_improvement"):
    """Create API payload from given job names."""
    
    # Configuration file paths
    job_config_path = project_root / f"config/job/yaml_examples/{job_name}.yaml"
    agent_config_path = project_root / f"config/agent/yaml_examples/{job_name}.yaml"
    template_config_path = project_root / f"config/template/{job_name}.yaml"
    
    print("🔍 Loading configuration files...")
    print(f"📄 Job config: {job_config_path}")
    print(f"🤖 Agent config: {agent_config_path}")
    print(f"📝 Template config: {template_config_path}")
    
    # Load configurations
    job_config = load_config_file(job_config_path)
    agent_config = load_config_file(agent_config_path)
    template_config = load_config_file(template_config_path)
    
    if not all([job_config, agent_config, template_config]):
        print("❌ Failed to load one or more configuration files")
        return None
    
    print("✅ All configuration files loaded successfully")
    print(f"📊 Job config keys: {list(job_config.keys())}")
    print(f"📊 Agent config keys: {list(agent_config.keys())}")
    print(f"📊 Template config keys: {list(template_config.keys())}")
    
    # Create API payload
    payload = {
        "job_config": job_config,
        "agent_config": agent_config,
        "template_config": template_config
    }
    
    return payload

def save_payload_to_file(payload, output_file):
    """Save the API payload to a JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"💾 API payload saved to: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving payload: {e}")
        return False

def main():
    """Main function to generate API payload."""
    print("🎯 Simple Code Improvement API Payload Generator")
    print("=" * 60)
    
    # Create payload
    job_name = sys.argv[1]
    payload = create_api_payload(job_name)
    if not payload:
        return 1
    
    # Save to file
    output_file = Path(__file__).parent / f"{job_name}.json"
    success = save_payload_to_file(payload, output_file)
    
    if success:
        print("\n🎉 Payload generated successfully!")
        print(f"📁 File location: {output_file}")
        print("\n📡 You can now use this payload to call the API:")
        print("curl -X POST http://localhost:8000/workflow/run \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d @{output_file}")
        print("\nOr use it in your Python script:")
        print("import requests")
        print("import json")
        print(f"with open('{output_file}', 'r') as f:")
        print("    payload = json.load(f)")
        print("response = requests.post('http://localhost:8000/workflow/run', json=payload)")
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())