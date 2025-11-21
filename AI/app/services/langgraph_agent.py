from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)


class ReminderAgent:
    def __init__(self):
        workflow = StateGraph(dict)
        workflow.add_node("plan", self._plan)
        workflow.add_node("compose", self._compose)
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "compose")
        workflow.add_edge("compose", END)
        self.graph = workflow.compile()

    async def run(self, context: dict) -> dict:
        result = await self.graph.ainvoke(context)
        return result

    async def _plan(self, state: dict) -> dict:
        state["plan"] = f"Remind user about {state.get('topic', 'an event')}."
        return state

    async def _compose(self, state: dict) -> dict:
        state["email_body"] = f"Hi! Here's a gentle reminder: {state['plan']}"
        return state

