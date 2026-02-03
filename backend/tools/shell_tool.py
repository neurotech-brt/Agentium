import subprocess
from typing import Dict, Any, List

class ShellTool:
    """Tool for agents to execute shell commands."""
    
    def execute(self, command: List[str], timeout: int = 300, cwd: str = None) -> Dict[str, Any]:
        """Execute command safely."""
        try:
            # Security: Block dangerous commands
            dangerous = ['rm -rf /', 'mkfs', 'dd if=/dev/zero', 'shutdown', 'reboot']
            cmd_str = ' '.join(command)
            if any(d in cmd_str for d in dangerous):
                return {"status": "error", "error": "Command blocked for security"}
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Command timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}