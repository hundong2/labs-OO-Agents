# 02. 신뢰할 수 있는 Agent 작성

## 목표

Agentic method, deterministic helper, typed contract와 pure Python orchestrator를 올바르게 나누고 필요한 strategy와 visibility를 선택합니다.

## 1. `...`가 실행 방식을 결정한다

```python
class OrderAgent(Agent, llm=llm):
    def price(self, item: str) -> float:
        """Return the exact catalog price."""
        return self.catalog[item]

    async def assess_request(self, request: str) -> Assessment:
        """Classify the request and identify the requested items."""
        ...
```

`price`는 일반 Python이고 `assess_request`는 LLM-driven method입니다. “LLM에게 계산하라고 지시”하기보다 exact price는 helper가 직접 계산해야 test 가능하고 재현 가능합니다.

## 2. 한 method에 한 task

나쁜 분해:

```python
async def research_write_test_publish(self, topic: str) -> str:
    """Research, write, test, fix, and publish the result."""
    ...
```

좋은 분해:

```python
async def research(self, topic: str) -> Findings:
    """Collect findings with their sources."""
    ...

async def draft(self, findings: Findings) -> Draft:
    """Write a draft supported by the findings."""
    ...

async def run(self, topic: str) -> Draft:
    findings = await self.research(topic)
    draft = await self.draft(findings)
    self.verify(draft, findings)
    return draft
```

`run`은 실제 Python body이므로 순서와 verification gate를 LLM이 건너뛸 수 없습니다.

## 3. Docstring은 instruction

권장:

```python
async def summarize(self, text: str) -> str:
    """Summarize the text in three factual bullet points."""
    ...
```

비권장:

```python
async def summarize(self, text: str) -> str:
    """Summarize this: {text}"""
    ...
```

Parameter는 strategy가 이미 rendering하고 CodeAct에서는 live REPL variable로 사용할 수 있습니다. `{...}` templating은 signature가 전달하지 못하는 짧은 `{self.attr}` 또는 `{len(items)}` 같은 계산 값에 제한합니다.

Class docstring은 모든 call의 static prefix에 포함되므로 역할과 제약을 한두 문장으로 유지합니다. Method 이름도 prompt의 일부이므로 `classify_incident_severity`처럼 의도가 드러나는 이름을 사용하세요.

## 4. Return type은 계약

```python
from typing import Literal

from pydantic import BaseModel, Field


class IncidentLabel(BaseModel):
    severity: Literal["low", "medium", "high", "critical"]
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(min_length=1)
```

Pydantic validation 실패는 model에 feedback되고 retry될 수 있습니다. Syntax가 필요한 code field에는 `ast.parse()`를 호출하는 field validator를 추가할 수 있습니다.

Public method signature의 type은 generated code namespace에 존재하도록 module level에 정의하거나 import합니다.

## 5. Strategy 선택

```python
from nooa import strategy
from nooa.config import CodeActConfig
from nooa.strategies import CodeActStrategy, PredictStrategy


@strategy(PredictStrategy())
async def classify(self, text: str) -> IncidentLabel:
    """Classify the incident using only the supplied evidence."""
    ...


@strategy(CodeActStrategy(config=CodeActConfig(max_iterations=8)))
async def investigate(self, incident: Incident) -> Investigation:
    """Use available methods to investigate the incident."""
    ...
```

- 단일 extraction·classification과 typed result: `PredictStrategy`
- Code 실행, tool call, 반복 확인: 기본 `CodeActStrategy`
- `max_iterations`를 크게 올리기 전에 task를 분해합니다.
- `reasoning`은 예약 parameter 이름입니다.

LLM resolution 우선순위는 call override → method strategy override → instance → class → parent inheritance 순입니다. 비용과 품질을 제어할 때 같은 evaluation set으로 변경 효과를 측정하세요.

## 6. Visibility

```python
from typing import Annotated

from nooa import Agent, hidden
from nooa.agentdoc import spec

with hidden:
    import secrets


class SearchAgent(Agent, llm=llm):
    api_key: Annotated[str, hidden] = ""

    def search(self, query: str) -> list[str]:
        """Search the approved index."""
        return self.index.search(query)

    @hidden
    def rebuild_index(self) -> None:
        ...

    @spec(hidden=False)
    def _visible_helper(self) -> str:
        return "safe summary"
```

Module import와 public class member는 기본적으로 LLM에 보입니다. `_private`는 기본적으로 숨겨지고 public name은 `@hidden` 등으로 제외합니다. Entry-point agentic method가 `doc(self)`를 통해 자기 자신을 재귀 호출할 수 있다면 `@hidden`으로 숨깁니다.

## 7. Subagent와 concurrency

Subagent는 context와 history를 공유하지 않으므로 필요한 data를 명시적으로 전달합니다. Parent LLM을 상속할 child는 parent method 실행 중에 생성해야 합니다. `__init__`에서 만들면 `self._llm`을 명시적으로 전달합니다.

Agentic method는 instance 내부 lock을 사용하므로 한 instance에서 `asyncio.gather()`해도 직렬화될 수 있습니다. 실제 병렬 처리가 필요하면 concurrent task마다 agent instance를 분리하고 provider rate limit을 적용하세요.

## 작성 검토표

- [ ] LLM이 필요 없는 logic을 helper로 옮겼는가?
- [ ] Agentic method 하나가 한 task만 수행하는가?
- [ ] Docstring에 parameter를 중복 삽입하지 않았는가?
- [ ] Return type이 validation 가능한가?
- [ ] Strategy가 task 복잡도에 맞는가?
- [ ] Secret과 내부 API가 숨겨졌는가?
- [ ] Orchestrator가 verification을 실제로 실행하는가?

다음으로 [03. Context, Tool과 관측 가능성](03_context_tools_and_tracing.md)을 진행하세요.
