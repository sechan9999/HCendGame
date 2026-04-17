"""
RxHCC Rule Engine Unit Tests
"""
import pytest
import sys
import os

# 프로젝트 루트 경로 추가 (상위 디렉토리)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.rules import (
    RxHCCRuleEngine,
    ClaimRecord, 
    ValidationResult,
    Severity
)
from engine.langgraph_integrity import run_validation, run_validation_sequential

class TestClaimRecord:
    """ClaimRecord 파싱 테스트"""
    def test_from_dict_basic(self):
        data = {
            "claim_id": "CLM-001",
            "patient_id": "PAT-001",
            "icd_codes": "E11.9",
            "ndc_codes": "00002-1433-80"
        }
        record = ClaimRecord.from_dict(data)
        assert record.claim_id == "CLM-001"
        assert record.icd_codes == ["E11.9"]
        assert record.ndc_codes == ["00002-1433-80"]

    def test_from_dict_multiple_codes(self):
        data = {
            "claim_id": "CLM-002",
            "patient_id": "PAT-002",
            "icd_codes": "E10.9,E11.65",
            "ndc_codes": "00088-2500-33,00002-1433-80"
        }
        record = ClaimRecord.from_dict(data)
        assert len(record.icd_codes) == 2
        assert len(record.ndc_codes) == 2

    def test_from_dict_list_input(self):
        data = {
            "claim_id": "CLM-003",
            "patient_id": "PAT-003",
            "icd_codes": ["E11.9", "I10"],
            "ndc_codes": ["00002-1433-80"]
        }
        record = ClaimRecord.from_dict(data)
        assert record.icd_codes == ["E11.9", "I10"]

class TestRuleEngine:
    """규칙 엔진 테스트"""
    def setup_method(self):
        self.engine = RxHCCRuleEngine()

    def test_normal_t2_diabetes(self):
        """정상: 제2형 당뇨 + Metformin"""
        record = ClaimRecord(
            claim_id="TEST-001",
            patient_id="PAT-001",
            icd_codes=["E11.9"],
            ndc_codes=["00002-1433-80"],
        )
        results = self.engine.validate(record)
        severities = [r.severity for r in results]
        assert Severity.CRITICAL not in severities

    def test_icd_conflict_t1_t2(self):
        """충돌: E10 + E11"""
        record = ClaimRecord(
            claim_id="TEST-002",
            patient_id="PAT-002",
            icd_codes=["E10.9", "E11.65"],
            ndc_codes=["00088-2500-33"],
        )
        results = self.engine.validate(record)
        critical_results = [r for r in results if r.severity == Severity.CRITICAL]
        assert len(critical_results) > 0
        assert any("CONFLICT" in r.rule_id for r in critical_results)

    def test_glp1_no_indication(self):
        """GLP-1 오남용: 적응증 없음"""
        record = ClaimRecord(
            claim_id="TEST-003",
            patient_id="PAT-003",
            icd_codes=["I10"], # 고혈압만
            ndc_codes=["00169-4060-12"], # Ozempic
        )
        results = self.engine.validate(record)
        critical_results = [r for r in results if r.severity == Severity.CRITICAL]
        assert len(critical_results) > 0
        assert any("GLP1" in r.rule_id for r in critical_results)

    def test_glp1_with_t2_diabetes(self):
        """정상: E11 + GLP-1"""
        record = ClaimRecord(
            claim_id="TEST-004",
            patient_id="PAT-004",
            icd_codes=["E11.9"],
            ndc_codes=["00169-4060-12"], # Ozempic
        )
        results = self.engine.validate(record)
        # GLP-1 관련 CRITICAL이 없어야 함
        glp1_critical = [r for r in results if r.severity == Severity.CRITICAL and "GLP1" in r.rule_id]
        assert len(glp1_critical) == 0

    def test_glp1_with_obesity(self):
        """정상: E66 + GLP-1 (Wegovy)"""
        record = ClaimRecord(
            claim_id="TEST-005",
            patient_id="PAT-005",
            icd_codes=["E66.01"],
            ndc_codes=["00169-4060-13"],
        )
        results = self.engine.validate(record)
        glp1_critical = [r for r in results if r.severity == Severity.CRITICAL and "GLP1" in r.rule_id]
        assert len(glp1_critical) == 0

    def test_glp1_for_type1(self):
        """위반: E10 + GLP-1"""
        record = ClaimRecord(
            claim_id="TEST-006",
            patient_id="PAT-006",
            icd_codes=["E10.9"],
            ndc_codes=["00169-4060-12"],
        )
        results = self.engine.validate(record)
        critical_results = [r for r in results if r.severity == Severity.CRITICAL]
        assert len(critical_results) > 0

    def test_hcc_upcoding(self):
        """HCC Upcoding: E11.9에 HCC18"""
        record = ClaimRecord(
            claim_id="TEST-007",
            patient_id="PAT-007",
            icd_codes=["E11.9"],
            ndc_codes=["00002-1433-80"],
            hcc_codes=["HCC18"],
        )
        results = self.engine.validate(record)
        upcode_results = [r for r in results if "UPCODE" in r.rule_id]
        assert len(upcode_results) > 0

    def test_hcc_correct_mapping(self):
        """정상 HCC: E11.65에 HCC18"""
        record = ClaimRecord(
            claim_id="TEST-008",
            patient_id="PAT-008",
            icd_codes=["E11.65"],
            ndc_codes=["00002-1433-80"],
            hcc_codes=["HCC18"],
        )
        results = self.engine.validate(record)
        upcode_results = [r for r in results if "UPCODE" in r.rule_id]
        assert len(upcode_results) == 0

    def test_custom_rule(self):
        """커스텀 규칙 추가"""
        def high_amount_check(claim: ClaimRecord):
            if claim.claim_amount > 10000:
                return ValidationResult(
                    rule_id="CUSTOM-001",
                    rule_name="High Amount Check",
                    severity=Severity.WARNING,
                    message=f"청구 금액 ${claim.claim_amount}이 $10,000 초과"
                )
            return None
        
        self.engine.add_custom_rule(high_amount_check)
        record = ClaimRecord(
            claim_id="TEST-009",
            patient_id="PAT-009",
            icd_codes=["E11.9"],
            ndc_codes=["00002-1433-80"],
            claim_amount=25000.0
        )
        results = self.engine.validate(record)
        custom_results = [r for r in results if r.rule_id == "CUSTOM-001"]
        assert len(custom_results) == 1

class TestLangGraphWorkflow:
    """LangGraph 워크플로우 테스트"""
    def test_sequential_normal(self):
        claim = {
            "claim_id": "WF-001",
            "patient_id": "PAT-001",
            "icd_codes": "E11.9",
            "ndc_codes": "00002-1433-80",
            "hcc_codes": ""
        }
        state = run_validation_sequential(claim)
        
        # 순차 실행에서는 stage가 마지막인 approved 또는 escalated
        assert state["stage"] in ("approved", "escalated")
        assert len(state["results"]) > 0

    def test_sequential_critical(self):
        claim = {
            "claim_id": "WF-002",
            "patient_id": "PAT-002",
            "icd_codes": "E10.9,E11.65",
            "ndc_codes": "00088-2500-33",
            "hcc_codes": ""
        }
        state = run_validation_sequential(claim)
        assert state["should_escalate"] == True
        assert state["stage"] == "escalated"

    def test_run_validation(self):
        """run_validation은 LangGraph 유무와 관계없이 동작해야 함"""
        claim = {
            "claim_id": "WF-003",
            "patient_id": "PAT-003",
            "icd_codes": "I10",
            "ndc_codes": "00169-4060-12",
            "hcc_codes": ""
        }
        state = run_validation(claim)
        assert "results" in state
        assert "metadata" in state

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
