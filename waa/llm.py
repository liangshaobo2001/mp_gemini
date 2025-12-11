from typing import List, Dict, Any, Optional
import os

class LLMError(Exception):
    def __init__(self, message: str, error_type: str = "LLMError", retry_after: Optional[float] = None):
        super().__init__(message)
        self.error_type = error_type
        self.retry_after = retry_after


class LanguageModel:
    def __init__(self):
        pass

    def generate(self, messages: List[Dict[str, Any]]) -> str:
        raise NotImplementedError("Subclasses must implement this method")


class GeminiLanguageModel(LanguageModel):
    def __init__(self, model_name: str = "gemini-2.5-pro", api_key: Optional[str] = None):
        super().__init__()
        self.model_name = model_name
        self.temperature = 0.0
        self.max_tokens = 8000
        self.top_p = 1.0

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        genai.configure(api_key=self.api_key)
        # Important: pass model name positionally; 'model_name=' is not a valid kwarg
        self.client = genai.GenerativeModel(
            self.model_name,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "top_p": self.top_p,
            },
        )

    def generate(self, messages: List[Dict[str, Any]]) -> str:
        """
        Convert our internal message format to Gemini's chat history.
        roles we handle: 'system', 'user', 'assistant', 'tool'
        """
        gemini_messages: List[Dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if role in ("system", "user"):
                gemini_messages.append({"role": "user", "parts": [str(content)]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [str(content)]})
            elif role == "tool":
                tool_content = content if isinstance(content, str) else str(content)
                gemini_messages.append({"role": "user", "parts": [f"Tool result: {tool_content}"]})
            else:
                # Unknown role → treat as user to be safe
                gemini_messages.append({"role": "user", "parts": [str(content)]})

        try:
            # Use all but the last as history; last as the new user prompt (if any)
            history = gemini_messages[:-1] if len(gemini_messages) > 1 else []
            prompt = gemini_messages[-1]["parts"][0] if gemini_messages else ""

            chat = self.client.start_chat(history=history)
            response = chat.send_message(prompt)
            return getattr(response, "text", str(response))
        except Exception as e:
            # Classify errors
            error_type = "UnknownLLMError"
            message = "An unexpected error occurred while calling the LLM. Please check server logs for details."
            retry_after = None
            
            ex_name = type(e).__name__
            err_str = str(e)

            if "ResourceExhausted" in ex_name or "429" in err_str:
                error_type = "RateLimit"
                message = "Gemini rate limit exceeded for the free tier. Please wait ~60 seconds and try again, or reduce the number of requests."
                # Attempt to extract retry delay if possible, otherwise None
            
            elif "PermissionDenied" in ex_name or "403" in err_str:
                error_type = "AuthError"
                message = "Gemini API key is invalid, suspended, or unauthorized. Please check your API key and Google AI Studio project settings."

            raise LLMError(message, error_type, retry_after) from e


class MockLanguageModel(LanguageModel):
    def __init__(self, responses: Optional[List[str]] = None):
        super().__init__()
        self.responses = responses or [
            '<tool_call>{"tool": "fs.read", "arguments": {"path": "package.json"}}</tool_call>',
            "Let me check the project structure.",
            '<tool_call>{"tool": "tests.run", "arguments": {"type": "all"}}</tool_call>',
            "<terminate>",
        ]
        self.call_count = 0

    def generate(self, messages: List[Dict[str, Any]]) -> str:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response

    def reset(self):
        self.call_count = 0


def create_language_model(config: Dict[str, Any]) -> "LanguageModel":
    """
    Factory: choose the correct LLM based on config.
      - llm_type: "gemini" | "mock" (default: "mock")
      - model: e.g., "gemini-2.5-pro" (used for gemini)
    Falls back to Mock if no GEMINI_API_KEY is set.
    """
    llm_type = (config or {}).get("llm_type", "mock").lower()

    if llm_type == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return MockLanguageModel()
        model = (config or {}).get("model", "gemini-2.5-pro")
        # Match constructor signature: (model_name, api_key)
        return GeminiLanguageModel(model_name=model, api_key=api_key)

    # default / unknown → mock
    return MockLanguageModel()
