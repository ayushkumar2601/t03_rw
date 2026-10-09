class KnowledgeBaseNotReadyError(Exception):
    pass


class LLMProviderError(Exception):
    pass


class CitationValidationError(Exception):
    pass


class InsufficientEvidenceError(Exception):
    pass
