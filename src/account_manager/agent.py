"""LangGraph 기반 Self-Correction + Reflection 에이전트"""
import os
from typing import Annotated, Literal

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from .memory import read_memory
from .tools import ALL_TOOLS

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

SYSTEM_PROMPT = """당신은 사용자의 웹사이트 계정 정보를 관리하는 AI 어시스턴트입니다.
사용자가 계정 정보를 조회, 저장, 업데이트, 삭제하도록 도와주세요.

중요 규칙:
1. 비밀번호는 사용자가 명시적으로 요청할 때만 show_password=True로 tool_get_account를 호출하세요.
2. 계정 삭제 전에 반드시 사용자에게 확인을 요청하세요.
3. 새 계정 저장 시 site명, 이메일/아이디, 비밀번호, URL을 최소한 수집하세요.
4. 답변은 한국어로 하고, 정확하고 간결하게 응답하세요.
5. 불확실한 경우 사용자에게 추가 정보를 요청하세요.

현재 저장된 기억:
{memory}
"""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    reflection_count: int


def create_agent():
    llm = ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=0,
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    tool_node = ToolNode(ALL_TOOLS)

    def agent_node(state: AgentState) -> AgentState:
        memory_content = read_memory()
        system_msg = SystemMessage(content=SYSTEM_PROMPT.format(memory=memory_content))
        messages = [system_msg] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "reflection_count": state.get("reflection_count", 0)}

    def reflection_node(state: AgentState) -> AgentState:
        """답변 품질 검증 및 자기 수정"""
        reflection_count = state.get("reflection_count", 0)
        if reflection_count >= 1:
            return state

        last_ai_msg = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                last_ai_msg = msg
                break

        if not last_ai_msg:
            return state

        reflection_prompt = f"""다음 답변을 검토하세요:
---
{last_ai_msg.content}
---
이 답변이 사용자의 질문에 정확하고 완전하게 답하고 있나요?
- 누락된 정보가 있다면 보완하세요.
- 잘못된 정보가 있다면 수정하세요.
- 답변이 충분하면 그대로 유지하세요.

간결하고 정확한 최종 답변만 반환하세요."""

        memory_content = read_memory()
        system_msg = SystemMessage(content=SYSTEM_PROMPT.format(memory=memory_content))
        reflection_msg = HumanMessage(content=reflection_prompt)
        messages = [system_msg] + state["messages"] + [reflection_msg]

        llm = ChatOllama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, temperature=0)
        refined = llm.invoke(messages)

        # 반성 결과가 의미있게 다르면 교체
        if refined.content and refined.content != last_ai_msg.content:
            new_messages = []
            replaced = False
            for msg in state["messages"]:
                if msg is last_ai_msg and not replaced:
                    new_messages.append(AIMessage(content=refined.content))
                    replaced = True
                else:
                    new_messages.append(msg)
            return {"messages": new_messages, "reflection_count": reflection_count + 1}

        return {"messages": state["messages"], "reflection_count": reflection_count + 1}

    def should_continue(state: AgentState) -> Literal["tools", "reflect", "end"]:
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        reflection_count = state.get("reflection_count", 0)
        if reflection_count < 1:
            return "reflect"
        return "end"

    def after_tools(state: AgentState) -> Literal["agent"]:
        return "agent"

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("reflect", reflection_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "reflect": "reflect", "end": END},
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("reflect", END)

    return graph.compile()


# 싱글톤 에이전트 인스턴스
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


def chat(message: str, history: list) -> str:
    """메시지를 에이전트에 전달하고 응답 반환"""
    agent = get_agent()
    lc_history = []
    for h in history:
        if h["role"] == "user":
            lc_history.append(HumanMessage(content=h["content"]))
        elif h["role"] == "assistant":
            lc_history.append(AIMessage(content=h["content"]))

    lc_history.append(HumanMessage(content=message))

    result = agent.invoke(
        {"messages": lc_history, "reflection_count": 0},
        config={"recursion_limit": 25},
    )

    # 마지막 AI 메시지 반환
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            return msg.content

    return "응답을 생성하지 못했습니다."
