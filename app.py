from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "diagnosis_history.json"
VEHICLE_FILE = DATA_DIR / "vehicle.json"

st.set_page_config(
    page_title="현대자동차 앱 개발",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded",
)

WARNINGS = {
    "엔진 경고등": {
        "symbol": "🟠", "level": "주의",
        "meaning": "엔진 제어 또는 배출가스 관련 시스템에서 이상이 감지되었을 수 있습니다.",
        "causes": ["산소 센서 또는 배출가스 센서 이상", "점화 플러그·점화 코일 문제", "연료 공급 계통 이상"],
        "action": "차량 떨림, 출력 저하, 이상 소음 여부를 확인하고 빠른 시일 내 점검받으세요. 엔진이 심하게 떨리거나 출력이 급격히 떨어지면 안전한 곳에 정차하세요.",
    },
    "엔진 오일 압력 경고등": {
        "symbol": "🔴", "level": "긴급",
        "meaning": "엔진 오일 압력이 정상보다 낮을 가능성이 있습니다.",
        "causes": ["엔진 오일 부족 또는 누유", "오일 펌프 이상", "오일 압력 센서 또는 윤활 계통 문제"],
        "action": "안전한 장소에 즉시 정차하고 엔진을 끄세요. 오일 압력 경고가 켜진 상태로 계속 주행하면 엔진이 심각하게 손상될 수 있습니다. 재시동·주행 전 전문 점검을 받으세요.",
    },
    "냉각수 온도 경고등": {
        "symbol": "🔴", "level": "긴급",
        "meaning": "엔진 냉각수 온도가 과도하게 높을 수 있습니다.",
        "causes": ["냉각수 부족 또는 누수", "냉각팬·서모스탯 이상", "라디에이터 또는 워터펌프 문제"],
        "action": "안전한 곳에 정차하고 엔진을 끄세요. 뜨거운 상태에서 냉각수 캡을 열지 마세요. 온도가 내려간 뒤에도 누수나 경고가 있으면 운행하지 말고 도움을 요청하세요.",
    },
    "타이어 공기압 경고등": {
        "symbol": "🟡", "level": "주의",
        "meaning": "타이어 공기압이 낮거나 타이어 공기압 감지 시스템에 이상이 있을 수 있습니다.",
        "causes": ["기온 변화에 따른 공기압 저하", "못·이물질 등에 의한 펑크", "TPMS 센서 또는 배터리 이상"],
        "action": "안전한 장소에서 타이어 외관을 확인하고 냉간 상태에서 차량 문 안쪽 라벨의 권장 공기압에 맞추세요. 타이어가 손상됐거나 공기압이 빠르게 떨어지면 주행하지 마세요.",
    },
    "배터리 충전 경고등": {
        "symbol": "🔴", "level": "긴급",
        "meaning": "배터리 충전 시스템이 정상적으로 작동하지 않을 수 있습니다.",
        "causes": ["발전기 이상", "구동 벨트 문제", "배터리 단자·배선 접촉 불량"],
        "action": "전기 장치 사용을 줄이고 안전한 장소로 이동해 점검받으세요. 시동이 꺼질 수 있으므로 장거리 주행은 피하세요.",
    },
    "브레이크 경고등": {
        "symbol": "🔴", "level": "긴급",
        "meaning": "주차 브레이크가 작동 중이거나 브레이크액·제동 시스템에 이상이 있을 수 있습니다.",
        "causes": ["주차 브레이크 미해제", "브레이크액 부족 또는 누유", "제동 시스템 이상"],
        "action": "주차 브레이크를 완전히 해제했는지 확인하세요. 경고가 계속되거나 페달 감각·제동 성능이 평소와 다르면 즉시 안전하게 정차하고 운행을 중단하세요.",
    },
    "ABS 경고등": {
        "symbol": "🟡", "level": "주의",
        "meaning": "잠김 방지 브레이크(ABS) 시스템에 이상이 있을 수 있습니다.",
        "causes": ["휠 속도 센서 이상", "센서 배선 또는 커넥터 문제", "ABS 제어 장치 이상"],
        "action": "기본 제동 기능이 남아 있을 수 있지만 ABS 기능은 제한될 수 있습니다. 급제동을 피하고 안전거리를 확보한 뒤 빠르게 점검받으세요. 브레이크 경고등도 함께 켜지면 운행을 중단하세요.",
    },
    "에어백 경고등": {
        "symbol": "🟡", "level": "주의",
        "meaning": "에어백 또는 안전벨트 프리텐셔너 시스템에 이상이 있을 수 있습니다.",
        "causes": ["충돌 센서 또는 배선 이상", "시트 하부 커넥터 접촉 불량", "에어백 제어 장치 이상"],
        "action": "충돌 시 안전장치가 정상 작동하지 않을 수 있으므로 빠른 시일 내 전문 점검을 받으세요. 커넥터를 임의로 분리하지 마세요.",
    },
    "연료 부족 경고등": {
        "symbol": "🟡", "level": "안내",
        "meaning": "연료 잔량이 낮은 상태입니다.",
        "causes": ["연료 잔량 부족", "연료량 센서 오차 가능성"],
        "action": "주행 가능 거리는 운전 조건에 따라 달라집니다. 가까운 주유소에서 연료를 보충하고 연료가 완전히 소진되기 전에 조치하세요.",
    },
    "차체 자세 제어 경고등": {
        "symbol": "🟡", "level": "주의",
        "meaning": "차체 자세 제어(ESC)가 작동 중이거나 시스템에 이상이 있을 수 있습니다.",
        "causes": ["미끄러운 노면에서 시스템 작동", "휠 속도 센서 이상", "ESC 제어 시스템 문제"],
        "action": "점멸은 시스템 작동을 의미할 수 있습니다. 계속 켜져 있으면 기능이 제한될 수 있으므로 급가속·급제동을 피하고 점검받으세요.",
    },
    "전동 파워 스티어링 경고등": {
        "symbol": "🔴", "level": "주의",
        "meaning": "전동식 파워 스티어링(EPS)의 보조 기능에 이상이 있을 수 있습니다.",
        "causes": ["조향 모터 또는 제어 장치 이상", "전원 공급 문제", "조향각 센서 이상"],
        "action": "핸들이 무거워질 수 있습니다. 조향이 어렵거나 불안정하면 안전하게 정차하고 견인 등 도움을 요청하세요.",
    },
    "요소수 경고등": {
        "symbol": "🟡", "level": "주의",
        "meaning": "디젤 차량의 요소수 잔량이 부족하거나 후처리 시스템에 이상이 있을 수 있습니다.",
        "causes": ["요소수 부족", "규격에 맞지 않는 요소수", "요소수 공급·분사 시스템 이상"],
        "action": "차량 설명서에 지정된 규격의 요소수를 보충하세요. 재시동 제한 안내나 시스템 이상 문구가 표시되면 즉시 제조사 안내에 따라 점검받으세요.",
    },
    "연료 필터 경고등": {
        "symbol": "🟡", "level": "주의",
        "meaning": "일부 디젤 차량에서 연료 필터 내 수분 또는 필터 계통 이상을 알릴 수 있습니다.",
        "causes": ["연료 필터 내 수분 축적", "연료 필터 막힘", "수분 감지 센서 이상"],
        "action": "차량 설명서의 안내를 확인하고 빠른 시일 내 정비소에서 점검·수분 제거를 받으세요. 출력 저하나 시동 불량이 있으면 주행을 중단하세요.",
    },
    "전구 고장 경고등": {
        "symbol": "🟡", "level": "안내",
        "meaning": "외부 조명 장치 중 일부가 정상적으로 작동하지 않을 수 있습니다.",
        "causes": ["전구 또는 LED 모듈 고장", "퓨즈·배선 문제", "조명 제어 장치 이상"],
        "action": "안전한 장소에서 전조등, 후미등, 방향지시등, 브레이크등을 확인하세요. 야간·악천후 운행 전 수리하는 것이 안전합니다.",
    },
    "차선 유지 보조 경고등": {
        "symbol": "🟡", "level": "안내",
        "meaning": "차선 유지 보조 시스템이 꺼져 있거나 카메라가 차선을 인식하지 못할 수 있습니다.",
        "causes": ["전방 카메라 시야 가림", "차선 표시가 흐리거나 도로 조건이 좋지 않음", "운전자 보조 시스템 이상"],
        "action": "전방 카메라 주변의 오염·김서림을 확인하세요. 시스템이 작동하지 않을 수 있으므로 운전자가 직접 조향과 차선 유지를 해야 합니다.",
    },
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
:root { --navy:#102b46; --blue:#0878bd; --cyan:#20a4d8; --ink:#172b3d; --muted:#718096; --line:#e5ebf1; }
.stApp { background:#f4f7fa; color:var(--ink); font-family:'Inter','Noto Sans KR',sans-serif; }
header[data-testid="stHeader"] { background:rgba(244,247,250,.92); }
.block-container { max-width:1440px; padding-top:2rem; padding-bottom:3rem; }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#102b46 0%,#153c5d 100%); }
section[data-testid="stSidebar"] * { color:#f4f8fb; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:7px 4px; }
.brand-mark { color:#8ed8ff; font-size:11px; font-weight:800; letter-spacing:2.2px; }
.hero { background:linear-gradient(115deg,#102b46 0%,#15527d 65%,#087fbd 100%); color:white; padding:30px 34px; border-radius:18px; margin-bottom:24px; box-shadow:0 12px 28px rgba(16,43,70,.13); }
.hero h1 { color:white !important; font-size:32px; letter-spacing:-1.2px; margin:5px 0 2px; }
.hero p { color:#d5e7f3; margin:0; font-size:14px; }
.section-kicker { color:#1685bd; font-size:11px; font-weight:800; letter-spacing:1.5px; margin-bottom:5px; }
.panel { background:#fff; border:1px solid var(--line); border-radius:14px; padding:21px 23px; margin:8px 0 15px; box-shadow:0 4px 16px rgba(23,43,61,.035); }
.panel-title { color:#173b58; font-size:18px; font-weight:800; margin-bottom:8px; }
.small-muted { color:#758596; font-size:13px; }
div[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:13px; padding:16px 18px; box-shadow:0 4px 14px rgba(23,43,61,.025); }
div[data-testid="stMetricLabel"] { color:#758596; font-weight:600; }
div[data-testid="stMetricValue"] { color:#153b59; font-weight:800; }
.stButton>button, .stDownloadButton>button, button[kind="primary"] { border-radius:9px; min-height:42px; font-weight:700; }
.stButton>button[kind="primary"], button[kind="primary"] { background:#0878bd; border-color:#0878bd; }
.stButton>button:hover { border-color:#0878bd; color:#0878bd; }
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea { border-radius:8px; }
hr { border-color:#e4eaf0; }
footer { visibility:hidden; }

/* Streamlit's dark theme changes native widgets, so keep the custom panels
   and page chrome in sync with it as well. The selector covers both DOM
   shapes used by different Streamlit releases. */
[data-theme="dark"] .stApp,
.stApp[data-theme="dark"] { background:#0f1720 !important; color:#e5edf5 !important; }
[data-theme="dark"] body,
[data-theme="dark"] .stApp,
[data-theme="dark"] [data-testid="stAppViewContainer"],
[data-theme="dark"] [data-testid="stHeader"],
[data-theme="dark"] section.main,
[data-theme="dark"] div[data-testid="stMainBlockContainer"],
.stApp[data-theme="dark"],
.stApp[data-theme="dark"] [data-testid="stAppViewContainer"],
.stApp[data-theme="dark"] section.main,
.stApp[data-theme="dark"] div[data-testid="stMainBlockContainer"] { background-color:#0f1720 !important; }
[data-theme="dark"] [data-testid="stMainBlockContainer"] p,
[data-theme="dark"] [data-testid="stMainBlockContainer"] label,
[data-theme="dark"] [data-testid="stMainBlockContainer"] h1,
[data-theme="dark"] [data-testid="stMainBlockContainer"] h2,
[data-theme="dark"] [data-testid="stMainBlockContainer"] h3,
.stApp[data-theme="dark"] [data-testid="stMainBlockContainer"] p,
.stApp[data-theme="dark"] [data-testid="stMainBlockContainer"] label,
.stApp[data-theme="dark"] [data-testid="stMainBlockContainer"] h1,
.stApp[data-theme="dark"] [data-testid="stMainBlockContainer"] h2,
.stApp[data-theme="dark"] [data-testid="stMainBlockContainer"] h3 { color:#e5edf5 !important; }
[data-theme="dark"] header[data-testid="stHeader"],
.stApp[data-theme="dark"] header[data-testid="stHeader"] { background:rgba(15,23,32,.94) !important; }
[data-theme="dark"] .panel,
.stApp[data-theme="dark"] .panel,
[data-theme="dark"] div[data-testid="stMetric"],
.stApp[data-theme="dark"] div[data-testid="stMetric"] { background:#17232f !important; border-color:#304252 !important; color:#e5edf5 !important; box-shadow:0 4px 16px rgba(0,0,0,.22); }
[data-theme="dark"] .panel-title,
.stApp[data-theme="dark"] .panel-title { color:#b9e5ff !important; }
[data-theme="dark"] .small-muted,
[data-theme="dark"] div[data-testid="stMetricLabel"],
.stApp[data-theme="dark"] .small-muted,
.stApp[data-theme="dark"] div[data-testid="stMetricLabel"] { color:#a6b8c8 !important; }
[data-theme="dark"] div[data-testid="stMetricValue"],
.stApp[data-theme="dark"] div[data-testid="stMetricValue"] { color:#e8f5ff !important; }
[data-theme="dark"] hr,
.stApp[data-theme="dark"] hr { border-color:#304252 !important; }
[data-theme="dark"] div[data-baseweb="input"] input,
[data-theme="dark"] div[data-baseweb="textarea"] textarea,
.stApp[data-theme="dark"] div[data-baseweb="input"] input,
.stApp[data-theme="dark"] div[data-baseweb="textarea"] textarea { background:#17232f !important; color:#edf6ff !important; border-color:#405365 !important; }
[data-theme="dark"] [data-baseweb="select"] > div,
.stApp[data-theme="dark"] [data-baseweb="select"] > div { background:#17232f !important; border-color:#405365 !important; color:#edf6ff !important; }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)



def warning_icon_svg(symbol: str, level: str) -> bytes:
    """간단한 계기판 스타일 경고등 일러스트(SVG)."""
    color = "#dc2626" if level == "긴급" else ("#d69e00" if level == "주의" else "#2583b8")
    # SVG image is intentionally illustrative, not an OEM-specific dashboard photograph.
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="520" height="260" viewBox="0 0 520 260">
      <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#172b3d"/><stop offset="1" stop-color="#304b61"/></linearGradient>
      <filter id="shadow"><feGaussianBlur stdDeviation="8"/></filter></defs>
      <rect x="8" y="8" width="504" height="244" rx="26" fill="url(#bg)"/>
      <circle cx="260" cy="124" r="82" fill="{color}" opacity=".18" filter="url(#shadow)"/>
      <circle cx="260" cy="124" r="68" fill="#101e2b" stroke="{color}" stroke-width="5"/>
      <text x="260" y="151" text-anchor="middle" font-size="76" font-family="sans-serif">{symbol}</text>
      <text x="260" y="222" text-anchor="middle" font-size="17" fill="#dbe7ef" font-family="sans-serif">VEHICLE WARNING INDICATOR</text>
    </svg>"""
    return svg.encode("utf-8")


HYUNDAI_MODELS = [
    "아반떼", "쏘나타", "그랜저", "아이오닉 6", "아이오닉 5", "아이오닉 5 N",
    "코나", "코나 일렉트릭", "투싼", "싼타페", "팰리세이드", "베뉴",
    "캐스퍼", "캐스퍼 일렉트릭", "스타리아", "포터 II", "마이티",
    "넥쏘", "아이오닉 9", "기타(직접 입력)"
]


def read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, TypeError):
        return default


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def load_history():
    data = read_json(HISTORY_FILE, [])
    return data if isinstance(data, list) else []


def save_history(data):
    write_json(HISTORY_FILE, data)


def empty_vehicle_data():
    return {"vehicles": [], "maintenance": []}


def load_vehicle_data():
    data = read_json(VEHICLE_FILE, empty_vehicle_data())
    # Upgrade the earlier single-vehicle JSON format without losing its contents.
    if isinstance(data, dict) and "vehicles" not in data:
        if data.get("brand") or data.get("model"):
            vehicle = {
                "id": str(uuid.uuid4()),
                "brand": data.get("brand", ""),
                "model": data.get("model", ""),
                "year": int(data.get("year", datetime.now().year)),
                "mileage": int(data.get("mileage", 0)),
                "nickname": "내 차량",
            }
            data = {"vehicles": [vehicle], "maintenance": []}
            write_json(VEHICLE_FILE, data)
        else:
            data = empty_vehicle_data()
    if not isinstance(data, dict):
        data = empty_vehicle_data()
    data.setdefault("vehicles", [])
    data.setdefault("maintenance", [])
    # 차량 관리 제조사는 현대자동차로 고정합니다.
    for vehicle in data["vehicles"]:
        vehicle["brand"] = "현대자동차"
    for plan in data["maintenance"]:
        plan.setdefault("next_replace_year", "")
    return data


if "history" not in st.session_state:
    st.session_state.history = load_history()
if "vehicle_data" not in st.session_state:
    st.session_state.vehicle_data = load_vehicle_data()


def refresh_vehicle_data():
    st.session_state.vehicle_data = load_vehicle_data()


def persist_vehicle_data():
    write_json(VEHICLE_FILE, st.session_state.vehicle_data)


def add_history(warning_name):
    info = WARNINGS[warning_name]
    record = {
        "id": str(uuid.uuid4()),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "warning": warning_name,
        "level": info["level"],
        "meaning": info["meaning"],
        "action": info["action"],
    }
    st.session_state.history.insert(0, record)
    save_history(st.session_state.history)


def header():
    st.markdown("""
    <div class="hero">
      <div class="brand-mark">SMART VEHICLE CARE PLATFORM</div>
      <h1>현대자동차 앱 개발</h1>
      <p>차량 상태 확인부터 경고등 진단과 정비 이력 관리까지</p>
    </div>
    """, unsafe_allow_html=True)


header()
menu_items = ["대시보드", "경고등 진단", "사진 등록", "진단 기록", "차량 관리", "서비스 안내"]
if "current_menu" not in st.session_state:
    st.session_state.current_menu = "대시보드"

with st.sidebar:
    st.markdown("## 🚘 현대자동차 앱 개발")
    st.caption("VEHICLE CARE SYSTEM")
    st.divider()
    menu = st.radio("메뉴", menu_items, key="current_menu", label_visibility="collapsed")
    st.divider()
    st.caption("현대자동차 앱 개발 · 개인 차량 관리용")
    st.caption("안전 관련 판단은 차량 설명서와 전문 정비 안내를 우선하세요.")

vehicles = st.session_state.vehicle_data["vehicles"]
maintenance = st.session_state.vehicle_data["maintenance"]
history = st.session_state.history

if menu == "대시보드":
    st.markdown('<div class="section-kicker">OVERVIEW</div>', unsafe_allow_html=True)
    st.title("내 차량 대시보드")
    st.caption("등록한 차량과 최근 진단·정비 현황을 한눈에 확인합니다.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("등록 차량", f"{len(vehicles)}대")
    c2.metric("진단 항목", f"{len(WARNINGS)}종")
    c3.metric("누적 진단", f"{len(history)}건")
    c4.metric("정비 기록", f"{len(maintenance)}건")
    st.markdown('<div class="panel"><div class="panel-title">차량 관리 현황</div><div class="small-muted">등록된 차량과 정비 일정을 기준으로 표시합니다. 실제 차량 센서 데이터와 연결된 상태 정보는 아닙니다.</div></div>', unsafe_allow_html=True)
    if vehicles:
        cols = st.columns(min(3, len(vehicles)))
        for i, vehicle in enumerate(vehicles):
            with cols[i % len(cols)]:
                st.markdown(f"""
                <div class="panel">
                  <div class="small-muted">{vehicle.get('nickname') or 'MY VEHICLE'}</div>
                  <div class="panel-title">🚗 {vehicle.get('brand','')} {vehicle.get('model','')}</div>
                  <div class="small-muted">{vehicle.get('year','-')}년식 · {int(vehicle.get('mileage',0)):,} km</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("등록된 차량이 없습니다. 차량 관리 메뉴에서 내 차량을 등록해 주세요.")
    left, right = st.columns(2)
    with left:
        st.subheader("최근 진단 기록")
        if history:
            for item in history[:4]:
                st.write(f"**{item.get('warning','진단')}** · {item.get('level','')}  ")
                st.caption(item.get("time", ""))
        else:
            st.caption("아직 저장된 진단 기록이 없습니다.")
    with right:
        st.subheader("최근 정비 기록")
        if maintenance:
            for item in sorted(maintenance, key=lambda x: x.get("created_at", ""), reverse=True)[:4]:
                st.write(f"**{item.get('part','부품')}** · 마지막 교체 {item.get('year','')}년")
                st.caption(f"{item.get('vehicle_name', '차량')} · 다음 교체 예정 {item.get('next_replace_year') or '미입력'}년")
        else:
            st.caption("아직 등록된 부품 교체 기록이 없습니다.")
    st.warning("빨간색 경고등, 제동·조향 이상, 과열, 오일 압력 경고가 나타나면 안전한 장소에 정차하고 차량 설명서의 지침을 따르세요.")

elif menu == "경고등 진단":
    st.markdown('<div class="section-kicker">WARNING LIGHT DIAGNOSIS</div>', unsafe_allow_html=True)
    st.title("경고등 진단")
    st.caption("계기판에 표시된 경고등을 선택해 의미와 권장 조치를 확인하세요.")
    selected = st.selectbox("경고등 종류 선택", list(WARNINGS.keys()))
    item = WARNINGS[selected]
    # 경고등별 개별 이미지(PNG)를 표시합니다.
    WARNING_IMAGE_FILES = {
        "엔진 경고등": "engine.png",
        "엔진 오일 압력 경고등": "oil_pressure.png",
        "냉각수 온도 경고등": "coolant_temp.png",
        "타이어 공기압 경고등": "tpms.png",
        "배터리 충전 경고등": "battery.png",
        "브레이크 경고등": "brake.png",
        "ABS 경고등": "abs.png",
        "에어백 경고등": "airbag.png",
        "연료 부족 경고등": "fuel.png",
        "차체 자세 제어 경고등": "esc.png",
        "전동 파워 스티어링 경고등": "eps.png",
        "요소수 경고등": "adblue.png",
        "연료 필터 경고등": "fuel_filter.png",
        "전구 고장 경고등": "bulb.png",
        "차선 유지 보조 경고등": "lane_assist.png",
    }
    image_name = WARNING_IMAGE_FILES.get(selected)
    image_path = BASE_DIR / "assets" / "warnings" / image_name if image_name else None
    if image_path and image_path.exists():
        st.image(str(image_path), caption=f"{selected} 계기판 표시 예시", width=520)
    else:
        st.warning("해당 경고등 이미지를 찾을 수 없습니다. 프로젝트의 assets/warnings 폴더를 확인하세요.")
    st.caption("경고등마다 구분되는 개별 이미지입니다. 실제 계기판 모양과 색상은 차종·연식·트림에 따라 다를 수 있습니다.")
    st.markdown(f"""
    <div class="panel">
      <div class="small-muted">SELECTED WARNING</div>
      <div class="panel-title" style="font-size:23px">{item['symbol']} {selected}</div>
      <b>위험 단계 · {item['level']}</b>
      <p>{item['meaning']}</p>
    </div>
    """, unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        st.subheader("예상 발생 원인")
        for cause in item["causes"]:
            st.write(f"• {cause}")
    with b:
        st.subheader("권장 대응 방법")
        if item["level"] == "긴급":
            st.error(item["action"])
        elif item["level"] == "주의":
            st.warning(item["action"])
        else:
            st.info(item["action"])
    if st.button("진단 기록 저장", type="primary", use_container_width=True):
        add_history(selected)
        st.success("진단 기록을 저장했습니다.")
    st.caption("이 기능은 선택한 경고등에 대한 일반 안내이며, 차량의 실제 고장코드를 판독하거나 정비 진단을 대신하지 않습니다. 차종·연식·시장에 따라 경고등 의미가 다를 수 있습니다.")

elif menu == "사진 등록":
    st.markdown('<div class="section-kicker">IMAGE UPLOAD</div>', unsafe_allow_html=True)
    st.title("경고등 사진 등록")
    st.caption("정차 상태에서 촬영한 계기판 사진을 업로드해 확인할 수 있습니다.")
    uploaded = st.file_uploader("이미지 파일 선택", type=["png", "jpg", "jpeg", "webp"])
    if uploaded:
        st.image(uploaded, caption="업로드한 계기판 사진", use_container_width=True)
        st.info("현재 버전은 이미지 업로드와 미리보기 기능을 제공합니다. 사진 속 경고등 자동 인식·AI 판독 기능은 아직 연결되어 있지 않습니다.")
    st.warning("주행 중 사진을 촬영하거나 휴대전화를 조작하지 마세요. 반드시 안전한 장소에 정차한 뒤 이용하세요.")

elif menu == "진단 기록":
    st.markdown('<div class="section-kicker">DIAGNOSIS HISTORY</div>', unsafe_allow_html=True)
    st.title("진단 기록")
    if not history:
        st.info("저장된 진단 기록이 없습니다. 경고등 진단 메뉴에서 기록을 저장할 수 있습니다.")
    else:
        st.metric("전체 진단 기록", f"{len(history)}건")
        for record in history:
            with st.expander(f"{record.get('time','')}  ·  {record.get('warning','')}  ·  {record.get('level','')}"):
                st.write(record.get("meaning", ""))
                st.write("**권장 조치**")
                st.write(record.get("action", ""))
        df = pd.DataFrame(history)
        st.download_button("진단 기록 CSV 다운로드", df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="car_care_diagnosis_history.csv", mime="text/csv")
        if st.button("전체 진단 기록 삭제"):
            st.session_state.history = []
            save_history([])
            st.rerun()

elif menu == "차량 관리":
    st.markdown('<div class="section-kicker">MY VEHICLES & MAINTENANCE</div>', unsafe_allow_html=True)
    st.title("차량 관리")
    st.caption("차량을 여러 대 등록하고 부품 교체 이력을 직접 관리할 수 있습니다.")
    with st.expander("＋ 새 차량 등록", expanded=not bool(vehicles)):
        with st.form("add_vehicle_form", clear_on_submit=True):
            st.text_input("제조사", value="현대자동차", disabled=True)
            model_choice = st.selectbox("차량 모델 선택", HYUNDAI_MODELS, index=0)
            custom_model = ""
            if model_choice == "기타(직접 입력)":
                custom_model = st.text_input("차량 모델 직접 입력", placeholder="차량 모델명을 입력하세요")
            c, d = st.columns(2)
            year = c.number_input("차량 연식", min_value=1950, max_value=2100, value=datetime.now().year, step=1)
            mileage = d.number_input("현재 주행거리 (km)", min_value=0, max_value=2_000_000, value=0, step=1000)
            nickname = st.text_input("차량 별칭 (선택)", placeholder="예: 출퇴근 차량")
            submitted = st.form_submit_button("차량 등록", type="primary")
            if submitted:
                model = custom_model.strip() if model_choice == "기타(직접 입력)" else model_choice
                if not model:
                    st.error("차량 모델을 선택하거나 입력해 주세요.")
                else:
                    st.session_state.vehicle_data["vehicles"].append({
                        "id": str(uuid.uuid4()), "brand": "현대자동차", "model": model,
                        "year": int(year), "mileage": int(mileage), "nickname": nickname.strip()
                    })
                    persist_vehicle_data()
                    st.success("현대자동차 차량을 등록했습니다.")
                    st.rerun()

    if vehicles:
        st.subheader("등록된 차량")
        for vehicle in list(vehicles):
            vid = vehicle["id"]
            vehicle_name = f"{vehicle.get('brand','')} {vehicle.get('model','')}".strip()
            with st.container(border=True):
                top1, top2 = st.columns([4, 1])
                with top1:
                    st.markdown(f"### 🚘 {vehicle_name}")
                    st.caption(f"{vehicle.get('nickname') or '내 차량'} · {vehicle.get('year','-')}년식 · {int(vehicle.get('mileage',0)):,} km")
                with top2:
                    if st.button("차량 삭제", key=f"del_vehicle_{vid}"):
                        st.session_state[f"confirm_vehicle_{vid}"] = True
                if st.session_state.get(f"confirm_vehicle_{vid}", False):
                    st.error("이 차량과 연결된 부품 교체 기록을 함께 삭제할까요?")
                    yes, no = st.columns(2)
                    if yes.button("삭제 진행", key=f"yes_vehicle_{vid}", type="primary"):
                        st.session_state.vehicle_data["vehicles"] = [v for v in st.session_state.vehicle_data["vehicles"] if v["id"] != vid]
                        st.session_state.vehicle_data["maintenance"] = [m for m in st.session_state.vehicle_data["maintenance"] if m.get("vehicle_id") != vid]
                        persist_vehicle_data()
                        st.session_state.pop(f"confirm_vehicle_{vid}", None)
                        st.rerun()
                    if no.button("취소", key=f"no_vehicle_{vid}"):
                        st.session_state.pop(f"confirm_vehicle_{vid}", None)
                        st.rerun()
                with st.expander("차량 정보 수정"):
                    with st.form(f"edit_vehicle_{vid}"):
                        st.text_input("제조사", value="현대자동차", disabled=True, key=f"brand_fixed_{vid}")
                        current_model = vehicle.get("model", "")
                        model_options = HYUNDAI_MODELS
                        selected_model = current_model if current_model in model_options else "기타(직접 입력)"
                        new_model_choice = st.selectbox("차량 모델 선택", model_options,
                            index=model_options.index(selected_model), key=f"model_choice_{vid}")
                        new_custom_model = ""
                        if new_model_choice == "기타(직접 입력)":
                            new_custom_model = st.text_input("차량 모델 직접 입력", value=current_model,
                                key=f"model_custom_{vid}")
                        e3, e4 = st.columns(2)
                        new_year = e3.number_input("연식", min_value=1950, max_value=2100, value=int(vehicle.get("year", datetime.now().year)), key=f"year_{vid}")
                        new_mileage = e4.number_input("주행거리 (km)", min_value=0, max_value=2_000_000, value=int(vehicle.get("mileage", 0)), key=f"mileage_{vid}")
                        new_nickname = st.text_input("별칭", value=vehicle.get("nickname", ""), key=f"nick_{vid}")
                        if st.form_submit_button("변경 내용 저장"):
                            chosen_model = new_custom_model.strip() if new_model_choice == "기타(직접 입력)" else new_model_choice
                            if not chosen_model:
                                st.error("차량 모델을 선택하거나 입력해 주세요.")
                            else:
                                vehicle.update({"brand": "현대자동차", "model": chosen_model, "year": int(new_year), "mileage": int(new_mileage), "nickname": new_nickname.strip()})
                                persist_vehicle_data()
                                st.success("차량 정보를 수정했습니다.")
                                st.rerun()
                st.markdown("**부품 교체 기록**")
                with st.form(f"add_maintenance_{vid}", clear_on_submit=True):
                    m1, m2 = st.columns([2, 1])
                    part = m1.text_input("교체 부품 / 정비 항목", placeholder="예: 엔진오일, 타이어, 배터리")
                    replace_year = m2.number_input("마지막 교체 연도", min_value=1950, max_value=2100, value=datetime.now().year, step=1, key=f"replace_year_{vid}")
                    next_replace_year = st.number_input("다음 교체 예정 연도", min_value=1950, max_value=2100, value=min(2100, datetime.now().year + 1), step=1, key=f"next_replace_year_{vid}")
                    memo = st.text_input("메모 (선택)", placeholder="예: 제조사 권장 규격으로 교체")
                    if st.form_submit_button("교체 기록 추가"):
                        if not part.strip():
                            st.error("부품 또는 정비 항목을 입력해 주세요.")
                        else:
                            st.session_state.vehicle_data["maintenance"].append({
                                "id": str(uuid.uuid4()), "vehicle_id": vid, "vehicle_name": vehicle_name,
                                "part": part.strip(), "year": int(replace_year),
                                "next_replace_year": int(next_replace_year), "memo": memo.strip(),
                                "created_at": datetime.now().isoformat(timespec="seconds")
                            })
                            persist_vehicle_data()
                            st.success("부품 교체 기록을 추가했습니다.")
                            st.rerun()
                related = [m for m in st.session_state.vehicle_data["maintenance"] if m.get("vehicle_id") == vid]
                if related:
                    for plan in sorted(related, key=lambda x: x.get("year", 0), reverse=True):
                        r1, r2, r3 = st.columns([3, 2, 1])
                        r1.write(f"**{plan.get('part','')}**")
                        r1.caption(plan.get("memo") or "메모 없음")
                        r2.write(f"마지막 교체: {plan.get('year','')}년")
                        r2.caption(f"다음 교체 예정: {plan.get('next_replace_year') or '미입력'}년")
                        if r3.button("기록 삭제", key=f"del_maint_{plan['id']}"):
                            st.session_state.vehicle_data["maintenance"] = [m for m in st.session_state.vehicle_data["maintenance"] if m["id"] != plan["id"]]
                            persist_vehicle_data()
                            st.rerun()
                else:
                    st.caption("등록된 부품 교체 기록이 없습니다.")
    st.caption("마지막 교체 연도와 다음 교체 예정 연도는 사용자가 직접 입력·관리합니다. 실제 교체 주기는 주행거리·운행 환경·차량 설명서 및 현대자동차 정비 지침을 확인하세요.")

elif menu == "서비스 안내":
    st.markdown('<div class="section-kicker">ABOUT THE SERVICE</div>', unsafe_allow_html=True)
    st.title("현대자동차 앱 개발 소개")
    st.markdown("""
    <div class="panel">
      <div class="panel-title">운전자를 위한 차량 관리 도우미</div>
      <p>현대자동차 앱 개발은 계기판 경고등에 관한 일반 정보와 차량별 정비 기록을 한곳에서 관리하는 개인용 시제품입니다.</p>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("제공 기능")
    for feature in ["15종 경고등 설명과 권장 대응 안내", "계기판 사진 업로드 및 미리보기", "진단 기록 저장 및 CSV 내보내기", "여러 차량 등록·수정·삭제", "마지막 교체 연도·다음 교체 예정 연도 및 메모 기록", "차량별 정비 이력 삭제"]:
        st.write(f"✓ {feature}")
    st.subheader("기능 범위 안내")
    st.info("현재 버전은 실제 차량 OBD/ECU 데이터, 정비소 예약, 이미지 자동 판독과 연결되어 있지 않습니다. 차량 상태 수치는 사용자가 직접 입력한 정보만 저장합니다.")
    st.warning("이 프로그램은 정비사 진단이나 차량 제조사의 공식 안내를 대체하지 않습니다. 안전과 관련된 경고가 발생하면 차량 설명서와 전문 정비사의 지침을 따르세요.")

st.divider()
st.caption("현대자동차 앱 개발 © 2026 · Vehicle Care Prototype · 안전한 운전은 정확한 점검에서 시작됩니다.")
