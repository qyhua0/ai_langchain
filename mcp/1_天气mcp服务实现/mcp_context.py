class MCPContext:
    """
    MCP 风格的上下文协议封装
    """

    def __init__(self, model: str, operation: str, params: dict):
        self.model = model
        self.operation = operation
        self.params = params

    def to_dict(self):
        return {
            "model": self.model,
            "operation": self.operation,
            "params": self.params
        }
