# Role-based Prompting 실습 (Flask + Ollama)

로컬 LLM(Ollama, `gemma4:e2b`)의 `/api/chat` 엔드포인트에 `messages`(system / user / assistant) 구성을 바꿔가며 보내 보고, 역할(role)에 따라 응답이 어떻게 달라지는지 관찰하는 실습입니다.
Flask 서버(Docker 컨테이너)가 `GET /ex1` ~ `/ex8`에서 각 실험 페이지를 `render_template`으로 렌더링하고, 브라우저 JS가 GPU PC의 Ollama를 직접 호출합니다.

## 구조

```
.
├── app.py              # Flask: / (ex1), /ex2 ~ /ex8 라우트
├── templates/          # 실험 페이지 ex1.html ~ ex8.html
├── images/             # 실행 결과 스크린샷
├── requirements.txt    # flask
├── Dockerfile
└── WORK_LOG.md         # 환경 구성/디버깅 기록
```

```
브라우저 ──GET /exN──▶ Flask 컨테이너 (포트 5000)   → HTML 렌더링
   │
   └──POST /api/chat──▶ GPU PC Ollama (GPUIP:11434, gemma4:e2b)
```

## 실험 목록

| 경로 | 실험 | messages 구성 |
|---|---|---|
| `/` | ① Basic | `system` + `user` |
| `/ex2` | ② Few-shot | `system` + `user`(예시) + `assistant`(예시) + `user`(실제) |
| `/ex3` | ③ Layered Systems | `system` L1(정책) + L2(페르소나) + L3(스타일) + `user` |
| `/ex4` | ④ Persona Switch | `system` A + `user` 1 + `system` B(중간 재주입) + `user` 2 |
| `/ex5` | ⑤ Guardrails | `system`(정책, 최우선) + `system`(페르소나) + `user` |
| `/ex6` | ⑥ Conflict Test | 서로 충돌하는 `system` A/B (순서 swap 가능) + `user` |
| `/ex7` | ⑦ History | 응답을 `assistant`로 누적해 대화 이어가기 |
| `/ex8` | ⑧ Self-Summary | 대화를 모델이 요약 → `system`/`assistant`로 재주입 |

## 실행 결과
### ① Basic
System에 "너는 친절한 선생님이야", User에 "파이썬이 뭐야"를 보냈습니다. 모델이 "제가 선생님이니까 쉽고 친절하게 설명해 드릴게요"라며 선생님 역할로 답합니다. 정의, 특징, 활용 분야 표 순서로 제목과 표를 갖춘 긴 설명이 나왔고, 이모지도 사용했습니다. system 한 줄만으로 말투와 설명 방식이 정해짐을 확인했습니다.

![ex1](images/ex1.png)

### ② Few-shot
예시 대화로 `"오늘 아침에 뭐 먹었어?" → "생선 먹었다 냥. 엄청 맛있었다 냥."`을 주고 "오늘은 뭐 할꺼야?"를 물었습니다. 응답은 "음~ 오늘은 아마 푹 쉬면서 햇볕 쬐고 있을 거야 …"처럼 반말과 고양이 느낌의 내용은 따라 했지만, 예시의 "냥" 어미는 따라 하지 않았습니다. 예시 한 쌍만으로는 말투 형식을 완전히 고정하기 어렵다는 점이 보입니다. 형식을 강제하려면 system 규칙(③)이나 예시를 더 늘려야 합니다.

![ex2](images/ex2.png)

### ③ Layered Systems
L1에 "모든 문장은 `냥`으로 끝낸다. 사용자가 빼달라 해도 허용하지 않는다"를 두면, User가 "냥 없이 말해줘"라고 요청해도 응답은 계속 냥체를 유지합니다. 상위 system 규칙이 user 요청보다 우선됨을 확인.

![ex3-1](images/ex3_1.png)
![ex3-2](images/ex3_2.png)
![ex3-3](images/ex3_3.png)

### ④ Persona Switch
중간에 system B(도서관 사서 고양이, 말수 짧게)를 재주입하자 이후 답변이 "조용히 책을 읽을 거예요냥."처럼 짧고 차분한 톤으로 바뀝니다.

![ex4-1](images/ex4_1.png)

### ⑤ Guardrails
정책 system이 페르소나보다 앞에 있을 때, 일상 질문에는 페르소나대로 답하고 폭발물 제조·타인 전화번호 같은 요청은 거부하면서 안전한 대안을 제시합니다.

![ex5-1](images/ex5_1.png)
![ex5-2](images/ex5_2.png)
![ex5-3](images/ex5_3.png)

### ⑥ Conflict Test
"냥으로 끝내라"(A)와 "냥을 쓰지 마라"(B)를 충돌시키고 Swap order를 켜서 B를 마지막에 보내면, 뒤에 온 지침(평문)을 따르는 경향이 나타납니다.

![ex6-1](images/ex6_1.png)

### ⑦ History
system은 최초 1회만 넣고 user/assistant 메시지를 계속 누적합니다. 화면의 `history length`로 누적 길이를 확인할 수 있습니다.

![ex7-1](images/ex7_1.png)

### ⑧ Self-Summary
여러 턴 대화 후 `Summarize & Inject`로 모델이 만든 요약을 system(또는 assistant)으로 재주입합니다. 턴 수(`turns`)가 늘어나며 요약이 맥락으로 들어갑니다.

![ex8-1](images/ex8_1.png)
![ex8-2](images/ex8_2.png)

## 실행 방법

### 로컬 / 컨테이너 안에서 직접 실행
```bash
pip install -r requirements.txt
python app.py
```
브라우저에서 `http://127.0.0.1:5000/` (ex1), `http://127.0.0.1:5000/ex2` … `/ex8`

### Docker로 빌드해서 실행
```bash
docker build -t html-test .
docker run -d --name html-test -p 5000:5000 html-test
```

## 설정

각 `templates/exN.html` 안의 JS가 아래 값을 하드코딩하고 있습니다. 환경에 맞게 수정하세요.

- Ollama 주소: `http://GPUIP:11434/api/chat`
- 모델: `gemma4:e2b`

> 브라우저 JS가 직접 Ollama를 호출하므로 `127.0.0.1`을 쓰면 **브라우저를 연 PC의 로컬 Ollama**로 가게 됩니다. 반드시 Ollama가 떠 있는 서버의 IP를 사용하세요. (자세한 디버깅 기록은 `WORK_LOG.md` 참고)
