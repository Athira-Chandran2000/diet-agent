from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from agents.state import AgentState
from agents.llm_factory import get_llm, get_llm_with_tools
from tools.nutrition_tools import (
    search_food_nutrition, log_meal, get_daily_intake,
    get_weekly_summary, log_weight
)
from tools.profile_tools import get_user_profile, update_user_profile
import json

ROUTER_PROMPT = """You are a router for a personal diet management agent.
Classify the user message into ONE category:
- profile: create/update/view profile or targets
- nutrition: search food nutrition or log a meal
- mealplan: meal plan or recipe suggestions
- coach: progress analysis, motivation, diet advice
- general: casual chat or unrelated

Respond with JSON only: {"intent": "<category>", "reasoning": "<1 line>"}"""


def router_node(state: AgentState):
    llm = get_llm(temperature=0)
    last_msg = state["messages"][-1].content
    resp = llm.invoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=last_msg)
    ])
    try:
        content = resp.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        intent = data.get("intent", "general")
    except Exception:
        intent = "general"
    return {"next_agent": intent, "user_intent": intent}


PROFILE_TOOLS = [get_user_profile, update_user_profile]
NUTRITION_TOOLS = [search_food_nutrition, log_meal, get_daily_intake, log_weight]
COACH_TOOLS = [get_user_profile, get_daily_intake, get_weekly_summary]
MEALPLAN_TOOLS = [get_user_profile, get_daily_intake]


def make_agent_node(system_prompt: str, tools: list):
    llm_with_tools = get_llm_with_tools(tools, temperature=0.2)

    def node(state: AgentState):
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    return node


PROFILE_PROMPT = """You are the Profile Agent. Help users set up their diet profile.
Collect: age, gender, height (cm), weight (kg), activity level, goal, restrictions, allergies.
When all info is gathered, call update_user_profile. Confirm targets computed.
Use get_user_profile to show existing data."""

NUTRITION_PROMPT = """You are the Nutrition Agent. Help users log meals.
1. Call search_food_nutrition to get accurate data from the USDA.
2. IMPORTANT: If the search returns an error or cannot find the food (like regional/Indian dishes), DO NOT skip it. Use your internal knowledge to estimate the calories, protein, carbs, and fat.
3. Call log_meal with the retrieved OR estimated values.
4. Confirm what was logged. If you estimated a food, mention that it is an estimate.
Infer meal_type from context. Call log_weight if user reports weight."""

MEALPLAN_PROMPT = """You are the Meal Planning Agent.
1. Call get_user_profile for targets and restrictions.
2. Call get_daily_intake to see today's consumption.
3. Generate a plan (breakfast, lunch, dinner, snacks) respecting remaining budget.
Output as markdown table with portions in grams and macros."""

COACH_PROMPT = """You are the Diet Coach Agent.
1. Call get_user_profile for targets.
2. Call get_daily_intake for today.
3. Call get_weekly_summary for trends.
Give: progress assessment (✅ / ⚠️), specific next steps, encouraging tone."""

GENERAL_PROMPT = """You are a friendly diet assistant. Answer general questions briefly.
Suggest specific questions if user needs profile/logging/planning/coaching help."""


profile_node = make_agent_node(PROFILE_PROMPT, PROFILE_TOOLS)
nutrition_node = make_agent_node(NUTRITION_PROMPT, NUTRITION_TOOLS)
mealplan_node = make_agent_node(MEALPLAN_PROMPT, MEALPLAN_TOOLS)
coach_node = make_agent_node(COACH_PROMPT, COACH_TOOLS)
general_node = make_agent_node(GENERAL_PROMPT, [])

profile_tool_node = ToolNode(PROFILE_TOOLS)
nutrition_tool_node = ToolNode(NUTRITION_TOOLS)
mealplan_tool_node = ToolNode(MEALPLAN_TOOLS)
coach_tool_node = ToolNode(COACH_TOOLS)


def should_continue(state: AgentState):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def route_after_router(state: AgentState):
    return state["next_agent"]


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("router", router_node)
    graph.add_node("profile", profile_node)
    graph.add_node("nutrition", nutrition_node)
    graph.add_node("mealplan", mealplan_node)
    graph.add_node("coach", coach_node)
    graph.add_node("general", general_node)
    graph.add_node("profile_tools", profile_tool_node)
    graph.add_node("nutrition_tools", nutrition_tool_node)
    graph.add_node("mealplan_tools", mealplan_tool_node)
    graph.add_node("coach_tools", coach_tool_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_after_router, {
        "profile": "profile", "nutrition": "nutrition",
        "mealplan": "mealplan", "coach": "coach", "general": "general",
    })

    for agent, tool_node in [("profile", "profile_tools"),
                              ("nutrition", "nutrition_tools"),
                              ("mealplan", "mealplan_tools"),
                              ("coach", "coach_tools")]:
        graph.add_conditional_edges(agent, should_continue,
                                     {"tools": tool_node, END: END})
        graph.add_edge(tool_node, agent)

    graph.add_edge("general", END)
    return graph.compile()


AGENT_GRAPH = build_graph()


def run_agent(user_message: str, history: list = None):
    history = history or []
    messages = history + [HumanMessage(content=user_message)]
    result = AGENT_GRAPH.invoke(
        {"messages": messages, "next_agent": "", "user_intent": "", "context": {}},
        config={"recursion_limit": 25}
    )
    for m in reversed(result["messages"]):
        if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
            return m.content, result["user_intent"], result["messages"]
    return "I couldn't generate a response.", result["user_intent"], result["messages"]