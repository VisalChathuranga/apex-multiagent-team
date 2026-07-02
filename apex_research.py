import os
import subprocess
import json
from pathlib import Path

# Try to find the local vibe_research package
try:
    import vibe_research
    HAS_VIBE = True
except ImportError:
    HAS_VIBE = False

def apex_deep_research(topic: str, depth: str = "standard", mode: str = "subscription") -> str:
    """
    Run an autonomous multi-agent research crew on a specific topic.
    Returns the absolute path to the generated Markdown report.
    """
    if not HAS_VIBE:
        return "Error: vibe_research package is not found or not installed in the current environment."
    
    # We will invoke the vibe-research CLI as a subprocess to keep it isolated
    # and to ensure it runs fully headless without event loop conflicts.
    env = os.environ.copy()
    
    # Ensure APEX workspace is used for reports
    reports_dir = Path("d:/apex-team/reports")
    reports_dir.mkdir(exist_ok=True)
    
    cmd = [
        "python", "-c", "import sys; from vibe_research.cli import main; sys.exit(main())",
        "run", topic,
        "--no-tui", 
        "--quiet",
        "--depth", depth,
        "--mode", mode,
        "--output-dir", str(reports_dir)
    ]
    
    try:
        # Run the command and capture output
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True, encoding="utf-8")
        # The quiet mode outputs paths like: "✔ Report: d:\apex-team\reports\topic.md"
        output = result.stdout
        report_path = None
        for line in output.splitlines():
            if line.startswith("✔ Report:"):
                report_path = line.split("✔ Report:")[1].strip()
                break
        
        if report_path and os.path.exists(report_path):
            return f"Research completed successfully. Report saved at: {report_path}"
        else:
            return f"Research completed, but could not determine report path. Output: {output}"
    except subprocess.CalledProcessError as e:
        return f"Research failed with exit code {e.returncode}.\nStdout: {e.stdout}\nStderr: {e.stderr}"
