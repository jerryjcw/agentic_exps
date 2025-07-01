"""
Test configuration and fixtures for pytest compatibility.

This file can be used if switching to pytest in the future.
Currently using unittest framework.
"""

import os
import sys

# Add project paths for test imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wrapper_dir = os.path.join(project_root, 'wrapper')
basics_dir = os.path.join(project_root, 'basics')

for path in [project_root, wrapper_dir, basics_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)