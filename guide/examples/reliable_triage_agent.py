# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Validation gate와 deterministic routing을 결합한 NOOA 학습 예제."""

from typing import Literal

from pydantic import BaseModel, Field

from nooa import Agent, hidden, strategy
from nooa.strategies import PredictStrategy
from nooa.unifiedllm import FakeLLMClient
from nooa.unifiedllm.registry import get_llm_client

with hidden:
    import argparse
    import asyncio
    import json


Category = Literal["billing", "technical", "account", "general"]
Urgency = Literal["low", "medium", "high", "critical"]


class TriageLabel(BaseModel):
    """LLM이 반환해야 하는 제한된 분류 계약."""

    category: Category
    urgency: Urgency
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1, max_length=300)


class TriageDecision(BaseModel):
    """분류 결과와 결정적 routing을 결합한 최종 결과."""

    label: TriageLabel
    queue: str


class TriageAgent(Agent, llm=FakeLLMClient()):
    """Classify support requests using only the supplied customer message."""

    @strategy(PredictStrategy())
    async def classify(self, message: str) -> TriageLabel:
        """Classify the request by category and urgency with a brief factual rationale."""
        ...

    def route_for(self, category: Category) -> str:
        """Return the approved queue for a validated category."""
        routes: dict[Category, str] = {
            "billing": "finance-support",
            "technical": "technical-support",
            "account": "identity-support",
            "general": "general-support",
        }
        return routes[category]

    @hidden
    async def run(self, message: str) -> TriageDecision:
        """Validate input, classify once, enforce confidence, and route deterministically."""
        normalized = " ".join(message.split())
        if not normalized:
            raise ValueError("message must not be empty")
        if len(normalized) > 4_000:
            raise ValueError("message must be at most 4,000 characters")

        label = await self.classify(normalized)
        if label.confidence < 0.55:
            raise RuntimeError("classification confidence is below the routing threshold")
        return TriageDecision(label=label, queue=self.route_for(label.category))


@hidden
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", help="분류할 customer support message")
    parser.add_argument("--model", default="gpt-5-mini", help="LiteLLM model 또는 registry alias")
    parser.add_argument(
        "--api-base", default=None, help="Ollama/vLLM 등 OpenAI-compatible endpoint"
    )
    return parser.parse_args()


@hidden
async def main() -> None:
    args = parse_args()
    llm = get_llm_client(args.model, api_base=args.api_base)
    decision = await TriageAgent(llm=llm).run(args.message)
    print(json.dumps(decision.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
