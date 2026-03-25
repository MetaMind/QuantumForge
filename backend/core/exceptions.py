class QuantumForgeException(Exception):
    """Base exception for QuantumForge AI"""
    pass


class LLMException(QuantumForgeException):
    """Raised when LLM interaction fails"""
    pass


class SandboxException(QuantumForgeException):
    """Raised when code execution in sandbox fails"""
    pass


class MemoryException(QuantumForgeException):
    """Raised when memory operations fail"""
    pass


class EvolutionException(QuantumForgeException):
    """Raised when evolution operations fail"""
    pass


class AgentException(QuantumForgeException):
    """Raised when agent execution fails"""
    pass


class DistributedException(QuantumForgeException):
    """Raised when distributed execution fails"""
    pass
