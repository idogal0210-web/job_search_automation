import json
import os
import shutil

def load_state(filepath: str, default=None):
    if default is None:
        default = {}
        
    if not os.path.exists(filepath):
        return default
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default

def save_state_atomic(filepath: str, data):
    tmp_filepath = filepath + '.tmp'
    bak_filepath = filepath + '.bak'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    # Write to tmp file first
    with open(tmp_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    # Backup existing file if it exists
    if os.path.exists(filepath):
        shutil.copy2(filepath, bak_filepath)
        
    # Replace atomically
    os.replace(tmp_filepath, filepath)
