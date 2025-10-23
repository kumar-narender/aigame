"""Base Agent class for all agents"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        Initialize the base agent.

        Args:
            name: Name of the agent
            config: Configuration dictionary for the agent
        """
        self.name = name
        self.config = config or {}
        self.status = "initialized"

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        Execute the agent's main task.

        Returns:
            The result of the agent's execution
        """
        pass

    def get_status(self) -> str:
        """
        Get the current status of the agent.

        Returns:
            Current status as a string
        """
        return self.status

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update the agent's configuration.

        Args:
            config: New configuration dictionary
        """
        self.config.update(config)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', status='{self.status}')"
