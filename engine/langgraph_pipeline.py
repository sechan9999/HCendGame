"""
LangGraph 다단계 에이전트 파이프라인
=====================================
StateGraph 기반 5단계 FWA 검증 워크플로우.

Pipeline:
  [Parse] → [Rule Engine] → [AI Analysis] → [Risk Scoring] → [Action/Escalation]

LangGraph 미설치 시 순차 실행 fallback 자동 전환.
"""
from typing import TypedDict, List, Dict, Annotated
import json
import logging
import operator
from datetime import datetime

logger = logging.getLogger(__name__)

# LangGraph 임포트 (설치 안 됐을 경우 fallback)
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("langgraph not installed. Using sequential fallback.")

from engine.rules import RxHCCRuleEngine, ClaimRecord, Severity


# ============================================================
# 1. State 스키마 정의
# ============================================================
class FWAPipelineState(TypedDict):
    """LangGraph 파이프라인 상태"""
    claim: Dict                                         # 원본 청구 데이터
    claim_record: Dict                                  # 파싱된 ClaimRecord
    rule_results: List[Dict]                            # 룰엔진 결과
    ai_analysis: Dict                                   # AI 분석 결과
    risk_score: float                                   # 종합 리스크 스코어
    risk_level: str                                     # HIGH / MEDIUM / LOW / MINIMAL
    recommended_action: str                             # BLOCK / REVIEW / MONITOR / APPROVE
    should_escalate: bool                               # 에스컬레이션 필요 여부
    escalation_reason: str                              # 사유
    stage: str                                          # 현재 단계
    alerts_sent: List[str]                              # 전송된 알림 채널 목록
    logs: Annotated[List[Dict], operator.add]           # 파이프라인 로그 (누적)
    metadata: Dict                                      # 메타데이터


# ============================================================
# 2. 노드 함수들 (각 단계)
# ============================================================
def node_parse_claim(state: FWAPipelineState) -> dict:
    """Stage 1: 청구 데이터 파싱 및 정규화"""
    logger.info("[Pipeline] Stage 1: Parsing claim")
    try:
        record = ClaimRecord.from_dict(state["claim"])
        return {
            "claim_record": {
                "claim_id": record.claim_id,
                "patient_id": record.patient_id,
                "icd_codes": record.icd_codes,
                "ndc_codes": record.ndc_codes,
                "hcc_codes": record.hcc_codes,
                "provider_id": record.provider_id,
                "claim_date": record.claim_date,
                "claim_amount": record.claim_amount,
            },
            "stage": "parsed",
            "logs": [{"stage": "parse", "status": "ok", "ts": _now(),
                      "message": f"Parsed: ICD={len(record.icd_codes)}, NDC={len(record.ndc_codes)}"}]
        }
    except Exception as e:
        return {
            "stage": "parse_error",
            "should_escalate": True,
            "escalation_reason": f"Parse error: {e}",
            "logs": [{"stage": "parse", "status": "error", "ts": _now(), "message": str(e)}]
        }


def node_rule_engine(state: FWAPipelineState) -> dict:
    """Stage 2: 룰엔진 검증"""
    logger.info("[Pipeline] Stage 2: Rule engine")
    if state["stage"] == "parse_error":
        return {"logs": [{"stage": "rules", "status": "skipped", "ts": _now(), "message": "Parse error — skipped"}]}

    try:
        record = ClaimRecord.from_dict(state["claim_record"])
        engine = RxHCCRuleEngine()
        results = engine.validate(record)
        result_dicts = [r.to_dict() for r in results]

        critical_count = sum(1 for r in results if r.severity == Severity.CRITICAL)
        warning_count = sum(1 for r in results if r.severity == Severity.WARNING)

        escalate = critical_count > 0
        reason = f"{critical_count} CRITICAL, {warning_count} WARNING" if escalate else ""

        return {
            "rule_results": result_dicts,
            "should_escalate": escalate,
            "escalation_reason": reason,
            "stage": "rules_complete",
            "logs": [{"stage": "rules", "status": "ok", "ts": _now(),
                      "message": f"Rules: {critical_count} CRITICAL, {warning_count} WARNING, {len(results)} total"}]
        }
    except Exception as e:
        return {
            "stage": "rules_error",
            "should_escalate": True,
            "escalation_reason": f"Rule engine error: {e}",
            "logs": [{"stage": "rules", "status": "error", "ts": _now(), "message": str(e)}]
        }


def node_ai_analysis(state: FWAPipelineState) -> dict:
    """Stage 3: OpenAI GPT AI 분석"""
    logger.info("[Pipeline] Stage 3: AI analysis")
    if state["stage"] in ("parse_error", "rules_error"):
        return {"logs": [{"stage": "ai", "status": "skipped", "ts": _now(), "message": "Prior error — skipped"}]}

    try:
        from engine.ai_analyzer import FWAAIAnalyzer
        analyzer = FWAAIAnalyzer()
        result = analyzer.analyze_claim(state["claim"], state.get("rule_results", []))
        return {
            "ai_analysis": result.to_dict(),
            "stage": "ai_complete",
            "logs": [{"stage": "ai", "status": "ok", "ts": _now(),
                      "message": f"AI: risk={result.risk_level}, prob={result.fraud_probability:.2f}"}]
        }
    except Exception as e:
        logger.warning(f"AI analysis failed: {e}")
        return {
            "ai_analysis": {},
            "stage": "ai_fallback",
            "logs": [{"stage": "ai", "status": "fallback", "ts": _now(), "message": f"Fallback: {e}"}]
        }


def node_risk_scoring(state: FWAPipelineState) -> dict:
    """Stage 4: 종합 리스크 스코어링"""
    logger.info("[Pipeline] Stage 4: Risk scoring")
    severity_scores = {"CRITICAL": 10, "WARNING": 5, "INFO": 1, "PASS": 0}

    rule_score = sum(
        severity_scores.get(r.get("severity", "INFO"), 0)
        for r in state.get("rule_results", [])
    )

    ai_prob = state.get("ai_analysis", {}).get("fraud_probability", 0)
    ai_score = ai_prob * 20  # AI 스코어 (최대 20)

    total = rule_score + ai_score

    if total >= 25:
        level, action = "HIGH", "BLOCK"
    elif total >= 15:
        level, action = "MEDIUM", "REVIEW"
    elif total >= 7:
        level, action = "LOW", "MONITOR"
    else:
        level, action = "MINIMAL", "APPROVE"

    return {
        "risk_score": round(total, 2),
        "risk_level": level,
        "recommended_action": action,
        "stage": "scored",
        "logs": [{"stage": "scoring", "status": "ok", "ts": _now(),
                  "message": f"Score: {total:.1f} (rule={rule_score}, ai={ai_score:.1f}) → {level}/{action}"}]
    }


def node_action(state: FWAPipelineState) -> dict:
    """Stage 5: 최종 조치 결정 및 알림"""
    logger.info("[Pipeline] Stage 5: Action/Escalation")
    alerts_sent = []

    if state.get("should_escalate") or state.get("risk_level") in ("HIGH", "MEDIUM"):
        # 알림 전송 시도
        try:
            from engine.alerts import AlertManager
            mgr = AlertManager()
            claim_id = state.get("claim", {}).get("claim_id", "UNKNOWN")
            risk = state.get("risk_level", "UNKNOWN")
            action = state.get("recommended_action", "REVIEW")
            score = state.get("risk_score", 0)

            message = (
                f"🚨 *FWA Alert*\n"
                f"• Claim: `{claim_id}`\n"
                f"• Risk: *{risk}* (Score: {score})\n"
                f"• Action: *{action}*\n"
                f"• Reason: {state.get('escalation_reason', 'High risk detected')}"
            )
            sent = mgr.send_all(message)
            alerts_sent = sent
        except Exception as e:
            logger.warning(f"Alert failed: {e}")

    return {
        "stage": "complete",
        "alerts_sent": alerts_sent,
        "logs": [{"stage": "action", "status": "ok", "ts": _now(),
                  "message": f"Action={state.get('recommended_action','N/A')}, Alerts={alerts_sent}"}]
    }


# ============================================================
# 3. 라우터 (조건부 분기)
# ============================================================
def route_after_parse(state: FWAPipelineState) -> str:
    if state["stage"] == "parse_error":
        return "action"  # 파싱 실패 → 바로 에스컬레이션
    return "rule_engine"


def route_after_rules(state: FWAPipelineState) -> str:
    if state["stage"] == "rules_error":
        return "action"
    return "ai_analysis"


# ============================================================
# 4. 그래프 빌더
# ============================================================
def build_fwa_pipeline():
    """LangGraph 파이프라인 구성"""
    if not LANGGRAPH_AVAILABLE:
        return None

    workflow = StateGraph(FWAPipelineState)

    # 노드 등록
    workflow.add_node("parse", node_parse_claim)
    workflow.add_node("rule_engine", node_rule_engine)
    workflow.add_node("ai_analysis", node_ai_analysis)
    workflow.add_node("scoring", node_risk_scoring)
    workflow.add_node("action", node_action)

    # 엣지 정의
    workflow.set_entry_point("parse")
    workflow.add_conditional_edges("parse", route_after_parse,
                                   {"rule_engine": "rule_engine", "action": "action"})
    workflow.add_conditional_edges("rule_engine", route_after_rules,
                                   {"ai_analysis": "ai_analysis", "action": "action"})
    workflow.add_edge("ai_analysis", "scoring")
    workflow.add_edge("scoring", "action")
    workflow.add_edge("action", END)

    return workflow.compile()


# ============================================================
# 5. 메인 실행 함수
# ============================================================
def run_fwa_pipeline(claim_data: Dict) -> FWAPipelineState:
    """
    FWA 파이프라인 실행 (LangGraph 또는 순차 fallback).
    
    Returns:
        FWAPipelineState 전체 상태
    """
    initial_state: FWAPipelineState = {
        "claim": claim_data,
        "claim_record": {},
        "rule_results": [],
        "ai_analysis": {},
        "risk_score": 0.0,
        "risk_level": "MINIMAL",
        "recommended_action": "APPROVE",
        "should_escalate": False,
        "escalation_reason": "",
        "stage": "init",
        "alerts_sent": [],
        "logs": [],
        "metadata": {"started_at": _now(), "engine": "langgraph" if LANGGRAPH_AVAILABLE else "sequential"}
    }

    if LANGGRAPH_AVAILABLE:
        try:
            graph = build_fwa_pipeline()
            result = graph.invoke(initial_state)
            result["metadata"]["completed_at"] = _now()
            return result
        except Exception as e:
            logger.error(f"LangGraph failed, fallback: {e}")

    # Sequential fallback
    return _run_sequential(initial_state)


def _run_sequential(state: FWAPipelineState) -> FWAPipelineState:
    """순차 실행 fallback"""
    state["metadata"]["engine"] = "sequential"

    updates = node_parse_claim(state)
    state.update({k: v for k, v in updates.items() if k != "logs"})
    state["logs"].extend(updates.get("logs", []))

    updates = node_rule_engine(state)
    state.update({k: v for k, v in updates.items() if k != "logs"})
    state["logs"].extend(updates.get("logs", []))

    updates = node_ai_analysis(state)
    state.update({k: v for k, v in updates.items() if k != "logs"})
    state["logs"].extend(updates.get("logs", []))

    updates = node_risk_scoring(state)
    state.update({k: v for k, v in updates.items() if k != "logs"})
    state["logs"].extend(updates.get("logs", []))

    updates = node_action(state)
    state.update({k: v for k, v in updates.items() if k != "logs"})
    state["logs"].extend(updates.get("logs", []))

    state["metadata"]["completed_at"] = _now()
    return state


def _now() -> str:
    return datetime.now().isoformat()
