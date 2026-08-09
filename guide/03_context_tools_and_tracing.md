# 03. Context, Tool과 관측 가능성

## 목표

Agent가 필요한 정보와 기능만 발견하게 하고, 긴 실행의 history를 관리하며, trace와 event로 동작을 조사합니다.

## 1. Progressive disclosure와 `doc()`

`doc(self)`는 visible method·field, signature, docstring을 API 문서로 생성합니다.

```python
async def investigate(self, issue: str) -> Report:
    """Investigate the issue using the available methods.

    Available API:
    {doc(self)}
    """
    ...
```

모든 외부 API schema를 system prompt에 복사하지 않고 model이 필요할 때 object 구조를 발견하게 할 수 있습니다. Visible surface가 너무 크면 선택 비용과 공격면이 커지므로 task에 필요한 method만 노출하세요.

## 2. Context block

Static context는 한 번 계산되고 cached됩니다.

```python
self.context["policy"] = rendered_policy
```

Dynamic context는 각 LLM turn에 Python expression을 다시 평가합니다.

```python
self.context.set_dynamic("project_state", "self.format_project_state()")
```

`self.context`와 `self.events`는 기본적으로 LLM에서 숨겨집니다. Agent가 직접 context를 관리해야 할 때만 `spec(self, "context", hidden=False)`로 공개합니다.

Context에는 secret 원문, 불필요한 전체 document와 무제한 log를 넣지 않습니다. Source와 timestamp를 붙이고 size budget, freshness와 trust level을 관리하세요.

## 3. History summarization

긴 session은 token budget을 넘기 전에 older event를 압축해야 합니다.

```python
from nooa.agents import TokenBudgetSummarizer
from nooa.config import TokenBudgetConfig

TokenBudgetSummarizer.install(
    agent,
    config=TokenBudgetConfig(max_tokens=1000),
)
```

Batch형 task에는 method call 단위로 압축하는 `MethodSummarizer`가 적합할 수 있습니다. Summary가 decision evidence를 삭제하지 않는지 regression test를 작성하세요.

## 4. Skill

Skill은 guideline, example과 domain knowledge를 curated context로 제공합니다. Skill을 작고 명확한 책임으로 나누고 version과 source를 기록합니다. Instruction precedence와 prompt injection 가능성을 검토하고, skill이 부여하지 않아야 할 권한을 tool로 노출하지 마세요.

이 저장소의 authoring skill은 [skills/nooa-agent-authoring/SKILL.md](../skills/nooa-agent-authoring/SKILL.md)에 있습니다.

## 5. MCP tool

```bash
uv add "nooa[mcp]"
```

MCP는 외부 service를 표준 interface로 호출하게 하지만 server가 신뢰된다는 뜻은 아닙니다.

- Server allowlist와 TLS identity 검증
- Tool별 최소 scope와 read/write 분리
- Timeout, retry, idempotency key
- Destructive call 전 human approval
- Untrusted tool output을 instruction으로 취급하지 않기
- Request/response secret scrubbing

## 6. Memory

```bash
uv add nooa-memory
```

Memory subsystem은 agent가 자신의 memory를 작성·검색·갱신·삭제하게 합니다. 오래된 사실, prompt injection, 개인정보와 잘못된 association이 장기적으로 누적될 수 있습니다.

- Memory schema와 provenance를 기록합니다.
- User·tenant namespace를 분리합니다.
- TTL, forget과 correction 경로를 제공합니다.
- Retrieval result를 evidence가 아니라 후보 context로 취급합니다.
- Memory enabled/disabled behavior를 regression test합니다.

## 7. Tracing

Viewer:

```bash
uv run nooa start-dev --port 5001
```

JSONL:

```python
from nooa.tracing import enable_tracing, exporters

enable_tracing(exporters=[exporters.jsonl("traces/my_agent")])
```

Public, private, dunder method도 기본 trace될 수 있으며 `@no_trace`로 제외할 수 있습니다. Trace에는 prompt, code, tool I/O와 private data가 포함될 수 있으므로 encryption, retention, access control과 scrubbing을 적용합니다.

좋은 trace 질문:

1. 어떤 method와 strategy가 선택됐는가?
2. Model이 어떤 visible API를 받았는가?
3. 어떤 tool과 parameter를 호출했는가?
4. Validation 실패와 retry가 있었는가?
5. 최종 주장을 뒷받침하는 observation은 무엇인가?
6. 비용, token, latency와 error는 어디서 발생했는가?

## 8. Event API

```python
agent.event_manager.on("message", lambda event: print(event.content))
recent = agent.events.query()
```

Audit와 monitoring subscriber가 agent 실행 자체를 지연시키거나 실패시키지 않도록 backpressure와 error isolation을 설계합니다.

다음으로 [04. Production 설계와 검증](04_production_and_testing.md)을 진행하세요.
