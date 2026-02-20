from typing import Dict, Any, Callable
from backend.tools.browser_tool import BrowserTool
from backend.tools.file_tool import FileSystemTool
from backend.tools.shell_tool import ShellTool

class ToolRegistry:
    """Registry of available tools for agents."""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Register all available tools."""
        
        # Browser Tool
        browser = BrowserTool()
        self.register_tool(
            name="browser_control",
            description="Control web browser for navigation, form filling, and data extraction",
            function=browser.navigate,
            parameters={
                "url": {"type": "string", "description": "URL to navigate to"}
            },
            authorized_tiers=["0xxxx", "1xxxx"]  # Head and Council only
        )
        
        self.register_tool(
            name="browser_screenshot",
            description="Take screenshot of current page",
            function=browser.screenshot,
            parameters={
                "path": {"type": "string", "description": "Save path for screenshot"}
            }
        )
        
        # File Tool
        file_tool = FileSystemTool()
        self.register_tool(
            name="read_file",
            description="Read file contents from host filesystem",
            function=file_tool.read_file,
            parameters={
                "filepath": {"type": "string", "description": "Absolute file path"},
                "limit": {"type": "integer", "description": "Max characters to read"}
            },
            authorized_tiers=["0xxxx", "1xxxx", "2xxxx"]  # Head, Council, Lead
        )
        
        self.register_tool(
            name="write_file",
            description="Write content to file (Head only)",
            function=file_tool.write_file,
            parameters={
                "filepath": {"type": "string", "description": "Absolute file path"},
                "content": {"type": "string", "description": "Content to write"}
            },
            authorized_tiers=["0xxxx"]  # Head only for security
        )
        
        # Shell Tool
        shell_tool = ShellTool()
        self.register_tool(
            name="execute_command",
            description="Execute shell command on host system",
            function=shell_tool.execute,
            parameters={
                "command": {"type": "array", "description": "Command and args as list"},
                "timeout": {"type": "integer", "description": "Timeout in seconds"}
            },
            authorized_tiers=["0xxxx", "1xxxx"]  # Head and Council
        )
    
    def register_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Any],
        authorized_tiers: list = None
    ):
        """Register a tool in the registry."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "function": function,
            "parameters": parameters,
            "authorized_tiers": authorized_tiers or []
        }
    
    def get_tool(self, name: str) -> Dict[str, Any]:
        """Get tool by name."""
        return self.tools.get(name)
    
    def list_tools(self, agent_tier: str) -> Dict[str, Any]:
        """List all tools available to a specific agent tier."""
        available = {}
        for name, tool in self.tools.items():
            if agent_tier in tool["authorized_tiers"]:
                available[name] = {
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
        return available
    
    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        tool = self.get_tool(name)
        if not tool:
            return {"status": "error", "error": f"Tool '{name}' not found"}
        
        try:
            result = tool["function"](**kwargs)
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_tool_function(self, name: str) -> Callable:
        """
        Return just the callable for a registered tool.
        Used by ToolCreationService.execute_tool() to invoke the function directly.
        Returns None if the tool does not exist.
        """
        tool = self.tools.get(name)
        return tool["function"] if tool else None

    def update_tool_function(self, name: str, function: Callable) -> bool:
        """
        Replace the callable for an existing tool (used after version update / rollback).
        Called by ToolVersioningService.approve_update() and rollback().
        Returns True if updated, False if tool not found.
        """
        if name not in self.tools:
            return False
        self.tools[name]["function"] = function
        return True

    def mark_deprecated(
        self,
        name: str,
        reason: str,
        replacement: str = None,
    ) -> bool:
        """
        Soft-mark a tool as deprecated.
        Tool remains callable but is flagged so callers can surface warnings.
        Called by ToolDeprecationService.deprecate_tool().
        Returns True if marked, False if tool not found.
        """
        if name not in self.tools:
            return False
        self.tools[name]["deprecated"] = True
        self.tools[name]["deprecation_reason"] = reason
        self.tools[name]["replacement"] = replacement
        return True

    def unmark_deprecated(self, name: str) -> bool:
        """
        Remove deprecation flag from a tool (used when restoring a deprecated tool).
        Called by ToolDeprecationService.restore_tool().
        Returns True if unmarked, False if tool not found.
        """
        if name not in self.tools:
            return False
        self.tools[name].pop("deprecated", None)
        self.tools[name].pop("deprecation_reason", None)
        self.tools[name].pop("replacement", None)
        return True

    def deregister_tool(self, name: str) -> bool:
        """
        Hard-remove a tool from the registry (used on sunset / hard removal).
        Called by ToolDeprecationService.execute_sunset().
        Returns True if removed, False if tool was not registered.
        """
        if name not in self.tools:
            return False
        del self.tools[name]
        return True


# Global registry instance
tool_registry = ToolRegistry()