# 실습: 검증 Gate가 있는 Triage Agent

[reliable_triage_agent.py](reliable_triage_agent.py)는 다음 설계 원칙을 한 파일에 적용합니다.

- LLM의 한 가지 task인 분류에는 `PredictStrategy`
- Category별 queue routing은 deterministic Python helper
- Pydantic으로 category, urgency, confidence 검증
- Entry-point orchestrator가 input·confidence gate를 강제
- Entry-point와 CLI helper는 LLM visible surface에서 숨김
- Model은 CLI argument로 주입해 environment별 교체 가능

## 준비

```bash
uv init nooa-guide-lab
cd nooa-guide-lab
uv add nooa
```

이 저장소 clone에서 실행한다면:

```bash
uv sync --group dev
```

Hosted model을 사용하면 provider key를 환경 변수에 설정합니다. 예제나 shell history에 값을 직접 쓰지 마세요.

## 실행

```bash
uv run python guide/examples/reliable_triage_agent.py \
  "Payment was charged twice and I need help now." \
  --model gpt-5-mini
```

Local Ollama model 예:

```bash
uv run python guide/examples/reliable_triage_agent.py \
  "The app crashes whenever I upload a file." \
  --model ollama_chat/qwen3:1.7b \
  --api-base http://localhost:11434
```

## 예상 흐름

```text
입력 정규화·길이 검사
  → PredictStrategy 분류
  → Pydantic validation/retry
  → confidence gate
  → deterministic route_for(category)
  → JSON 결과
```

Confidence가 `0.55` 미만이면 자동 route하지 않고 exception으로 중단합니다. 이 threshold는 calibration 결과가 아니라 학습용 예시이므로 실제 서비스에서는 labeled evaluation set으로 조정하세요.

## 정적 검증

```bash
uv run ruff check guide/examples/reliable_triage_agent.py
uv run ruff format --check guide/examples/reliable_triage_agent.py
uv run pyright guide/examples/reliable_triage_agent.py
```

## 확장 과제

1. `FakeLLMClient` scripted response로 network 없는 contract test를 만듭니다.
2. `critical` urgency는 human approval queue로만 보내도록 변경합니다.
3. 분류 evidence를 입력의 exact quote로 제한하고 validator를 추가합니다.
4. Prompt injection 문구와 매우 긴 input의 regression case를 추가합니다.
5. Trace에서 원문 customer data를 redaction하는 middleware를 적용합니다.
6. Category별 accuracy, abstention rate, latency와 비용을 evaluation dataset에서 측정합니다.
