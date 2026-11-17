"""Single place to choose the LLM. Everything else just calls get_llm()."""
import os

from dotenv import load_dotenv

load_dotenv()


def get_llm(temperature: float = 0):
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    model = os.getenv("LLM_MODEL")

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model or "claude-sonnet-4-5", temperature=temperature)

    if provider == "openai":  # also covers any OpenAI-compatible server via OPENAI_BASE_URL
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model or "gpt-4o-mini",
            temperature=temperature,
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )

    raise ValueError(f"Unknown LLM_PROVIDER={provider!r} (use 'anthropic' or 'openai')")
