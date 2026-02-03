import os
import shutil
from typing import Dict, Any

class FileSystemTool:
    """Tool for agents to manage files."""
    
    def read_file(self, filepath: str, limit: int = 1000) -> Dict[str, Any]:
        """Read file contents."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "status": "success",
                "path": filepath,
                "content": content[:limit * 100],  # Limit chars
                "size": len(content)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def write_file(self, filepath: str, content: str, backup: bool = True) -> Dict[str, Any]:
        """Write file with optional backup."""
        try:
            if backup and os.path.exists(filepath):
                shutil.copy2(filepath, f"{filepath}.bak")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {"status": "success", "path": filepath, "bytes_written": len(content)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def list_directory(self, path: str) -> Dict[str, Any]:
        """List directory contents."""
        try:
            entries = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                entries.append({
                    "name": item,
                    "is_directory": os.path.isdir(full_path),
                    "size": os.path.getsize(full_path),
                    "modified": os.path.getmtime(full_path)
                })
            return {"status": "success", "path": path, "entries": entries}
        except Exception as e:
            return {"status": "error", "error": str(e)}