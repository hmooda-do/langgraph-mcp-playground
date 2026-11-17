"""A hand-built LangGraph: START -> summarize -> critique -> END (two LLM nodes, shared state)."""
import sys
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langgraph.graph import END, START, StateGraph

from my_agent.llm import get_llm

llm = get_llm()


class State(TypedDict):
    text: str
    summary: str
    critique: str


def summarize(state: State) -> dict:
    out = llm.invoke(f"Summarize in one sentence:\n\n{state['text']}")
    return {"summary": out.content}


def critique(state: State) -> dict:
    out = llm.invoke(f"Point out anything lost in this summary.\n\nOriginal:\n{state['text']}\n\nSummary:\n{state['summary']}")
    return {"critique": out.content}


graph = (
    StateGraph(State)
    .add_node("summarize", summarize)
    .add_node("critique", critique)
    .add_edge(START, "summarize")
    .add_edge("summarize", "critique")
    .add_edge("critique", END)
    .compile()
)

if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or (
        "LangGraph models agent workflows as graphs of nodes that read and update shared state. "
        "Edges can be conditional, enabling loops, branching, and human-in-the-loop pauses."
    )
    result = graph.invoke({"text": text})
    print("SUMMARY :", result["summary"])
    print("CRITIQUE:", result["critique"])
