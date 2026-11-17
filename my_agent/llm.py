"""Single place to choose the LLM.

On MARS the spec's env/secrets arrive as HARNESS_INFERENCE_* (OpenAI-compatible endpoint, e.g.
DigitalOcean Inference). Locally you can use those same vars, or LLM_PROVIDER=anthropic|openai.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def get_llm(temperature: float = 0):
    # MARS / any OpenAI-compatible gateway
    if os.getenv("HARNESS_INFERENCE_BASE_URL"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.environ["HARNESS_INFERENCE_MODEL"],
            base_url=os.environ["HARNESS_INFERENCE_BASE_URL"],
            api_key=os.environ["HARNESS_INFERENCE_API_KEY"],
            temperature=temperature,
            streaming=True,     # MARS keys the streamed reply off per-token events
            stream_usage=True,  # without this, custom base_urls report zero tokens
        )

    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    model = os.getenv("LLM_MODEL")
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model or "claude-sonnet-4-5", temperature=temperature)
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model or "gpt-4o-mini",
            temperature=temperature,
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            streaming=True,
            stream_usage=True,
        )
    raise ValueError(f"Unknown LLM_PROVIDER={provider!r} (use 'anthropic' or 'openai')")
