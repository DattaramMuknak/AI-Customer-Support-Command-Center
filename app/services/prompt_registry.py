"""
Prompt Registry — centralizes and versions all agent system prompts.

In real MLOps practice, prompts are treated like model artifacts: versioned,
tracked, and A/B tested. This registry gives each prompt a version tag that
gets logged alongside MLflow runs, so you can correlate quality metrics with
*which version of the prompt* produced them.
"""

from dataclasses import dataclass

from app.agents.billing_agent import BILLING_SYSTEM_PROMPT
from app.agents.escalation_agent import ESCALATION_SYSTEM_PROMPT
from app.agents.knowledge_agent import KNOWLEDGE_SYSTEM_PROMPT
from app.agents.router_agent import ROUTER_SYSTEM_PROMPT
from app.agents.support_agent import SUPPORT_SYSTEM_PROMPT


@dataclass(frozen=True)
class PromptVersion:
    name: str
    version: str
    template: str


# Bump the version string any time a prompt template is edited.
# This creates an audit trail between prompt changes and downstream quality shifts.
PROMPT_REGISTRY: dict[str, PromptVersion] = {
    "router": PromptVersion(
        name="router", version="v1.0", template=ROUTER_SYSTEM_PROMPT
    ),
    "knowledge": PromptVersion(
        name="knowledge", version="v1.0", template=KNOWLEDGE_SYSTEM_PROMPT
    ),
    "support": PromptVersion(
        name="support", version="v1.0", template=SUPPORT_SYSTEM_PROMPT
    ),
    "billing": PromptVersion(
        name="billing", version="v1.0", template=BILLING_SYSTEM_PROMPT
    ),
    "escalation": PromptVersion(
        name="escalation", version="v1.0", template=ESCALATION_SYSTEM_PROMPT
    ),
}


def get_prompt_version(agent_name: str) -> str:
    """Return the version tag for a given agent's current prompt — logged with every run."""
    entry = PROMPT_REGISTRY.get(agent_name)
    return entry.version if entry else "unknown"


def get_all_prompt_versions() -> dict[str, str]:
    """Snapshot of all current prompt versions — useful to log once per deployment."""
    return {name: pv.version for name, pv in PROMPT_REGISTRY.items()}
