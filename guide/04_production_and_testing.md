# 04. Production 설계와 검증

## 목표

Agent를 일반 software와 probabilistic component가 결합된 system으로 시험하고, 보안·비용·latency·배포 위험을 통제합니다.

## 1. Test pyramid

### 결정적 unit test

- Parsing, policy, routing, validation helper
- Visibility metadata와 rendered agent documentation
- Pydantic constraint와 invalid input
- Context formatter와 memory namespace

### Fake LLM contract test

`FakeLLMClient`로 network 없이 prompt construction, strategy wiring, retry와 event behavior를 검증합니다.

```python
from nooa.unifiedllm import FakeLLMClient

agent = MyAgent(llm=FakeLLMClient())
```

Scripted response가 필요한 test는 expected tool call 또는 code response를 명시합니다. Fake test 통과는 실제 model 품질을 증명하지 않습니다.

### Provider integration test

- 실제 provider의 작은 canary set
- Timeout, rate limit, malformed response와 retry
- Model alias·version 변경 감지
- Secret scrubbing과 trace export

### Evaluation

대표 task dataset에 correctness, schema-valid rate, tool success, safety violation, latency, token과 비용을 기록합니다. 평균 외에 p95·p99와 category별 실패를 봅니다.

## 2. 저장소 검증 명령

```bash
uv sync --group dev
uv run pytest
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pre-commit run --all-files
```

Integration, sandbox, stress marker는 필요한 environment에서 별도로 실행합니다.

```bash
uv run pytest -m integration
uv run pytest -m sandbox
uv run pytest -m stress
```

실제 provider call과 비용이 발생하는 test는 기본 unit suite와 분리하고 명시적인 opt-in을 요구하세요.

## 3. Prompt와 API regression

Method 이름, docstring, type annotation, visible helper와 context 변화는 모두 prompt/API 변경입니다.

- `build_prompt_data()`로 structured prompt snapshot을 검사합니다.
- `print_prompt()`로 사람이 최종 rendering을 검토합니다.
- Public type과 `doc(self)` 변경을 golden test로 추적합니다.
- Prompt 변경 전후 같은 evaluation set을 실행합니다.
- Argument truncation과 큰 input behavior를 test합니다.

## 4. Security threat model

| 위험 | 예 | 통제 |
|---|---|---|
| Prompt injection | Document가 policy 무시 지시 | data/instruction 분리, allowlisted tool, approval |
| Code execution | Generated Python이 파일 삭제 | OS sandbox, read-only mount, 최소 권한 |
| Data exfiltration | Tool이 secret을 외부 전송 | egress 제한, secret isolation, scrubbing |
| Tool misuse | Write/delete API 오호출 | read/write 분리, idempotency, human gate |
| Memory poisoning | 악성 사실 장기 저장 | provenance, namespace, TTL, review/forget |
| Supply chain | 새 dependency·skill 변조 | `uv.lock`, source review, version pin, scan |
| Trace leakage | Prompt에 PII·key 저장 | redaction, encryption, retention, RBAC |

Static AST validator는 malicious Python을 가두는 containment가 아닙니다.

## 5. Reliability

- 전체 deadline 안에서 method·tool별 timeout을 배분합니다.
- Retry는 transient error에만 제한하고 exponential backoff와 jitter를 사용합니다.
- Write tool은 idempotency key와 operation status 조회를 제공합니다.
- Partial failure와 resume point를 event에 기록합니다.
- Circuit breaker와 provider fallback의 품질 차이를 측정합니다.
- Confidence는 calibration하지 않으면 실제 확률로 해석하지 않습니다.

## 6. 비용과 latency

- Predict로 충분한 단일 task에 CodeAct loop를 사용하지 않습니다.
- Deterministic helper로 token과 model call을 줄입니다.
- Context와 `doc()` surface를 task에 맞게 제한합니다.
- 긴 history는 summarizer를 사용하되 정보 손실을 평가합니다.
- Model cascade는 cheap model의 failure cost까지 포함해 비교합니다.
- Instance lock과 provider concurrency/rate limit을 함께 고려합니다.

## 7. Deployment gate

- [ ] 고정된 package·model·skill version이 있는가?
- [ ] Unit, contract, integration, evaluation 결과가 기준을 통과했는가?
- [ ] Sandbox와 egress policy가 실제 배포 환경에서 확인됐는가?
- [ ] Tool permission과 human approval 경계가 문서화됐는가?
- [ ] Trace redaction, retention과 incident access 절차가 있는가?
- [ ] 비용·latency·error SLO와 alert가 있는가?
- [ ] Rollback과 provider 장애 fallback이 시험됐는가?
- [ ] User에게 agent 한계와 자동 행동 범위를 알렸는가?

## 8. 기여 규칙

- Dependency는 `uv`로만 관리합니다.
- Python file에는 저장소의 SPDX header가 필요합니다.
- DCO에 따라 commit을 sign-off합니다.
- Automated agent commit message는 프로젝트가 지정한 marker로 끝냅니다.
- 코드 변경에는 관련 test와 evidence를 포함합니다.

[실습 예제](examples/README.md)에서 분류와 routing을 LLM/결정적 logic으로 나누고 validation gate를 적용해 보세요.
