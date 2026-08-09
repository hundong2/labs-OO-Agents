# 01. 설치, 첫 Agent와 안전 경계

## 목표

격리된 Python 환경을 만들고 model client와 첫 agent를 실행하며, in-process guardrail과 실제 sandbox의 차이를 이해합니다.

## 1. 환경 생성

이 저장소 안에서는 dependency 관리와 실행에 `uv`만 사용합니다.

### Windows 실행 환경

현재 저장소의 core storage가 POSIX `fcntl`을 import하므로 native Windows에서는 `ModuleNotFoundError: No module named 'fcntl'`로 시작되지 않을 수 있습니다. Windows에서는 WSL2 Linux distribution, Linux container 또는 VM을 사용하세요.

Windows build backend가 UTF-8 `pyproject.toml`을 CP949로 읽어 실패한다면 해당 shell에 다음 값을 설정할 수 있습니다. 이 설정은 text encoding만 해결하며 POSIX module 호환성을 제공하지 않습니다.

```powershell
$env:PYTHONUTF8 = "1"
```

```bash
uv init my-agent-project
cd my-agent-project
uv python pin 3.12
uv add nooa
```

Trace viewer까지 사용하려면:

```bash
uv add nooa-cli
```

현재 저장소를 개발하려면:

```bash
uv sync --group dev
uv run nooa --help
```

## 2. Model client

Hosted provider:

```bash
export OPENAI_API_KEY=<secret>
# 또는 ANTHROPIC_API_KEY, NVIDIA_API_KEY 등
```

```python
from nooa.unifiedllm.registry import get_llm_client

llm = get_llm_client("gpt-5-mini")
```

Local endpoint:

```python
llm = get_llm_client(
    "ollama_chat/qwen3:1.7b",
    api_base="http://localhost:11434",
)
```

Secret은 `.env.example`에 값 없이 이름만 기록하고 실제 값은 secret manager 또는 보호된 환경 변수로 주입합니다. Trace, prompt dump, exception과 shell history에 key가 남지 않는지 확인하세요.

## 3. 첫 generation method

```python
import asyncio

from nooa import Agent
from nooa.unifiedllm.registry import get_llm_client

llm = get_llm_client("gpt-5-mini")


class FeedbackAgent(Agent, llm=llm):
    """Analyze customer feedback faithfully and concisely."""

    async def analyze(self, text: str) -> str:
        """Summarize the sentiment and key topic in one sentence."""
        ...


async def main() -> None:
    result = await FeedbackAgent().analyze("Great product, but shipping was slow")
    print(result)


asyncio.run(main())
```

```bash
uv run python feedback_agent.py
```

`text` 값은 signature와 strategy의 안전한 rendering 경로로 전달됩니다. Docstring에 `Summarize {text}`처럼 다시 넣으면 truncation을 우회하고 untrusted input을 instruction channel로 이동시키므로 피합니다.

## 4. 안전 경계

CodeAct agent는 Python REPL에서 generated code를 실행할 수 있습니다. AST 검사와 deny-list는 실수와 흔한 문제를 줄이지만 다음 접근을 완전히 막는 보안 경계가 아닙니다.

- `open()`을 통한 filesystem 접근
- path에서 module을 load하는 `importlib`
- reflection을 통한 object graph 접근
- network client를 통한 외부 전송
- parent process가 가진 credential과 environment 접근

따라서 신뢰할 수 없는 task나 data를 처리하는 agent는 다음 조건을 갖춘 OS-level isolation 안에서 실행합니다.

- 최소 filesystem mount와 read-only root
- 필요한 destination만 허용하는 egress policy
- 짧은 수명의 credential과 최소 권한
- CPU, memory, process, wall-time 제한
- 실행 후 폐기되는 container/VM
- human approval가 필요한 destructive action

## 5. Trace viewer

```bash
uv run nooa start-dev
```

`http://localhost:5001`에서 method call graph, LLM call과 code execution을 확인합니다. Viewer를 public interface에 그대로 노출하면 prompt·input·output과 secret이 유출될 수 있으므로 인증과 network 제한을 적용하세요.

## 6. 첫 점검

- [ ] Python version이 `>=3.12,<3.14`인가?
- [ ] `uv lock` 또는 `uv.lock`으로 dependency가 고정됐는가?
- [ ] provider key가 source와 trace에 없는가?
- [ ] generated code가 primary filesystem과 분리됐는가?
- [ ] timeout·resource limit이 있는가?
- [ ] 첫 method trace에서 입력, 실행 단계와 결과를 설명할 수 있는가?

다음으로 [02. 신뢰할 수 있는 Agent 작성](02_agent_authoring.md)을 진행하세요.
