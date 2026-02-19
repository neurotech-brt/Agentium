"""
PromptTemplateManager - Model-specific prompt templates for different providers.
Optimizes prompts based on provider strengths and model capabilities.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from backend.models.entities.user_config import ProviderType


class TaskCategory(Enum):
    """Categories of tasks requiring different prompt strategies."""
    CODE = "code"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    CONVERSATION = "conversation"
    SYSTEM = "system"
    REASONING = "reasoning"


@dataclass
class PromptTemplate:
    """A prompt template with system and user formatting."""
    name: str
    system_template: str
    user_prefix: str = ""
    user_suffix: str = ""
    stop_sequences: List[str] = None
    requires_cot: bool = False  # Chain-of-thought
    max_tokens_multiplier: float = 1.0
    
    def format(self, system_vars: Dict[str, Any], user_message: str) -> tuple:
        """Format the template with variables."""
        system = self.system_template.format(**system_vars)
        user = f"{self.user_prefix}{user_message}{self.user_suffix}"
        return system, user


class PromptTemplateManager:
    """
    Manages provider and model-specific prompt templates.
    Each provider has different optimal prompting strategies.
    """
    
    # Provider-specific base templates
    PROVIDER_TEMPLATES: Dict[ProviderType, Dict[TaskCategory, PromptTemplate]] = {
        ProviderType.OPENAI: {
            TaskCategory.CODE: PromptTemplate(
                name="openai_code",
                system_template="""You are an expert software engineer. {role_context}

Guidelines:
- Write clean, well-documented code
- Follow best practices and security standards
- Include error handling
- Use modern language features where appropriate

Current task: {mission_statement}""",
                user_prefix="",
                user_suffix="\n\nPlease provide the complete, working code solution.",
                requires_cot=False,
                max_tokens_multiplier=1.5
            ),
            TaskCategory.ANALYSIS: PromptTemplate(
                name="openai_analysis",
                system_template="""You are a thorough analytical assistant. {role_context}

Analysis Framework:
1. Identify key components
2. Examine relationships and dependencies
3. Evaluate strengths and weaknesses
4. Provide actionable insights

{mission_statement}""",
                requires_cot=True,
                max_tokens_multiplier=1.2
            ),
            TaskCategory.CREATIVE: PromptTemplate(
                name="openai_creative",
                system_template="""You are a creative assistant with expertise in {specialization}. {role_context}

Creative Guidelines:
- Be original and engaging
- Consider the target audience
- Maintain consistent tone and style
- Iterate on ideas when helpful

{mission_statement}""",
                max_tokens_multiplier=1.3
            ),
            TaskCategory.SYSTEM: PromptTemplate(
                name="openai_system",
                system_template="""{mission_statement}

{role_context}
{behavioral_rules}""",
                max_tokens_multiplier=1.0
            ),
        },
        
        ProviderType.ANTHROPIC: {
            TaskCategory.CODE: PromptTemplate(
                name="anthropic_code",
                system_template="""You are Claude, an expert coding assistant. {role_context}

When writing code:
- Prioritize correctness and safety
- Explain your reasoning before coding
- Include comprehensive comments
- Consider edge cases and error handling

{mission_statement}""",
                user_prefix="<user_request>\n",
                user_suffix="\n</user_request>\n\nProvide your solution with explanation first, then the code.",
                requires_cot=True,
                max_tokens_multiplier=1.6
            ),
            TaskCategory.ANALYSIS: PromptTemplate(
                name="anthropic_analysis",
                system_template="""You are Claude, an analytical assistant skilled at deep reasoning. {role_context}

Approach:
- Break down complex problems step by step
- Consider multiple perspectives
- Acknowledge uncertainty where appropriate
- Provide well-reasoned conclusions

{mission_statement}""",
                user_prefix="<analysis_request>\n",
                user_suffix="\n</analysis_request>",
                requires_cot=True,
                max_tokens_multiplier=1.4
            ),
            TaskCategory.CREATIVE: PromptTemplate(
                name="anthropic_creative",
                system_template="""You are Claude, a thoughtful creative assistant. {role_context}

Creative Approach:
- Consider the deeper meaning and impact
- Balance creativity with coherence
- Be mindful of tone and audience
- Revise and improve iteratively

{mission_statement}""",
                user_prefix="<creative_task>\n",
                user_suffix="\n</creative_task>",
                max_tokens_multiplier=1.3
            ),
            TaskCategory.SYSTEM: PromptTemplate(
                name="anthropic_system",
                system_template="""{mission_statement}

{role_context}
{behavioral_rules}""",
                max_tokens_multiplier=1.0
            ),
        },
        
        ProviderType.GROQ: {
            TaskCategory.CODE: PromptTemplate(
                name="groq_code",
                system_template="""You are a fast, efficient coding assistant. {role_context}

Requirements:
- Quick, accurate code generation
- Minimal explanation, maximum code
- Production-ready solutions
- Fast execution priority

{mission_statement}""",
                user_prefix="Code task: ",
                user_suffix="\nProvide code only, minimal comments.",
                max_tokens_multiplier=1.2
            ),
            TaskCategory.CONVERSATION: PromptTemplate(
                name="groq_chat",
                system_template="""You are a quick, helpful assistant. {role_context}
Be concise and fast. {mission_statement}""",
                max_tokens_multiplier=0.8
            ),
        },
        
        ProviderType.LOCAL: {
            TaskCategory.CODE: PromptTemplate(
                name="local_code",
                system_template="""You are a coding assistant running on local hardware. {role_context}

Focus on:
- Simple, efficient solutions
- Minimal resource usage
- Clear, straightforward code
- Working within local constraints

{mission_statement}""",
                max_tokens_multiplier=1.0
            ),
            TaskCategory.CONVERSATION: PromptTemplate(
                name="local_chat",
                system_template="""You are a helpful local AI assistant. {role_context}
Provide helpful responses efficiently. {mission_statement}""",
                max_tokens_multiplier=0.7
            ),
        },
        
        # Default templates for other providers
        ProviderType.GEMINI: {},
        ProviderType.MISTRAL: {},
        ProviderType.TOGETHER: {},
        ProviderType.MOONSHOT: {},
        ProviderType.DEEPSEEK: {},
        ProviderType.CUSTOM: {},
        ProviderType.OPENAI_COMPATIBLE: {},
    }
    
    # Model-specific overrides (for fine-tuned or special models)
    MODEL_OVERRIDES: Dict[str, Dict[TaskCategory, PromptTemplate]] = {
        "claude-3-opus": {
            TaskCategory.CODE: PromptTemplate(
                name="opus_code",
                system_template="""You are Claude 3 Opus, the most capable coding assistant. {role_context}

Coding Standards:
- Architecturally sound solutions
- Comprehensive error handling
- Security-first approach
- Extensive inline documentation
- Test considerations

{mission_statement}""",
                requires_cot=True,
                max_tokens_multiplier=2.0
            ),
        },
        "gpt-4-turbo": {
            TaskCategory.SYSTEM: PromptTemplate(
                name="gpt4_system",
                system_template="""{mission_statement}

{role_context}
{behavioral_rules}

You are GPT-4 Turbo, optimized for both speed and quality.""",
                max_tokens_multiplier=1.2
            ),
        },
        "llama-3.1-70b": {
            TaskCategory.CODE: PromptTemplate(
                name="llama_code",
                system_template="""You are a helpful AI assistant specialized in coding. {role_context}

Write high-quality, efficient code following best practices.

{mission_statement}""",
                max_tokens_multiplier=1.3
            ),
        },
    }
    
    def __init__(self):
        self._cache: Dict[str, PromptTemplate] = {}
    
    def get_template(
        self,
        provider: ProviderType,
        model_name: str,
        task_category: TaskCategory,
        agent_tier: int = 3
    ) -> PromptTemplate:
        """
        Get the best template for provider + model + task combination.
        
        Hierarchy:
        1. Model-specific override
        2. Provider-specific for task
        3. Provider-specific SYSTEM (fallback)
        4. Generic default
        """
        cache_key = f"{provider.value}:{model_name}:{task_category.value}:{agent_tier}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 1. Check model-specific override
        model_key = model_name.lower().replace("-", "_")
        for key, templates in self.MODEL_OVERRIDES.items():
            if key in model_name.lower() and task_category in templates:
                template = templates[task_category]
                self._cache[cache_key] = template
                return template
        
        # 2. Check provider-specific for task
        provider_templates = self.PROVIDER_TEMPLATES.get(provider, {})
        if task_category in provider_templates:
            template = provider_templates[task_category]
            self._cache[cache_key] = template
            return template
        
        # 3. Fallback to SYSTEM template for provider
        if TaskCategory.SYSTEM in provider_templates:
            template = provider_templates[TaskCategory.SYSTEM]
            self._cache[cache_key] = template
            return template
        
        # 4. Generic default
        default = PromptTemplate(
            name="generic_default",
            system_template="{mission_statement}\n\n{role_context}\n{behavioral_rules}",
            max_tokens_multiplier=1.0
        )
        self._cache[cache_key] = default
        return default
    
    def classify_task(self, description: str, task_type: Optional[str] = None) -> TaskCategory:
        """Classify a task into a category for template selection."""
        desc_lower = description.lower()
        
        # Code detection
        code_keywords = ['code', 'program', 'function', 'script', 'python', 'javascript', 
                        'debug', 'error', 'implement', 'class', 'api', 'database', 'sql']
        if any(kw in desc_lower for kw in code_keywords) or task_type in ['code', 'coding']:
            return TaskCategory.CODE
        
        # Analysis detection
        analysis_keywords = ['analyze', 'analysis', 'research', 'investigate', 'evaluate',
                           'compare', 'assess', 'review', 'study', 'examine']
        if any(kw in desc_lower for kw in analysis_keywords) or task_type in ['analysis', 'research']:
            return TaskCategory.ANALYSIS
        
        # Creative detection
        creative_keywords = ['write', 'create', 'story', 'content', 'draft', 'design',
                           'creative', 'blog', 'article', 'marketing', 'copy']
        if any(kw in desc_lower for kw in creative_keywords) or task_type in ['creative', 'writing']:
            return TaskCategory.CREATIVE
        
        # Reasoning detection
        reasoning_keywords = ['reason', 'logic', 'solve', 'problem', 'math', 'calculate',
                            'prove', 'deduce', 'infer']
        if any(kw in desc_lower for kw in reasoning_keywords):
            return TaskCategory.REASONING
        
        # Default to conversation
        return TaskCategory.CONVERSATION
    
    def build_system_prompt(
        self,
        provider: ProviderType,
        model_name: str,
        task_description: str,
        agent_ethos: Any,
        agent_tier: int = 3
    ) -> tuple:
        """
        Build a complete system prompt using templates.
        
        Returns: (system_prompt, max_tokens_multiplier, requires_cot)
        """
        # Classify the task
        task_category = self.classify_task(task_description)
        
        # Get appropriate template
        template = self.get_template(provider, model_name, task_category, agent_tier)
        
        # Build template variables
        role_context = self._build_role_context(agent_tier, agent_ethos)
        
        behavioral_rules = ""
        if agent_ethos and hasattr(agent_ethos, 'behavioral_rules'):
            import json
            try:
                rules = json.loads(agent_ethos.behavioral_rules) if agent_ethos.behavioral_rules else []
                behavioral_rules = "\n".join(f"- {r}" for r in rules[:10])
            except:
                pass
        
        system_vars = {
            "mission_statement": getattr(agent_ethos, 'mission_statement', "You are an AI assistant."),
            "role_context": role_context,
            "behavioral_rules": behavioral_rules,
            "specialization": getattr(agent_ethos, 'specialization', 'general assistance'),
        }
        
        system_prompt, _ = template.format(system_vars, "")
        
        return (
            system_prompt,
            template.max_tokens_multiplier,
            template.requires_cot
        )
    
    def _build_role_context(self, agent_tier: int, agent_ethos: Any) -> str:
        """Build role context based on agent tier."""
        tier_roles = {
            0: "You are the Head of Council with ultimate authority and comprehensive system access.",
            1: "You are a Council Member with deliberation and oversight responsibilities.",
            2: "You are a Lead Agent coordinating task execution and team management.",
            3: "You are a Task Agent focused on efficient execution of assigned tasks.",
        }
        return tier_roles.get(agent_tier, "You are an AI assistant in the Agentium system.")
    
    def get_provider_recommendations(self, task_description: str) -> List[tuple]:
        """
        Get provider recommendations for a task.
        Returns list of (provider, confidence_score) tuples.
        """
        category = self.classify_task(task_description)
        
        recommendations = []
        
        # Code: Claude-3 Opus or GPT-4 best
        if category == TaskCategory.CODE:
            recommendations = [
                (ProviderType.ANTHROPIC, 0.95),
                (ProviderType.OPENAI, 0.90),
                (ProviderType.GROQ, 0.75),
                (ProviderType.LOCAL, 0.60),
            ]
        # Analysis: Claude best for deep reasoning
        elif category == TaskCategory.ANALYSIS:
            recommendations = [
                (ProviderType.ANTHROPIC, 0.95),
                (ProviderType.OPENAI, 0.88),
                (ProviderType.DEEPSEEK, 0.80),
                (ProviderType.GROQ, 0.70),
            ]
        # Creative: GPT-4 or Claude
        elif category == TaskCategory.CREATIVE:
            recommendations = [
                (ProviderType.OPENAI, 0.92),
                (ProviderType.ANTHROPIC, 0.90),
                (ProviderType.MOONSHOT, 0.75),
                (ProviderType.GROQ, 0.65),
            ]
        # Speed: Groq best
        elif category == TaskCategory.CONVERSATION:
            recommendations = [
                (ProviderType.GROQ, 0.95),
                (ProviderType.OPENAI, 0.85),
                (ProviderType.GROQ, 0.80),
                (ProviderType.LOCAL, 0.70),
            ]
        else:
            recommendations = [
                (ProviderType.OPENAI, 0.90),
                (ProviderType.ANTHROPIC, 0.88),
                (ProviderType.GROQ, 0.80),
                (ProviderType.LOCAL, 0.65),
            ]
        
        return recommendations


# Global instance
prompt_template_manager = PromptTemplateManager()