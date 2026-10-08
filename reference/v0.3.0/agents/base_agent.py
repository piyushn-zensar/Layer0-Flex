"""
Shared LLM-calling layer used by every agent.

Design intent: no agent module below ever calls an HTTP endpoint or a
mock function directly. They all call `call_llm_json(prompt, mock_fn,
*mock_args)`. This is the one seam in the codebase where "how do we get
a model's output" is decided — swapping backends (llama.cpp today,
vLLM or a different local model tomorrow, or pointing at a hosted API
for a quick showcase) means editing this file only, never the agents.
"""
import json
import re
import requests

from config import settings


class LLMCallError(Exception):
    pass


def _extract_json(raw_text: str) -> dict:
    """Model output is sometimes wrapped in markdown fences or preceded
    by stray commentary even when instructed not to. This extracts the
    first well-formed JSON object found, rather than assuming the raw
    text is clean JSON."""
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise LLMCallError(f"Could not parse JSON from model output:\n{raw_text[:500]}")


class LlamaCppLLMClient:
    """Calls a local llama.cpp server (llama-server) via its
    OpenAI-compatible /v1/chat/completions endpoint."""

    def __init__(self):
        self.base_url = settings.LLAMA_CPP_SERVER_URL.rstrip("/")
        self.model = settings.LLAMA_CPP_MODEL_NAME
        self.timeout = settings.LLAMA_CPP_TIMEOUT_S
        self.max_tokens = settings.LLAMA_CPP_MAX_TOKENS
        self.temperature = settings.LLAMA_CPP_TEMPERATURE

    def chat(self, prompt: str) -> str:
        try:
            resp = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise LLMCallError(
                f"Could not reach llama.cpp server at {self.base_url}. "
                f"Is `llama-server` running? (see scripts/03_start_llm_server.sh) "
                f"Underlying error: {e}"
            )
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise LLMCallError(f"Unexpected llama.cpp server response shape: {data}") from e


def call_llm_json(prompt: str, mock_fn=None, *mock_args, **mock_kwargs) -> dict:
    """The single entry point every agent uses to get structured output.

    - LLM_MODE=llama_cpp: sends `prompt` to the local model, parses JSON
      from the response.
    - LLM_MODE=mock: bypasses the network entirely and calls `mock_fn`,
      which must return a dict of the same shape the real prompt asks
      the model to produce. Mock functions are input-driven (they read
      the actual RFP/requirements passed in), not hardcoded constants,
      so orchestration logic can be genuinely exercised and tested
      without a running model.
    """
    if settings.LLM_MODE == "mock":
        if mock_fn is None:
            raise LLMCallError("LLM_MODE=mock but no mock_fn was provided for this call.")
        return mock_fn(*mock_args, **mock_kwargs)

    if settings.LLM_MODE == "llama_cpp":
        client = LlamaCppLLMClient()
        raw = client.chat(prompt)
        return _extract_json(raw)

    raise LLMCallError(f"Unknown LLM_MODE '{settings.LLM_MODE}'. Expected 'llama_cpp' or 'mock'.")
