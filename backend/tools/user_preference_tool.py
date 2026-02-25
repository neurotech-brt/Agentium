"""
User Preference Tool for Agentium.
Allows agents to read and modify user preferences with proper authorization.
"""

from typing import Any, Dict, List, Optional, Union
from backend.services.user_preference_service import UserPreferenceService, PreferenceCategory
from backend.models.database import get_db_context


class UserPreferenceTool:
    """
    Tool for agents to access and modify user preferences.
    Respects agent tier permissions and audit logging.
    """

    def __init__(self):
        self.name = "user_preference"
        self.description = "Access and modify user preferences with governance controls"

    def get_preference(
        self,
        key: str,
        agent_tier: str,
        agent_id: str,
        user_id: Optional[str] = None,
        default: Any = None
    ) -> Dict[str, Any]:
        """
        Get a preference value.
        All agents can read preferences they have access to.
        """
        try:
            with get_db_context() as db:
                service = UserPreferenceService(db)

                # Check if agent can access this preference
                accessible = service.get_agent_accessible_preferences(
                    agent_tier=agent_tier,
                    agent_id=agent_id,
                    user_id=user_id
                )

                accessible_keys = [p.key for p in accessible]

                # Check if key is accessible or is a system default
                if key not in accessible_keys and not key.startswith('system.'):
                    # Try to get system default
                    pref = service.get_preference(key, user_id=None)
                    if pref and pref.is_editable_by_agents == "Y":
                        return {
                            "status": "success",
                            "key": key,
                            "value": pref.get_value(),
                            "source": "system_default",
                            "editable": False
                        }
                    return {
                        "status": "error",
                        "error": f"Preference '{key}' not accessible by agent {agent_id} (tier {agent_tier})",
                        "accessible_categories": service._get_allowed_categories(agent_tier)
                    }

                # Get the preference
                value = service.get_value(key, user_id, default=default)

                # Find the preference object to check editability
                pref = service.get_preference(key, user_id)
                editable = False
                if pref:
                    editable = service.agent_can_modify(pref, agent_tier, agent_id)

                return {
                    "status": "success",
                    "key": key,
                    "value": value,
                    "default_used": value == default,
                    "editable": editable
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def set_preference(
        self,
        key: str,
        value: Any,
        agent_tier: str,
        agent_id: str,
        user_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set a preference value.
        Requires appropriate agent tier permissions.
        """
        try:
            with get_db_context() as db:
                service = UserPreferenceService(db)

                success, message, pref = service.set_preference_by_agent(
                    key=key,
                    value=value,
                    agent_tier=agent_tier,
                    agent_id=agent_id,
                    user_id=user_id,
                    change_reason=reason
                )

                if not success:
                    return {
                        "status": "error",
                        "error": message
                    }

                return {
                    "status": "success",
                    "key": key,
                    "value": value,
                    "message": message,
                    "preference_id": pref.agentium_id if pref else None
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def list_preferences(
        self,
        agent_tier: str,
        agent_id: str,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        include_values: bool = True
    ) -> Dict[str, Any]:
        """
        List all preferences accessible to this agent.
        """
        try:
            with get_db_context() as db:
                service = UserPreferenceService(db)

                prefs = service.get_agent_accessible_preferences(
                    agent_tier=agent_tier,
                    agent_id=agent_id,
                    user_id=user_id,
                    category=category
                )

                result = []
                for pref in prefs:
                    pref_dict = {
                        "key": pref.key,
                        "category": pref.category,
                        "scope": pref.scope,
                        "data_type": pref.data_type,
                        "editable": service.agent_can_modify(pref, agent_tier, agent_id),
                        "description": pref.description,
                    }
                    if include_values:
                        pref_dict["value"] = pref.get_value()
                    result.append(pref_dict)

                return {
                    "status": "success",
                    "count": len(result),
                    "agent_tier": agent_tier,
                    "category_filter": category,
                    "preferences": result
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def get_categories(
        self,
        agent_tier: str
    ) -> Dict[str, Any]:
        """
        Get list of categories this agent can access.
        """
        try:
            with get_db_context() as db:
                service = UserPreferenceService(db)
                categories = service._get_allowed_categories(agent_tier)

                return {
                    "status": "success",
                    "agent_tier": agent_tier,
                    "accessible_categories": categories,
                    "descriptions": {
                        PreferenceCategory.GENERAL: "General system preferences",
                        PreferenceCategory.UI: "User interface settings",
                        PreferenceCategory.NOTIFICATIONS: "Notification preferences",
                        PreferenceCategory.AGENTS: "Agent behavior settings",
                        PreferenceCategory.TASKS: "Task execution preferences",
                        PreferenceCategory.CHAT: "Chat and messaging settings",
                        PreferenceCategory.MODELS: "AI model configuration",
                        PreferenceCategory.TOOLS: "Tool execution settings",
                        PreferenceCategory.PRIVACY: "Privacy and data settings",
                        PreferenceCategory.CUSTOM: "Custom user-defined preferences",
                    }
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def bulk_update(
        self,
        preferences: Dict[str, Any],
        agent_tier: str,
        agent_id: str,
        user_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update multiple preferences at once.
        Each update is validated individually.
        """
        results = {
            "success": [],
            "failed": []
        }

        for key, value in preferences.items():
            result = self.set_preference(
                key=key,
                value=value,
                agent_tier=agent_tier,
                agent_id=agent_id,
                user_id=user_id,
                reason=reason
            )

            if result["status"] == "success":
                results["success"].append(key)
            else:
                results["failed"].append({
                    "key": key,
                    "error": result.get("error", "Unknown error")
                })

        return {
            "status": "partial_success" if results["failed"] else "success",
            "updated": len(results["success"]),
            "failed": len(results["failed"]),
            "details": results
        }

    def get_default_preferences(self) -> Dict[str, Any]:
        """Get system default preferences (read-only)."""
        return {
            "status": "success",
            "defaults": UserPreferenceService.DEFAULT_PREFERENCES,
            "note": "These are system defaults. Use get_preference/set_preference for actual values."
        }


# Singleton instance for tool registry
user_preference_tool = UserPreferenceTool()