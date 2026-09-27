import json
from pathlib import Path
from zforge.orchestration import execute_workflow

def main():
    root = Path(__file__).resolve().parent.parent.parent
    ws = root / "workspace" / "synthetic-banking"
    result = execute_workflow(ws)
    json_str = json.dumps(result, indent=2)
    
    # Save cache file in reports directory
    reports_dir = ws / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_file = reports_dir / "workflow-result.json"
    out_file.write_text(json_str, encoding="utf-8")
    
    print(json_str)

if __name__ == "__main__":
    main()
