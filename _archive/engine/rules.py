"""
RxHCC Validation Rules Engine
=============================
모든 검증 규칙을 중앙 집중 관리.
새 규칙 추가 시 이 파일만 수정하면 됨.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Callable
import json
import logging

logger = logging.getLogger(__name__)

class Severity(Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    INFO = "INFO"

@dataclass
class ValidationResult:
    rule_id: str
    rule_name: str
    severity: Severity
    message: str
    details: Dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details
        }

@dataclass
class ClaimRecord:
    """표준화된 청구 레코드"""
    claim_id: str
    patient_id: str
    icd_codes: List[str]
    ndc_codes: List[str]
    hcc_codes: List[str] = field(default_factory=list)
    provider_id: str = ""
    claim_date: str = ""
    claim_amount: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> 'ClaimRecord':
        """딕셔너리에서 ClaimRecord 생성 (유연한 키 매핑)"""
        # 다양한 키 이름 지원
        icd_raw = data.get('icd_codes') or data.get('icd_code') or data.get('diagnosis_code', '')
        ndc_raw = data.get('ndc_codes') or data.get('ndc_code') or data.get('drug_code', '')
        hcc_raw = data.get('hcc_codes') or data.get('hcc_code', '')

        def to_list(val):
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                return [v.strip() for v in val.split(',') if v.strip()]
            return []

        return cls(
            claim_id=str(data.get('claim_id', 'UNKNOWN')),
            patient_id=str(data.get('patient_id', 'UNKNOWN')),
            icd_codes=to_list(icd_raw),
            ndc_codes=to_list(ndc_raw),
            hcc_codes=to_list(hcc_raw),
            provider_id=str(data.get('provider_id', '')),
            claim_date=str(data.get('claim_date', '')),
            claim_amount=float(data.get('claim_amount', 0.0))
        )

# ============================================================
# ICD-NDC 매핑 테이블 (확장 가능)
# ============================================================
ICD_NDC_VALID_MAPPINGS = {
    # 제2형 당뇨 (E11.x) → 허용 약물
    "E11": {
        "valid_ndc_prefixes": [
            "00002-1433", # Metformin (Glucophage)
            "00002-1434", # Metformin ER
            "00169-4060", # Ozempic (Semaglutide) - GLP-1
            "00169-4130", # Victoza (Liraglutide) - GLP-1
            "00002-7515", # Trulicity (Dulaglutide) - GLP-1
            "00088-2220", # Jardiance (Empagliflozin) - SGLT2
            "00078-0431", # Invokana (Canagliflozin) - SGLT2
            "55111-0396", # Glipizide (Sulfonylurea)
        ],
        "description": "Type 2 Diabetes Mellitus"
    },
    # 제1형 당뇨 (E10.x) → 허용 약물 (인슐린 위주)
    "E10": {
        "valid_ndc_prefixes": [
            "00088-2500", # Lantus (Insulin Glargine)
            "00169-7501", # NovoLog (Insulin Aspart)
            "00002-7714", # Humalog (Insulin Lispro)
            "00169-3919", # Levemir (Insulin Detemir)
            "00169-4130", # Tresiba (Insulin Degludec)
        ],
        "description": "Type 1 Diabetes Mellitus"
    },
    # 고혈압 (I10) → 허용 약물
    "I10": {
        "valid_ndc_prefixes": [
            "00071-0155", # Norvasc (Amlodipine)
            "00781-1506", # Lisinopril
            "00378-4145", # Losartan
            "00591-0405", # Hydrochlorothiazide
            "68180-0519", # Metoprolol
        ],
        "description": "Essential Hypertension"
    },
    # 비만 (E66.x) → 허용 약물
    "E66": {
        "valid_ndc_prefixes": [
            "00169-4060", # Wegovy (Semaglutide - weight mgmt)
            "76431-0220", # Contrave
            "65757-0300", # Qsymia
            "00032-5200", # Xenical (Orlistat)
        ],
        "description": "Obesity"
    },
    # COPD (J44.x) → 허용 약물
    "J44": {
        "valid_ndc_prefixes": [
            "00173-0717", # Advair (Fluticasone/Salmeterol)
            "00597-0075", # Spiriva (Tiotropium)
            "00078-0610", # Breo Ellipta
            "00310-0200", # Symbicort
        ],
        "description": "Chronic Obstructive Pulmonary Disease"
    },
}

# ============================================================
# ICD 충돌 규칙 (상호 배타적 진단)
# ============================================================
ICD_CONFLICT_RULES = [
    {
        "rule_id": "CONFLICT-001",
        "name": "Type 1/Type 2 Diabetes Conflict",
        "codes_a": ["E10"],
        "codes_b": ["E11"],
        "severity": Severity.CRITICAL,
        "message": "제1형 당뇨(E10)와 제2형 당뇨(E11)가 동시에 진단됨. 상호 배타적 진단입니다."
    },
    {
        "rule_id": "CONFLICT-002",
        "name": "Diabetes Remission Conflict",
        "codes_a": ["E11"],
        "codes_b": ["Z86.39"], # Personal history of diabetes
        "severity": Severity.WARNING,
        "message": "현재 당뇨 진단(E11)과 당뇨 과거력(Z86.39)이 동시 존재. 코딩 검토 필요."
    },
    {
        "rule_id": "CONFLICT-003",
        "name": "Asthma/COPD Overlap Check",
        "codes_a": ["J45"], # Asthma
        "codes_b": ["J44"], # COPD
        "severity": Severity.WARNING,
        "message": "천식(J45)과 COPD(J44) 동시 진단. ACO(Asthma-COPD Overlap) 확인 필요."
    },
]

# ============================================================
# GLP-1 특별 규칙
# ============================================================
GLP1_NDC_PREFIXES = [
    "00169-4060", # Semaglutide (Ozempic/Wegovy)
    "00169-4130", # Liraglutide (Victoza/Saxenda)
    "00002-7515", # Dulaglutide (Trulicity)
]
GLP1_VALID_ICD_PREFIXES = ["E11", "E66"] # 제2형 당뇨 or 비만만 허용

# ============================================================
# HCC Upcoding 감지 규칙
# ============================================================
HCC_HIGH_RISK_MAPPINGS = {
    "HCC18": {
        "expected_icds": ["E11.65", "E11.69", "E13.65"],
        "description": "Diabetes with Chronic Complications",
        "risk_score_impact": 0.302
    },
    "HCC19": {
        "expected_icds": ["E11.9", "E11.8"],
        "description": "Diabetes without Complication",
        "risk_score_impact": 0.104
    },
    "HCC85": {
        "expected_icds": ["I50.20", "I50.22", "I50.32"],
        "description": "Congestive Heart Failure",
        "risk_score_impact": 0.331
    },
}

# ============================================================
# 메인 규칙 엔진 클래스
# ============================================================
class RxHCCRuleEngine:
    """ 중앙 규칙 엔진. 모든 검증 로직을 실행하고 결과를 반환. """
    def __init__(self, custom_mappings: Dict = None, custom_conflicts: List = None):
        self.icd_ndc_mappings = custom_mappings or ICD_NDC_VALID_MAPPINGS
        self.conflict_rules = custom_conflicts or ICD_CONFLICT_RULES
        self._custom_rules: List[Callable] = []
        logger.info("RxHCC Rule Engine initialized with %d ICD mappings, %d conflict rules", len(self.icd_ndc_mappings), len(self.conflict_rules))

    def add_custom_rule(self, rule_fn: Callable):
        """커스텀 규칙 함수 등록. rule_fn(claim: ClaimRecord) -> Optional[ValidationResult]"""
        self._custom_rules.append(rule_fn)

    def validate(self, claim: ClaimRecord) -> List[ValidationResult]:
        """모든 규칙을 실행하여 검증 결과 리스트 반환"""
        results = []
        
        # 1) ICD-NDC 매핑 검증
        results.extend(self._check_icd_ndc_mapping(claim))
        
        # 2) ICD 충돌 검증
        results.extend(self._check_icd_conflicts(claim))
        
        # 3) GLP-1 특별 검증
        results.extend(self._check_glp1_rules(claim))
        
        # 4) HCC Upcoding 검증
        results.extend(self._check_hcc_upcoding(claim))
        
        # 5) 커스텀 규칙 실행
        for rule_fn in self._custom_rules:
            try:
                result = rule_fn(claim)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error("Custom rule error: %s", e)

        # 결과 없으면 PASS
        if not results:
            results.append(ValidationResult(
                rule_id="PASS-000",
                rule_name="All Checks Passed",
                severity=Severity.PASS,
                message=f"Claim {claim.claim_id}: 모든 검증을 통과했습니다.",
                details={"claim_id": claim.claim_id}
            ))

        return results

    def validate_batch(self, claims: List[ClaimRecord]) -> Dict[str, List[ValidationResult]]:
        """배치 검증"""
        return {claim.claim_id: self.validate(claim) for claim in claims}

    # --- 내부 검증 메서드 ---
    def _check_icd_ndc_mapping(self, claim: ClaimRecord) -> List[ValidationResult]:
        results = []
        for icd in claim.icd_codes:
            icd_prefix = self._get_icd_prefix(icd)
            if icd_prefix not in self.icd_ndc_mappings:
                continue # 매핑 테이블에 없는 ICD는 스킵
            
            valid_ndcs = self.icd_ndc_mappings[icd_prefix]["valid_ndc_prefixes"]
            desc = self.icd_ndc_mappings[icd_prefix]["description"]
            
            for ndc in claim.ndc_codes:
                ndc_clean = ndc.strip()
                is_valid = any(ndc_clean.startswith(v) for v in valid_ndcs)
                if not is_valid:
                    results.append(ValidationResult(
                        rule_id="NDC-MISMATCH-001",
                        rule_name="ICD-NDC Mapping Mismatch",
                        severity=Severity.WARNING,
                        message=f"진단 {icd} ({desc})에 대해 약물 {ndc}이(가) 허용 목록에 없습니다.",
                        details={
                            "icd_code": icd,
                            "ndc_code": ndc,
                            "expected_ndc_prefixes": valid_ndcs,
                            "diagnosis_description": desc
                        }
                    ))
        return results

    def _check_icd_conflicts(self, claim: ClaimRecord) -> List[ValidationResult]:
        results = []
        for rule in self.conflict_rules:
            has_a = any(
                any(icd.startswith(code) for code in rule["codes_a"]) 
                for icd in claim.icd_codes
            )
            has_b = any(
                any(icd.startswith(code) for code in rule["codes_b"])
                for icd in claim.icd_codes
            )
            
            if has_a and has_b:
                results.append(ValidationResult(
                    rule_id=rule["rule_id"],
                    rule_name=rule["name"],
                    severity=rule["severity"],
                    message=rule["message"],
                    details={
                        "icd_codes": claim.icd_codes,
                        "conflicting_groups": [rule["codes_a"], rule["codes_b"]]
                    }
                ))
        return results

    def _check_glp1_rules(self, claim: ClaimRecord) -> List[ValidationResult]:
        results = []
        has_glp1 = any(
            any(ndc.startswith(prefix) for prefix in GLP1_NDC_PREFIXES)
            for ndc in claim.ndc_codes
        )
        
        if not has_glp1:
            return results

        has_valid_diagnosis = any(
            any(icd.startswith(prefix) for prefix in GLP1_VALID_ICD_PREFIXES)
            for icd in claim.icd_codes
        )
        
        if not has_valid_diagnosis:
            results.append(ValidationResult(
                rule_id="GLP1-001",
                rule_name="GLP-1 Off-Label Use Detection",
                severity=Severity.CRITICAL,
                message="GLP-1 약물이 처방되었으나 적응증(E11: 제2형 당뇨, E66: 비만)이 없습니다. 오남용 가능성.",
                details={
                    "ndc_codes": claim.ndc_codes,
                    "icd_codes": claim.icd_codes,
                    "required_icd_prefixes": GLP1_VALID_ICD_PREFIXES
                }
            ))

        # E10(1형 당뇨)에 GLP-1 처방 체크
        has_type1 = any(icd.startswith("E10") for icd in claim.icd_codes)
        if has_type1:
            results.append(ValidationResult(
                rule_id="GLP1-002",
                rule_name="GLP-1 for Type 1 Diabetes",
                severity=Severity.CRITICAL,
                message="제1형 당뇨(E10) 환자에게 GLP-1이 처방됨. GLP-1은 제1형 당뇨 적응증이 아닙니다.",
                details={
                    "ndc_codes": claim.ndc_codes,
                    "icd_codes": claim.icd_codes
                }
            ))
        
        return results

    def _check_hcc_upcoding(self, claim: ClaimRecord) -> List[ValidationResult]:
        results = []
        for hcc in claim.hcc_codes:
            hcc_upper = hcc.upper()
            if hcc_upper in HCC_HIGH_RISK_MAPPINGS:
                mapping = HCC_HIGH_RISK_MAPPINGS[hcc_upper]
                has_supporting_icd = any(
                    icd in mapping["expected_icds"] for icd in claim.icd_codes
                )
                
                if not has_supporting_icd:
                    results.append(ValidationResult(
                        rule_id="HCC-UPCODE-001",
                        rule_name="Potential HCC Upcoding",
                        severity=Severity.CRITICAL,
                        message=f"HCC {hcc_upper} ({mapping['description']}) 매핑되었으나 "
                                f"뒷받침하는 ICD 코드가 부족합니다. Risk Score 영향: {mapping['risk_score_impact']}",
                        details={
                            "hcc_code": hcc_upper,
                            "expected_icds": mapping["expected_icds"],
                            "actual_icds": claim.icd_codes,
                            "risk_score_impact": mapping["risk_score_impact"]
                        }
                    ))
        return results

    @staticmethod
    def _get_icd_prefix(icd_code: str) -> str:
        """ICD 코드에서 카테고리 prefix 추출 (예: E11.65 -> E11)"""
        code = icd_code.strip().upper()
        if '.' in code:
            return code.split('.')[0]
        # 3자리까지만
        return code[:3] if len(code) >= 3 else code
