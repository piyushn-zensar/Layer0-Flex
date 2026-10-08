"""Model gateway: the ONLY place a language model is called (rule R4).

Provider: Azure OpenAI (GPT-4o deployment), structured JSON output, temperature 0.

Agents propose, people decide. Every answer is cached in data/llm_cache/<task>/<hash>.json,
keyed by task, model, system prompt, prompt and schema. The cache is committed to git, so:
  - a re-run returns the frozen first-pass answer instead of a new one (rule R2);
  - teammates and the demo run with LLM_PROVIDER=mock and no API key;
  - changing a prompt or schema changes the key, so stale answers are never reused.
"""
import hashlib
import json

from app.core import config


class LLMUnavailable(RuntimeError):
    """No cached answer and no provider (or the model refused). Callers must surface this, never guess."""


def complete_json(task: str, system: str, prompt: str, schema: dict) -> dict:
    key = hashlib.sha256(
        json.dumps([task, config.LLM_MODEL, system, prompt, schema], sort_keys=True).encode()
    ).hexdigest()[:24]
    path = config.LLM_CACHE / task / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text("utf-8"))["output"]
    if config.LLM_PROVIDER != "azure":
        raise LLMUnavailable(f"No cached answer for {task}/{key}; set LLM_PROVIDER=azure to generate it.")
    output = _azure(task, system, prompt, schema)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"task": task, "model": config.LLM_MODEL, "output": output},
                               indent=2, sort_keys=True, ensure_ascii=False), "utf-8")
    return output


def _azure(task: str, system: str, prompt: str, schema: dict) -> dict:
    from openai import AzureOpenAI  # imported here so mock mode never needs Azure settings

    client = AzureOpenAI(azure_endpoint=config.AZURE_OPENAI_ENDPOINT, api_key=config.AZURE_OPENAI_API_KEY,
                         api_version=config.AZURE_OPENAI_API_VERSION)
    response = client.chat.completions.create(
        model=config.LLM_MODEL,  # the Azure deployment name
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=16000,
        response_format={"type": "json_schema", "json_schema": {"name": task, "schema": schema, "strict": True}},
    )
    choice = response.choices[0]
    if choice.message.refusal:
        raise LLMUnavailable(f"Model refused: {choice.message.refusal}")
    if choice.finish_reason == "length":
        raise LLMUnavailable("Answer truncated at max_tokens; send a smaller chunk.")
    return json.loads(choice.message.content)
