import os
import sys
import subprocess
import ast
import shutil
from google import genai
from google.genai import types

def is_valid_python(code_str):
    try:
        ast.parse(code_str)
        return True
    except SyntaxError:
        return False

def run_script(script_name):
    print(f"[Healer] Running {script_name}...")
    result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
    return result

def heal_script(script_name, error_output):
    print(f"[Healer] Detected failure in {script_name}. Asking Gemini to heal...")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[Healer] Error: GEMINI_API_KEY not found. Cannot auto-heal.")
        return False
        
    with open(script_name, 'r', encoding='utf-8') as f:
        source_code = f.read()
        
    prompt = f"""
You are an expert Python DevOps AI. 
The following Python script failed with this error traceback:
```
{error_output}
```

Here is the source code of the script:
```python
{source_code}
```

Identify the root cause of the crash (likely a web scraping HTML change, JSON structure change, or Syntax/Type error).
Provide the FULL, FIXED source code for the script so it can run successfully.
CRITICAL: Return ONLY the raw Python code. Do not include markdown formatting like ```python, do not include explanations. Just the raw text of the python script.
"""
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1
            )
        )
        
        fixed_code = response.text.strip()
        if fixed_code.startswith("```python"):
            fixed_code = fixed_code[9:]
        if fixed_code.startswith("```"):
            fixed_code = fixed_code[3:]
        if fixed_code.endswith("```"):
            fixed_code = fixed_code[:-3]
            
        fixed_code = fixed_code.strip()
        
        if not fixed_code or len(fixed_code) < 50:
            print("[Healer] AI returned code that is too short.")
            return False
            
        if not is_valid_python(fixed_code):
            print("[Healer] AI returned invalid Python syntax.")
            return False
            
        # Create backup
        backup_name = f"{script_name}.backup"
        shutil.copy2(script_name, backup_name)
        
        with open(script_name, 'w', encoding='utf-8') as f:
            f.write(fixed_code)
            
        # Compile check
        compile_result = subprocess.run([sys.executable, "-m", "py_compile", script_name], capture_output=True)
        if compile_result.returncode != 0:
            print("[Healer] AI returned code that fails py_compile. Restoring backup.")
            shutil.copy2(backup_name, script_name)
            return False
            
        print(f"[Healer] Successfully patched {script_name}. Retrying execution...")
        return True
    except Exception as e:
        print(f"[Healer] AI healing failed: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python ai_healer.py <script_to_run.py>")
        sys.exit(1)
        
    target_script = sys.argv[1]
    
    if not os.path.exists(target_script):
        print(f"[Healer] Target script {target_script} not found.")
        sys.exit(1)
        
    result = run_script(target_script)
    
    if result.returncode == 0:
        print(result.stdout)
        print("[Healer] Script executed successfully.")
        sys.exit(0)
        
    print(result.stdout)
    print(f"[Healer] Script failed with exit code {result.returncode}")
    print("Stderr:")
    print(result.stderr)
    
    # Try to heal
    success = heal_script(target_script, result.stderr)
    
    if success:
        # Retry once
        retry_result = run_script(target_script)
        if retry_result.returncode == 0:
            print(retry_result.stdout)
            print("[Healer] Script healed and executed successfully on retry!")
            sys.exit(0)
        else:
            print(retry_result.stdout)
            print("[Healer] Script failed again after healing. Restoring backup if exists.")
            backup_name = f"{target_script}.backup"
            if os.path.exists(backup_name):
                shutil.copy2(backup_name, target_script)
            print(retry_result.stderr)
            sys.exit(retry_result.returncode)
    else:
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()
