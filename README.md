# 현대자동차 앱 개발

Windows PC에서 실행하는 자동차 경고등 안내 및 차량 정비 기록 관리 시제품입니다.

## 포함 기능
- 15종 자동차 경고등의 일반적인 의미, 예상 원인, 권장 대응 안내
- 계기판 사진 업로드 및 미리보기
- 진단 기록 저장 및 CSV 다운로드
- 여러 차량 등록, 수정, 삭제
- 차량별 부품 교체 연도 및 메모 등록
- 부품 교체 기록 삭제
- 기존 프로젝트에 저장되어 있던 차량 정보(현대자동차 쏘나타, 2026년식, 100,000km)를 초기 데이터로 반영

> 주의: 실제 차량 OBD/ECU 연결, 이미지 자동 인식, 정비소 예약 기능은 포함되어 있지 않습니다. 안전 관련 경고는 차량 설명서와 전문 정비사의 안내를 따르세요.

## 1. VS Code에서 폴더 열기
압축을 푼 프로젝트 폴더를 VS Code에서 엽니다.

## 2. 가상환경 만들기 (권장)
VS Code 메뉴에서 터미널 → 새 터미널을 누른 뒤 다음 명령을 실행합니다.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

PowerShell에서 실행 정책 오류가 나오면 아래 명령을 한 번 실행한 뒤 다시 활성화합니다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. 필요한 패키지 설치

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. 웹앱으로 실행

```powershell
python -m streamlit run app.py --server.port 8502
```

브라우저에서 `http://localhost:8502`가 열립니다. 종료하려면 터미널에서 `Ctrl + C`를 누릅니다.

## 5. 별도 Windows 창으로 실행

```powershell
python desktop.py
```

브라우저 탭 대신 별도의 현대자동차 앱 개발 창이 열립니다. 창을 닫으면 내부 Streamlit 서버도 종료됩니다.

## 6. EXE 만들기 (선택)

패키지를 설치한 뒤 아래 명령을 실행합니다.

```powershell
python -m PyInstaller --noconfirm --clean --windowed --name Hyundai_Car_App --collect-all streamlit --collect-all webview --collect-all pandas desktop.py
```

생성 결과는 `dist\Hyundai_Car_App\Hyundai_Car_App.exe`에 만들어집니다. PyInstaller 결과물은 실행 PC의 Windows 환경 및 보안 프로그램에 따라 추가 설정이 필요할 수 있습니다.

## 데이터 파일
앱 실행 후 `data` 폴더에 아래 파일이 자동 생성됩니다.
- `vehicle.json`: 차량 및 부품 교체 기록
- `diagnosis_history.json`: 진단 기록

제공해 주신 기존 `vehicle.json`의 차량 정보는 초기 데이터로 반영했습니다. 이후 등록·수정한 정보는 `data\vehicle.json`에 저장됩니다.


## 이번 수정 사항
- 경고등 진단에서 선택한 경고등의 계기판 스타일 안내 이미지를 표시합니다. 이미지는 이해를 돕는 예시 일러스트이며, 제조사 순정 계기판 사진이나 자동 판독 결과는 아닙니다.
- 차량 관리 제조사는 현대자동차로 고정했습니다.
- 차량 모델은 목록에서 선택하며, 목록에 없는 모델은 '기타(직접 입력)'으로 등록할 수 있습니다.
- 소모품 정비 기록에 마지막 교체 연도와 다음 교체 예정 연도를 각각 입력하고 확인할 수 있습니다.
- 기존 차량 데이터의 제조사 값은 현대자동차로 정규화하며, 기존 정비 기록은 보존합니다.


## 경고등 이미지
- `assets/warnings/` 폴더에 경고등별 PNG 이미지가 들어 있습니다.
- 경고등 진단 화면에서 선택한 항목에 맞는 이미지가 표시됩니다.
- 이미지는 이해를 돕기 위한 시각 자료이며, 실제 계기판 표시는 차종·연식에 따라 다를 수 있습니다.
