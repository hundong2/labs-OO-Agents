# NVIDIA OO Agents 한국어 학습 가이드

작성일: 2026-08-09

NOOA를 처음 설치해 첫 generation method를 만드는 단계부터, typed contract·strategy·context·tracing·MCP·memory·sandbox와 운영 검증을 설계하는 단계까지 이어지는 학습 경로입니다.

## 학습 순서

1. [설치, 첫 Agent와 안전 경계](01_getting_started.md) — `uv`, Python 3.12+, provider/local model, code execution isolation
2. [신뢰할 수 있는 Agent 작성](02_agent_authoring.md) — ellipsis, docstring, type contract, helper, orchestrator, strategy, visibility
3. [Context, Tool과 관측 가능성](03_context_tools_and_tracing.md) — context/event, `doc()`, skill, MCP, memory, tracing과 summarization
4. [Production 설계와 검증](04_production_and_testing.md) — test pyramid, fake LLM, security, concurrency, 비용, 배포, 기여
5. [실습: 검증 gate가 있는 triage agent](examples/README.md) — Predict strategy와 결정적 route helper를 결합한 실행 예제

## 핵심 정신 모델

```text
Python class
  ├─ field: 상태와 dependency
  ├─ 일반 method: 결정적 helper/tool/orchestrator
  ├─ async method + ...: LLM이 구현하는 agentic task
  ├─ docstring: instruction
  ├─ signature·type: 입력과 출력 계약
  └─ context·events·trace: runtime state와 증거
```

NOOA는 “agent workflow를 별도 DSL로 표현”하기보다 Python object model을 agent interface로 사용합니다. 그 결과 일반적인 refactoring, test, type checking과 tracing을 그대로 적용할 수 있습니다.

## 가장 중요한 작성 규칙

- Agentic method 하나에는 LLM task 하나만 둡니다.
- Workflow 순서를 보장할 orchestrator는 실제 Python body로 작성합니다.
- Exact parsing, 계산, validation과 policy는 deterministic helper로 둡니다.
- Parameter는 자동 rendering되므로 docstring에 `{param}`으로 다시 삽입하지 않습니다.
- Return type을 구체적인 Pydantic model 등으로 선언합니다.
- Public name은 LLM에 보인다고 가정하고 secret·내부 helper는 명시적으로 숨깁니다.
- 완료 주장은 검증 evidence 뒤에만 허용합니다.
- LLM-generated code는 OS-level sandbox에서 실행합니다.

## 학습 전 준비

- Python 3.12 또는 3.13
- `uv`
- hosted provider key 또는 격리된 local model endpoint
- container, VM, NVIDIA OpenShell 등 code execution sandbox
- trace viewer를 위한 `nooa-cli`

## 공식 자료

- [원본 README](../README.md)
- [한국어 README](../README_kor.md)
- [공식 예제](../examples/README.md)
- [저장소 지침](../AGENTS.md)
- [Agent authoring skill](../skills/nooa-agent-authoring/SKILL.md)
- [Security policy](../SECURITY.md)
- [Contributing](../CONTRIBUTING.md)

NOOA는 연구 software입니다. API, model alias와 package 구조는 변경될 수 있으므로 현재 `uv.lock`, source와 changelog를 기준으로 검증하세요.
