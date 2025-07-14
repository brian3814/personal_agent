class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def cleanup(self):
        raise NotImplementedError("Subclasses must implement cleanup method")