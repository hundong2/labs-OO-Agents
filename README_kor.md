<div align="center">

<br />

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/NVIDIA-NeMo/labs-OO-Agents/main/assets/nvidia-labs-object-oriented-agents-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/NVIDIA-NeMo/labs-OO-Agents/main/assets/nvidia-labs-object-oriented-agents-light.svg">
  <img alt="NVIDIA-labs Object Oriented Agents" src="https://raw.githubusercontent.com/NVIDIA-NeMo/labs-OO-Agents/main/assets/nvidia-labs-object-oriented-agents-light.svg" width="820">
</picture>

<p align="center"><b>AI agent를 만드는 Python다운 방법</b></p>

[![NVIDIA](https://img.shields.io/badge/NVIDIA-76B900?logo=nvidia&logoColor=white)](https://www.nvidia.com/)
[![Paper](https://img.shields.io/badge/paper-arXiv-b31b1b?logo=arxiv&logoColor=white)](https://arxiv.org/abs/2607.20709)
[![Blog](https://img.shields.io/badge/blog-NVIDIA-76B900?logo=nvidia&logoColor=white)](https://developer.nvidia.com/blog/six-agent-harness-capabilities-for-higher-model-performance/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

**언어:** [English](README.md) | [한국어](README_kor.md) · [한국어 학습 가이드](guide/README.md)

</div>

NVIDIA-labs OO Agents(NOOA)는 신뢰할 수 있는 AI agent 개발을 지원하는 model-agnostic Python framework입니다. Prompt, tool, callback, workflow를 서로 다른 추상화로 나누는 대신 agent의 상태, 기능, prompt와 typed interface를 하나의 Python class로 표현합니다.

```python
from nooa import Agent


class SupportAgent(Agent):
    """You are a support agent."""

    order_db: OrderDB

    # 일반 method는 결정적 Python입니다.
    def is_refund_eligible(self, order: Order) -> bool:
        return order.delivered and order.days_since_delivery <= 30

    # ... body는 runtime에서 LLM이 실행하는 agentic method입니다.
    async def triage(self, message: str, order: Order) -> Ticket:
        """Create a typed support ticket."""
        ...
```

핵심 원리:

- **Agent는 Python object입니다.** Field는 상태, method는 기능, docstring은 prompt, type annotation은 계약입니다.
- **`...` body는 LLM-driven입니다.** 실제 본문이 있으면 일반 Python으로 결정적으로 실행됩니다.
- **Code as action.** Model은 `self`, import와 helper에 접근 가능한 Jupyter형 REPL에서 Python을 작성해 행동합니다.
- **Typed I/O.** Pydantic·dataclass·TypedDict 같은 return type을 검증하고 실패 시 재시도할 수 있습니다.
- **기존 소프트웨어 방식.** Python test, tracing, refactoring, version control을 그대로 적용합니다.

설계 원리와 평가 결과는 [NVIDIA OO Agents: Native Python Object-Oriented Agents](https://arxiv.org/abs/2607.20709)를 참고하세요.

## 설치

이 저장소의 개발 규칙은 dependency와 실행에 [uv](https://docs.astral.sh/uv/getting-started/installation/)만 사용하도록 요구합니다. Python 3.12 또는 3.13이 필요합니다.

> **Windows 참고:** 현재 core storage 구현이 POSIX `fcntl` module을 import하므로 native Windows에서는 import 단계에서 실패할 수 있습니다. Windows 사용자는 WSL2의 Linux 환경이나 Linux container/VM에서 실행하세요. Windows build 과정에서 `pyproject.toml` UTF-8 해석 오류가 나면 해당 shell에 `PYTHONUTF8=1`을 설정할 수 있지만, 이는 `fcntl` 호환성 문제를 해결하지는 않습니다.

```bash
uv init my-agent-project
cd my-agent-project
uv add nooa
```

### 선택 package

```bash
uv add nooa-cli                 # 또는 uv add "nooa[cli]"
uv add nooa-memory              # 또는 uv add "nooa[memory]"
uv add nooa-bench               # 또는 uv add "nooa[bench]"
uv add "nooa[cli,memory]"
```

| Package | Extra | 추가 기능 |
|---|---|---|
| `nooa-cli` | `nooa[cli]` | `nooa` command, trace viewer, eval runner |
| `nooa-memory` | `nooa[memory]` | 장기 memory subsystem |
| `nooa-bench` | `nooa[bench]` | `BenchAgent`, Harbor benchmark runner |

`eval_pipeline`은 PyPI에 공개되지 않았으므로 저장소에서 설치합니다.

```bash
uv add "eval_pipeline @ git+https://github.com/NVIDIA-NeMo/labs-OO-Agents.git@main#subdirectory=util/eval_pipeline"
```

개발 branch 또는 release tag를 직접 고정할 수도 있습니다.

```bash
uv add "nooa @ git+https://github.com/NVIDIA-NeMo/labs-OO-Agents.git@main"
uv add "nooa @ git+https://github.com/NVIDIA-NeMo/labs-OO-Agents.git@v0.0.7"
```

## 빠른 시작

### ⚠️ 먼저 읽을 안전 주의사항

NOOA는 연구용 software이며 LLM이 생성한 code를 실행하도록 구성할 수 있습니다. 생성 code는 private data를 외부로 보내거나, 파일을 삭제하거나, 환경을 변경하는 등 위험하거나 원하지 않는 행동을 할 수 있습니다.

NOOA의 AST 검사와 module deny-list는 defense-in-depth guardrail이지 containment boundary가 아닙니다. `open()`, `importlib`, reflection 등으로 Python process의 광범위한 기능에 접근할 수 있으므로 in-process validator만 신뢰하면 안 됩니다. 생성 code는 primary filesystem과 credential에서 격리된 container, VM 또는 [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) 같은 OS 수준 sandbox 안에서 실행하세요.

### 1. Model 선택

LiteLLM이 지원하는 hosted 또는 local model을 사용할 수 있습니다.

```python
from nooa.unifiedllm.registry import get_llm_client

llm = get_llm_client("claude-haiku-4-5")
llm = get_llm_client("gpt-5-mini")
llm = get_llm_client("ollama_chat/qwen3:1.7b", api_base="http://localhost:11434")
llm = get_llm_client(
    "hosted_vllm/Qwen/Qwen3-1.7B",
    api_base="http://localhost:8000/v1",
)
```

Hosted provider는 `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` 등 해당 환경 변수가 필요합니다. Secret을 source, prompt, trace나 commit에 기록하지 마세요.

### 2. 첫 Agent

```python
import asyncio

from nooa import Agent
from nooa.unifiedllm.registry import get_llm_client

llm = get_llm_client("gpt-5-mini")


class FeedbackAgent(Agent, llm=llm):
    """You are an agent specializing in analyzing customer feedback."""

    async def analyze_feedback(self, text: str) -> str:
        """Analyze customer feedback for sentiment and key topics in one sentence."""
        ...


async def main() -> None:
    agent = FeedbackAgent()
    result = await agent.analyze_feedback("Great product, but shipping was slow")
    print(result)


asyncio.run(main())
```

Method name, signature, parameter 값과 docstring이 prompt를 구성합니다. Parameter는 framework가 안전한 크기 제한과 함께 자동 전달하므로 docstring에 `{text}`처럼 다시 삽입하지 마세요.

저장소 예제 실행:

```bash
uv run python examples/quickstart/01_first_generation_method.py
```

### 3. Tracing

Agent method, LLM call과 code execution은 parent-child 관계로 trace됩니다. CLI와 viewer dependency를 설치했다면 다음 명령으로 `http://localhost:5001`에서 확인합니다.

```bash
uv run nooa start-dev
```

Viewer가 실행 중이 아니면 tracing은 별도 오류 없이 비활성화됩니다. JSONL exporter도 사용할 수 있습니다.

## Agent 작성 규칙

### Agentic method와 일반 method

```python
class InventoryAgent(Agent, llm=llm):
    def get_stock(self, item: str) -> int:
        """Get current stock for an item."""
        return self.inventory.get(item, 0)

    async def decide(self, item: str) -> Decision:
        """Decide whether the requested item can be fulfilled."""
        ...
```

- LLM 판단이 필요한 한 작업만 `...` method로 만듭니다.
- Parsing, exact matching, 계산과 검증은 일반 Python helper가 더 안전합니다.
- 여러 단계를 순서대로 묶는 orchestrator는 실제 Python body로 작성해 LLM이 단계를 생략하지 못하게 합니다.
- 완료 주장 전에 test·검증 evidence를 확인하는 gate를 orchestrator에 둡니다.

### Structured output

```python
from typing import Literal

from pydantic import BaseModel, Field


class Analysis(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0, le=1)
    topics: list[str]
```

Raw `dict`보다 명시적인 schema를 사용하면 validation과 자동 retry가 가능해집니다. Public signature에 사용한 type은 generated code namespace에서 보이도록 module level에 정의하거나 import해야 합니다.

### Strategy

- `CodeActStrategy`가 기본이며 code·tool 실행과 반복 추론에 적합합니다.
- 단일 분류·추출과 typed output에는 `PredictStrategy`가 더 단순하고 빠릅니다.
- Strategy 설정은 `PredictConfig`, `CodeActConfig`를 `config=`로 전달합니다.
- `reasoning`은 예약 parameter 이름이므로 agentic method 인자로 사용하지 않습니다.

### Visibility

Public method·field와 module name은 기본적으로 LLM에 보입니다. `@hidden`, `Annotated[T, hidden]`, `with hidden:`으로 명시적으로 숨깁니다. `_private` 이름은 기본적으로 숨겨지며 `@spec(hidden=False)`로 다시 노출할 수 있습니다.

`self.context`, `self.events`는 모든 Agent에 있지만 기본적으로 숨겨집니다. 필요할 때만 `spec(self, "context", hidden=False)`처럼 노출하세요.

## 더 학습하기

- [한국어 단계별 학습 가이드](guide/README.md)
- [공식 progressive example](examples/README.md)
- [Agent authoring skill](skills/nooa-agent-authoring/SKILL.md)
- [Repository 작업 규칙](AGENTS.md)
- [논문](https://arxiv.org/abs/2607.20709)
- [NVIDIA blog](https://developer.nvidia.com/blog/six-agent-harness-capabilities-for-higher-model-performance/)

공식 example은 structured output, helper tool, strategy, `doc()`, tracing, dynamic prompt, context block, summarization, skill, MCP, sandbox, self-extension, model cascade와 event history를 단계적으로 다룹니다.

## 기여

```bash
git clone https://github.com/NVIDIA-NeMo/labs-OO-Agents.git
cd labs-OO-Agents
uv sync --group dev

uv run pre-commit install
uv run pytest
uv run ruff check
uv run pyright
```

기여 commit은 [DCO](CONTRIBUTING.md)에 따라 sign-off해야 하며 자동화 agent의 commit message에는 프로젝트가 요구하는 marker가 필요합니다. 전체 절차는 [CONTRIBUTING.md](CONTRIBUTING.md)를 확인하세요.

## 인용

```bibtex
@techreport{nvidia_oo_agents_2026,
  title  = {NVIDIA-labs OO Agents: Native Python Object-Oriented Agents},
  author = {Furgale, Paul and Klingler, Severin and Nolan, James and Staats, Matt and
            Di Lorenzo, Gaia and Martinez Abad, Elisa and Schueler, Christian and
            Dinu, Razvan and Devoto, Alessio and Berard, Pascal and Kaplun, Gal and Sarafian, Elad and
            Roveri, Riccardo and Derczynski, Leon and Silveira Cabral, Ricardo},
  year   = {2026},
}
```

## 라이선스

Apache 2.0입니다. [LICENSE](LICENSE)와 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)를 확인하세요.

---

> 이 문서는 원본 [README.md](README.md)의 한국어 번역입니다. 연구 software의 API, model alias와 package version은 변경될 수 있으므로 실행 시점의 공식 문서와 lockfile을 함께 확인하세요.
