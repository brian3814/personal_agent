import os
from typing import Optional
from langfuse import Langfuse
from langfuse.decorators import observe
from functools import wraps


class TracingManager:
    """Manages Langfuse tracing for the personal agent system"""
    
    def __init__(self):
        self.langfuse_client: Optional[Langfuse] = None
        self.enabled = False
        self._initialize()
    
    def _initialize(self):
        """Initialize Langfuse client if environment variables are present"""
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        if public_key and secret_key:
            try:
                self.langfuse_client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host
                )
                self.enabled = True
                print(f"Langfuse tracing initialized with host: {host}")
            except Exception as e:
                print(f"Failed to initialize Langfuse: {e}")
                self.enabled = False
        else:
            print("Langfuse environment variables not found. Tracing disabled.")
    
    def trace_llm_call(self, name: str = "llm_call"):
        """Decorator to trace LLM calls"""
        def decorator(func):
            if not self.enabled:
                return func
            
            @observe(name=name)
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            
            @observe(name=name)
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def create_trace(self, name: str, input_data: dict = None, user_id: str = None):
        """Create a new trace"""
        if not self.enabled:
            return None
        
        return self.langfuse_client.trace(
            name=name,
            input=input_data,
            user_id=user_id
        )
    
    def create_span(self, trace_id: str, name: str, input_data: dict = None):
        """Create a span within a trace"""
        if not self.enabled:
            return None
        
        return self.langfuse_client.span(
            trace_id=trace_id,
            name=name,
            input=input_data
        )
    
    def log_generation(self, trace_id: str, name: str, input_data: dict = None, 
                      output_data: dict = None, model: str = None, usage: dict = None):
        """Log a generation event"""
        if not self.enabled:
            return None
        
        return self.langfuse_client.generation(
            trace_id=trace_id,
            name=name,
            input=input_data,
            output=output_data,
            model=model,
            usage=usage
        )
    
    def flush(self):
        """Flush any pending traces"""
        if self.enabled and self.langfuse_client:
            self.langfuse_client.flush()


# Global tracing manager instance
tracing_manager = TracingManager()

# Export convenience functions
trace_llm_call = tracing_manager.trace_llm_call
create_trace = tracing_manager.create_trace
create_span = tracing_manager.create_span
log_generation = tracing_manager.log_generation
flush_traces = tracing_manager.flush