# 작업 로그 — Flask 컨테이너에서 ex1.html 렌더링 + Ollama 연동 (2026-11-20)

## 목표

Flask 서버가 이미 떠 있는 컨테이너(`flaskserver`) 안에서, `GET /` 요청 시 `render_template("ex1.html")`로 응답하도록 구성. `ex1.html`은 System/User 입력을 받아 Ollama(`gemma4:e2b`)에 채팅 요청을 보내고 응답을 화면에 보여주는 테스트 페이지.

## 환경 확인

- `docker ps`로 확인한 결과, 포트 5000은 **이미 떠 있던 `flaskserver` 컨테이너**(`COMMAND: python3`, 3주 전 생성)가 점유하고 있었음.
- `flaskserver` 컨테이너의 ID(`dd2a464e19ed`)가 이 작업을 진행한 셸 환경 자체와 동일 — 즉 새로 컨테이너를 빌드/실행할 필요 없이, **이미 떠 있는 이 컨테이너 안에서 바로 코드를 작성/실행**하면 되는 구조였음.
- 컨테이너 안을 확인해보니 `python3`만 대기 중이고 실제 Flask 서버는 돌고 있지 않은 상태(포트 5000에 리스닝 프로세스 없음) → 직접 `app.py`를 작성해서 실행.

## 구성한 파일 (`/workspace/html_test`)

```
html_test/
├── app.py              # GET "/" → render_template("ex1.html")
├── templates/
│   └── ex1.html        # System/User 입력 → Ollama 채팅 테스트 페이지
├── ex1.html             # 원본(최상위, IDE에서 열려있던 파일 — 내용 동일하게 유지)
├── requirements.txt     # flask
└── Dockerfile           # 별도로 이미지 빌드할 경우를 위한 참고용(이번엔 기존 컨테이너에서 바로 실행해 사용하지 않음)
```

`app.py` 핵심:
```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("ex1.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

컨테이너 안에서 실행:
```bash
cd /workspace/html_test
python3 app.py
```
→ `0.0.0.0:5000`에서 서빙, 컨테이너의 `-p 5000:5000` 매핑으로 호스트 PC에서 `http://127.0.0.1:5000/` 접속 가능.

## 디버깅

1. **"예전 화면이 나온다"**
   - 원인: 포트 5000에 실제로는 아무것도 안 떠 있었는데, 브라우저가 이전에 캐시해둔 페이지를 보여주고 있었음.
   - 해결: `app.py` 실행 확인 후 브라우저 강력 새로고침(`Ctrl+F5`).

2. **`{"error": "model 'gemma4:e2b' not found"}`**
   - `ex1.html`의 JS가 Ollama를 `http://127.0.0.1:11434/api/chat`로 **브라우저 기준**으로 직접 호출하는 구조.
   - `GPUIP:11434`(GPU PC, Docker로 띄운 ollama 컨테이너)에는 `gemma4:e2b`가 정상적으로 존재하고 `/api/chat` 테스트도 200 OK로 확인됨.
   - 하지만 브라우저를 켠 PC 자체의 `127.0.0.1:11434`를 직접 조회(`/api/tags`)해보니, **이전 번역기 프로젝트 때 쓴 네이티브(비-Docker) Ollama**가 떠 있었고 거기엔 `qwen3.5:4b`만 설치돼 있었음 — 즉 브라우저가 엉뚱한(로컬) Ollama로 요청을 보내고 있던 것.
   - 해결: `ex1.html`의 fetch 주소를 `http://127.0.0.1:11434` → `http://GPUIP:11434`로 수정 (원본 `ex1.html`, `templates/ex1.html` 둘 다 수정). Flask가 debug 모드(`Debug mode: on`, auto-reload)라 저장 즉시 반영됨.

3. **번역기 때 쓴 로컬 Ollama(qwen3.5) 처리**
   - Docker 컨테이너가 아니라 Windows에 네이티브로 설치된 프로그램(시스템 트레이에 상주)이라는 걸 확인.
   - 지울 필요 없이, 평소엔 꺼두고(트레이 아이콘 우클릭 → Quit Ollama, 또는 `taskkill /IM ollama.exe /F`) 번역기 프로젝트 작업할 때만 다시 켜는 방식으로 정리 — `127.0.0.1` 주소를 쓰는 다른 코드가 실수로 이 로컬 Ollama에 연결되는 혼란을 방지.

## 최종 결과

- `http://127.0.0.1:5000/` (Flask 컨테이너 호스트 PC) 접속 → `ex1.html` 정상 렌더링
- System/User 입력 후 Run 클릭 → `GPUIP:11434`의 `gemma4:e2b`에 정상적으로 요청/응답 확인 (로컬 Ollama를 꺼둔 상태에서도 정상 동작 — 주소가 명확히 분리되어 있음을 재확인)

## 참고 / 교훈

- 브라우저 JS에서 `127.0.0.1`로 외부 서비스를 호출하면, **그 페이지를 여는 컴퓨터가 어디냐**에 따라 전혀 다른 서버에 연결될 수 있음 — 특히 같은 서비스(Ollama 등)가 여러 PC에 각각 설치돼 있을 때 혼란의 원인이 되기 쉬움.
- 더 안정적으로 만들려면, comfyui 프로젝트처럼 Flask 서버가 중간에서 Ollama/ComfyUI를 대신 호출하는 proxy 라우트를 두고 프론트는 항상 Flask 자신에게만 요청하도록 바꾸는 것이 좋음 (추후 개선 포인트로 남김).
