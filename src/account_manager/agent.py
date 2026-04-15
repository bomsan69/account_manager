"""LangGraph 기반 Self-Correction + Reflection 에이전트"""
import os
from typing import Annotated, Literal

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from .memory import read_memory
from .tools import ALL_TOOLS

# Ollama 설정
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

# vLLM (OpenAI-compatible) 설정
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")  # ollama | vllm
VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "https://openai.aifreechatbot.com/v1")
VLLM_MODEL = os.environ.get("VLLM_MODEL", "")
VLLM_API_KEY = os.environ.get("VLLM_API_KEY", "EMPTY")

# REFLECTION_ENABLED=false 로 설정하면 반성 단계를 건너뜀 (응답 속도 2배 향상)
REFLECTION_ENABLED = os.environ.get("REFLECTION_ENABLED", "true").lower() != "false"


def _create_llm(with_tools: bool = False):
    """LLM_PROVIDER 환경변수에 따라 LLM 인스턴스 반환"""
    if LLM_PROVIDER == "vllm":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            base_url=VLLM_BASE_URL,
            model=VLLM_MODEL,
            api_key=VLLM_API_KEY,
            temperature=0,
        )
    else:
        llm = ChatOllama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=0,
        )
    if with_tools:
        return llm.bind_tools(ALL_TOOLS)
    return llm

SYSTEM_PROMPT = """당신은 사용자의 웹사이트 계정 정보를 관리하는 AI 어시스턴트입니다.
사용자가 계정 정보를 조회, 저장, 업데이트, 삭제하도록 도와주세요.

중요 규칙:
1. 사용자가 "로그인 정보", "계정 정보", "비밀번호"를 요청하면 show_password=True로 tool_get_account를 호출하세요.
   단순히 계정 존재 여부만 묻는 경우에는 show_password=False로 호출하세요.
2. 도구가 반환한 계정 정보를 그대로 사용자에게 전달하세요. 비밀번호 표시 여부에 대한 설명이나 보안 안내 문구를 임의로 추가하지 마세요.
3. 계정 삭제 전에 반드시 사용자에게 확인을 요청하세요.
4. 새 계정 저장 시 인증 방식(auth_method)을 먼저 파악하세요:
   - password: 이메일/아이디 + 비밀번호 → 이메일, 비밀번호, URL 수집
   - oauth: 소셜 로그인 → oauth_provider(Google/GitHub/Kakao 등), oauth_account(사용 계정) 수집
   - apikey: API 키 인증 → api_key, URL 수집
   - passkey: 패스키 → 이메일, URL 수집 (비밀번호 없음)
5. 답변은 한국어로 하고, 정확하고 간결하게 응답하세요.
6. 불확실한 경우 사용자에게 추가 정보를 요청하세요.
7. tool_save_memory에는 절대로 비밀번호, API 키, 토큰 등 민감한 자격증명을 저장하지 마세요.
   사이트명, 사용자 선호도, 카테고리 구조 등 메타정보만 저장하세요.

현재 저장된 기억:
{memory}
"""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    reflection_count: int


def create_agent():
    llm_with_tools = _create_llm(with_tools=True)
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

        reflection_prompt = f"""아래는 AI가 사용자에게 보낸 답변입니다:
---
{last_ai_msg.content}
---
위 답변에 누락되거나 잘못된 정보가 있으면 수정하여 완전한 답변을 작성하세요.
답변이 이미 정확하고 완전하다면, 위 답변을 그대로 복사해서 반환하세요.
절대로 답변의 품질에 대한 평가나 코멘트를 하지 마세요. 오직 최종 답변 내용만 반환하세요."""

        memory_content = read_memory()
        system_msg = SystemMessage(content=SYSTEM_PROMPT.format(memory=memory_content))
        reflection_msg = HumanMessage(content=reflection_prompt)
        messages = [system_msg] + state["messages"] + [reflection_msg]

        refined = _create_llm().invoke(messages)

        # 메타 코멘트 감지: 실제 답변 대신 품질 평가를 반환한 경우 원본 유지
        meta_keywords = ["유지합니다", "정확합니다", "완전합니다", "충분합니다", "검토 결과", "답변이 적절"]
        is_meta = any(kw in refined.content for kw in meta_keywords)

        if not is_meta and refined.content and refined.content != last_ai_msg.content:
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
        if REFLECTION_ENABLED:
            reflection_count = state.get("reflection_count", 0)
            if reflection_count < 1:
                return "reflect"
        return "end"

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
    import httpx

    if LLM_PROVIDER == "vllm":
        # vLLM 서버 연결 확인
        try:
            headers = {"Authorization": f"Bearer {VLLM_API_KEY}"}
            resp = httpx.get(f"{VLLM_BASE_URL}/models", headers=headers, timeout=5)
            if resp.status_code == 401:
                raise RuntimeError(
                    f"vLLM 서버 인증 실패 ({VLLM_BASE_URL})\n"
                    "  .env의 VLLM_API_KEY를 확인하세요."
                )
            if not VLLM_MODEL:
                # 모델 이름 미설정 시 첫 번째 모델 자동 선택
                models = resp.json().get("data", [])
                if models:
                    raise RuntimeError(
                        f"VLLM_MODEL이 설정되지 않았습니다.\n"
                        f"  사용 가능한 모델: {', '.join(m['id'] for m in models)}\n"
                        f"  .env에 VLLM_MODEL=<모델명>을 추가하세요."
                    )
        except httpx.ConnectError:
            raise RuntimeError(
                f"vLLM 서버에 연결할 수 없습니다. ({VLLM_BASE_URL})"
            )
    else:
        # Ollama 연결 사전 확인
        try:
            resp = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
            models = [m["name"].split(":")[0] for m in resp.json().get("models", [])]
            model_base = OLLAMA_MODEL.split(":")[0]
            if model_base not in models:
                available = ", ".join(models) if models else "없음"
                raise RuntimeError(
                    f"모델 '{OLLAMA_MODEL}'이 설치되어 있지 않습니다.\n"
                    f"  설치된 모델: {available}\n"
                    f"  설치 명령어: ollama pull {OLLAMA_MODEL}"
                )
        except httpx.ConnectError:
            raise RuntimeError(
                f"Ollama 서버에 연결할 수 없습니다. ({OLLAMA_BASE_URL})\n"
                "  실행 명령어: ollama serve"
            )

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
        config={"recursion_limit": 50},
    )

    # 마지막 AI 메시지 반환
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            return msg.content

    return "응답을 생성하지 못했습니다."
