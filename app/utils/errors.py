class ProviderError(Exception):
    """Raised when a provider call fails."""


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is invalid or incomplete."""
