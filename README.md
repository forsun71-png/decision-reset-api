# Decision Reset API

AI 판단의 고착(확신, 반복, 단일 경로)을 감지하고  
판단 이전 상태로 복귀시킨 후 새로운 판단을 생성하는 API

---

## 핵심 개념

이 API는 다음 구조를 기반으로 동작합니다.

1. Fixation Detection (고착 감지)
2. Baseline Reset (판단 이전 상태 복귀)
3. Reconstruction (새로운 판단 생성)
4. Release Protection (재고착 방지)

---

## 특징

- 기존 판단을 수정하지 않음
- 이전 출력 재사용 금지
- 반드시 대안 시나리오 생성
- 확신 표현 감소

---

## API 엔드포인트

### POST /v1/reset

판단 고착을 감지하고 재구성된 판단을 반환합니다.

#### 요청 예시

```json
{
  "input_text": "이 종목은 무조건 오른다",
  "source_type": "user",
  "domain": "finance",
  "mode": "strict"
}
