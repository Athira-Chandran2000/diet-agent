"""Unified LLM factory supporting multiple FREE providers."""
from config import LLM_PROVIDER, GROQ_API_KEY, GOOGLE_API_KEY, GROQ_MODEL, GEMINI_MODEL, OLLAMA_MODEL


def get_llm(temperature: float = 0.2):
    """Return an LLM instance based on configured provider.
    Switch providers by changing LLM_PROVIDER in .env - no code changes!"""
    
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL,
            temperature=temperature,
            api_key=GROQ_API_KEY,
            max_tokens=2048,
        )
    
    elif LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=temperature,
            google_api_key=GOOGLE_API_KEY,
            max_output_tokens=2048,
        )
    
    elif LLM_PROVIDER == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=OLLAMA_MODEL,
            temperature=temperature,
        )
    
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")


def get_llm_with_tools(tools: list, temperature: float = 0.2):
    """Return LLM with tools bound - works across providers."""
    llm = get_llm(temperature)
    return llm.bind_tools(tools)