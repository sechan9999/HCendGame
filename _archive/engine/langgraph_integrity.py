"""
LangGraph-based Integrity Validation Workflow
==============================================
StateGraph를 사용하여 다단계 검증 파이프라인 구현.
"""
from typing import TypedDict, List, Dict, Annotated
from enum import Enum
import json
import logging
import operator

logger = logging.getLogger(__name__)

# LangGraph 임포트 (설치 안 됐을 경우 fallback)
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("langgraph not installed. Using sequential fallback.")

from engine.rules import (
    RxHCCRuleEngine,
    ClaimRecord,
    ValidationResult,
    Severity
)

# ============================================================
# State 정의
# ============================================================
class ValidationState(TypedDict):
    """LangGraph 상태 스키마"""
    claim: Dict # 원본 청구 데이터
    claim_record: Dict # 파싱된 ClaimRecord (dict로 직렬화)
    results: Annotated[List[Dict], operator.add] # 누적되는 검증 결과
    stage: str # 현재 단계
    should_escalate: bool # 에스컬레이션 필요 여부
    escalation_reason: str # 에스컬레이션 사유
    metadata: Dict # 추가 메타데이터

# ============================================================
# 노드 함수들
# ============================================================
def parse_claim(state: ValidationState) -> ValidationState:
    """1단계: 청구 데이터 파싱 및 정규화"""
    logger.info("Stage 1: Parsing claim data")
    try:
        claim_data = state["claim"]
        record = ClaimRecord.from_dict(claim_data)
        
        state["claim_record"] = {
            "claim_id": record.claim_id,
            "patient_id": record.patient_id,
            "icd_codes": record.icd_codes,
            "ndc_codes": record.ndc_codes,
            "hcc_codes": record.hcc_codes,
            "provider_id": record.provider_id,
            "claim_date": record.claim_date,
            "claim_amount": record.claim_amount,
        }
        state["stage"] = "parsed"
        state["results"].append({
            "rule_id": "PARSE-OK",
            "rule_name": "Claim Parsing",
            "severity": "INFO",
            "message": f"Claim {record.claim_id} 파싱 완료. ICD: {len(record.icd_codes)}, NDC: {len(record.ndc_codes)}"
        })
    except Exception as e:
        state["stage"] = "parse_error"
        state["results"].append({
            "rule_id": "PARSE-ERR",
            "rule_name": "Claim Parsing Error",
            "severity": "CRITICAL",
            "message": f"파싱 실패: {str(e)}"
        })
        state["should_escalate"] = True
        state["escalation_reason"] = f"Parse error: {str(e)}"
    
    return state

def run_rule_engine(state: ValidationState) -> ValidationState:
    """2단계: 규칙 엔진 실행"""
    logger.info("Stage 2: Running rule engine")
    if state["stage"] == "parse_error":
        return state

    try:
        record = ClaimRecord.from_dict(state["claim_record"])
        engine = RxHCCRuleEngine()
        results = engine.validate(record)
        
        for r in results:
            state["results"].append(r.to_dict())
            
        # CRITICAL 결과가 있으면 에스컬레이션 플래그
        critical_count = sum(1 for r in results if r.severity == Severity.CRITICAL)
        if critical_count > 0:
            state["should_escalate"] = True
            state["escalation_reason"] = f"{critical_count}개의 CRITICAL 위반 발견"
            
        state["stage"] = "rules_complete"
        
    except Exception as e:
        logger.error("Rule engine error: %s", e)
        state["results"].append({
            "rule_id": "ENGINE-ERR",
            "rule_name": "Rule Engine Error",
            "severity": "CRITICAL",
            "message": f"규칙 엔진 오류: {str(e)}"
        })
        state["should_escalate"] = True
    
    return state

def risk_scoring(state: ValidationState) -> ValidationState:
    """3단계: 리스크 스코어링"""
    logger.info("Stage 3: Risk scoring")
    if state["stage"] == "parse_error":
        return state

    severity_scores = {
        "CRITICAL": 10,
        "WARNING": 5,
        "INFO": 1,
        "PASS": 0
    }
    
    total_score = sum(
        severity_scores.get(r.get("severity", "INFO"), 0)
        for r in state["results"]
    )
    
    # 리스크 등급 계산
    if total_score >= 20:
        risk_level = "HIGH"
    elif total_score >= 10:
        risk_level = "MEDIUM"
    elif total_score >= 5:
        risk_level = "LOW"
    else:
        risk_level = "MINIMAL"
        
    if "metadata" not in state:
        state["metadata"] = {}
        
    state["metadata"]["risk_score"] = total_score
    state["metadata"]["risk_level"] = risk_level
    state["stage"] = "scoring_complete"
    
    state["results"].append({
        "rule_id": "RISK-SCORE",
        "rule_name": "Risk Assessment",
        "severity": "INFO",
        "message": f"종합 리스크 스코어: {total_score} ({risk_level})"
    })
    
    return state

def escalation_check(state: ValidationState) -> ValidationState:
    """4단계: 에스컬레이션 결정"""
    logger.info("Stage 4: Escalation check")
    
    if state["should_escalate"]:
        state["results"].append({
            "rule_id": "ESCALATE",
            "rule_name": "Escalation Required",
            "severity": "CRITICAL",
            "message": f"⚠️ 수동 검토 필요: {state['escalation_reason']}"
        })
        state["stage"] = "escalated"
    else:
        state["results"].append({
            "rule_id": "AUTO-APPROVE",
            "rule_name": "Auto-Approved",
            "severity": "PASS",
            "message": "✅ 자동 승인: 모든 검증 통과"
        })
        state["stage"] = "approved"
        
    return state

# ============================================================
# 라우터 함수
# ============================================================
def should_continue(state: ValidationState) -> str:
    """parse 후 에러면 escalation으로 바로 이동"""
    if state["stage"] == "parse_error":
        return "escalation"
    return "rules"

# ============================================================
# 그래프 빌더
# ============================================================
def build_validation_graph():
    """LangGraph StateGraph 생성"""
    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph not available, returning sequential executor")
        return None
        
    workflow = StateGraph(ValidationState)
    
    # 노드 추가
    workflow.add_node("parse", parse_claim)
    workflow.add_node("rules", run_rule_engine)
    workflow.add_node("scoring", risk_scoring)
    workflow.add_node("escalation", escalation_check)
    
    # 엣지 정의
    workflow.set_entry_point("parse")
    
    workflow.add_conditional_edges(
        "parse",
        should_continue,
        {
            "rules": "rules",
            "escalation": "escalation"
        }
    )
    
    workflow.add_edge("rules", "scoring")
    workflow.add_edge("scoring", "escalation")
    workflow.add_edge("escalation", END)
    
    return workflow.compile()

# ============================================================
# Fallback: LangGraph 없이도 실행 가능
# ============================================================
def run_validation_sequential(claim_data: Dict) -> ValidationState:
    """LangGraph 없이 순차 실행 (fallback)"""
    state: ValidationState = {
        "claim": claim_data,
        "claim_record": {},
        "results": [],
        "stage": "init",
        "should_escalate": False,
        "escalation_reason": "",
        "metadata": {}
    }
    
    state = parse_claim(state)
    state = run_rule_engine(state)
    state = risk_scoring(state)
    state = escalation_check(state)
    
    return state

def run_validation(claim_data: Dict) -> ValidationState:
    """메인 실행 함수. LangGraph 사용 가능하면 그래프, 아니면 순차 실행."""
    if LANGGRAPH_AVAILABLE:
        try:
            graph = build_validation_graph()
            initial_state: ValidationState = {
                "claim": claim_data,
                "claim_record": {},
                "results": [],
                "stage": "init",
                "should_escalate": False,
                "escalation_reason": "",
                "metadata": {}
            }
            result = graph.invoke(initial_state)
            return result
        except Exception as e:
            logger.error("LangGraph execution failed, falling back: %s", e)
            return run_validation_sequential(claim_data)
    else:
        return run_validation_sequential(claim_data)
