"""SSE stream formatting for AI token output."""
import json


class StreamManager:
    @staticmethod
    def format_sse(token: str, event: str = "message") -> str:
        payload = json.dumps({"token": token})
        return f"event: {event}\ndata: {payload}\n\n"

    @staticmethod
    def status_event(message: str) -> str:
        return f"event: status\ndata: {message}\n\n"

    @staticmethod
    def error_event(message: str) -> str:
        payload = json.dumps({"error": message})
        return f"event: error\ndata: {payload}\n\n"

    @staticmethod
    def done_event() -> str:
        return "data: [DONE]\n\n"

    @staticmethod
    def cached_event(cache_data: dict) -> str:
        payload = json.dumps({"cached": True, "data": cache_data})
        return f"event: cached\ndata: {payload}\n\n"
