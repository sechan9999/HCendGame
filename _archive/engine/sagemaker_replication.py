"""
SageMaker Replication with Pandas Fallback
===========================================
SageMaker Processing Job을 시뮬레이션하면서 Pandas로 대용량 데이터 생성 및 검증 수행.
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
import json
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# SageMaker SDK (옵션)
try:
    import sagemaker
    from sagemaker.processing import ScriptProcessor
    SAGEMAKER_AVAILABLE = True
except ImportError:
    SAGEMAKER_AVAILABLE = False
    logger.info("SageMaker SDK not installed. Using Pandas-only mode.")

# ============================================================
# 합성 데이터 생성기
# ============================================================
class SyntheticClaimGenerator:
    """
    현실적인 보험 청구 합성 데이터 생성.
    다양한 시나리오(정상, 충돌, 오남용 등)를 포함.
    """
    # ICD 코드 풀
    ICD_POOLS = {
        "diabetes_t2": ["E11.9", "E11.65", "E11.21", "E11.22", "E11.40"],
        "diabetes_t1": ["E10.9", "E10.65", "E10.10"],
        "hypertension": ["I10", "I11.9", "I12.9"],
        "obesity": ["E66.01", "E66.09", "E66.3"],
        "copd": ["J44.0", "J44.1", "J44.9"],
        "heart_failure": ["I50.20", "I50.22", "I50.9"],
        "asthma": ["J45.20", "J45.30", "J45.50"],
    }
    
    # NDC 코드 풀
    NDC_POOLS = {
        "metformin": ["00002-1433-80", "00002-1434-80"],
        "glp1": ["00169-4060-12", "00169-4130-12", "00002-7515-01"],
        "insulin": ["00088-2500-33", "00169-7501-11", "00002-7714-01"],
        "antihypertensive": ["00071-0155-23", "00781-1506-01", "00378-4145-01"],
        "weight_loss": ["00169-4060-13", "76431-0220-01"], # Wegovy
        "copd_inhalers": ["00173-0717-20", "00597-0075-75"],
    }
    
    # HCC 코드 풀
    HCC_POOLS = {
        "diabetes_complications": ["HCC18", "HCC19"],
        "heart": ["HCC85", "HCC86"],
        "respiratory": ["HCC111", "HCC112"],
    }

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)
        
    def generate(self, n_records: int = 1000, anomaly_rate: float = 0.15) -> pd.DataFrame:
        """
        합성 청구 데이터 생성
        Args:
            n_records: 생성할 레코드 수
            anomaly_rate: 이상 레코드 비율 (0~1)
        """
        records = []
        n_anomalies = int(n_records * anomaly_rate)
        n_normal = n_records - n_anomalies
        
        # 정상 레코드 생성
        for i in range(n_normal):
            records.append(self._generate_normal_record(f"CLM-{i:06d}"))
            
        # 이상 레코드 생성 (다양한 유형)
        anomaly_types = ["icd_conflict", "glp1_misuse", "hcc_upcoding", "ndc_mismatch", "duplicate_claim"]
        for i in range(n_anomalies):
            atype = self.rng.choice(anomaly_types)
            claim_id = f"CLM-A{i:05d}"
            
            if atype == "icd_conflict":
                records.append(self._generate_icd_conflict(claim_id))
            elif atype == "glp1_misuse":
                records.append(self._generate_glp1_misuse(claim_id))
            elif atype == "hcc_upcoding":
                records.append(self._generate_hcc_upcoding(claim_id))
            elif atype == "ndc_mismatch":
                records.append(self._generate_ndc_mismatch(claim_id))
            elif atype == "duplicate_claim":
                records.append(self._generate_duplicate_flag(claim_id))
                
        df = pd.DataFrame(records)
        # 셔플
        df = df.sample(frac=1, random_state=self.rng).reset_index(drop=True)
        
        logger.info("Generated %d records (%d normal, %d anomalies)", len(df), n_normal, n_anomalies)
        return df

    def _generate_normal_record(self, claim_id: str) -> Dict:
        """정상적인 청구 레코드"""
        scenario = self.rng.choice(["diabetes_t2", "hypertension", "copd"])
        
        if scenario == "diabetes_t2":
            icd = self.rng.choice(self.ICD_POOLS["diabetes_t2"])
            ndc = self.rng.choice(self.NDC_POOLS["metformin"])
            hcc = self.rng.choice(self.HCC_POOLS["diabetes_complications"])
        elif scenario == "hypertension":
            icd = self.rng.choice(self.ICD_POOLS["hypertension"])
            ndc = self.rng.choice(self.NDC_POOLS["antihypertensive"])
            hcc = ""
        else: # copd
            icd = self.rng.choice(self.ICD_POOLS["copd"])
            ndc = self.rng.choice(self.NDC_POOLS["copd_inhalers"])
            hcc = self.rng.choice(self.HCC_POOLS["respiratory"])
            
        return {
            "claim_id": claim_id,
            "patient_id": f"PAT-{self.rng.randint(10000, 99999)}",
            "icd_codes": icd,
            "ndc_codes": ndc,
            "hcc_codes": hcc,
            "provider_id": f"PRV-{self.rng.randint(1000, 9999)}",
            "claim_date": self._random_date(),
            "claim_amount": round(self.rng.uniform(50, 5000), 2),
            "anomaly_type": "NORMAL",
            "expected_result": "PASS"
        }

    def _generate_icd_conflict(self, claim_id: str) -> Dict:
        """ICD 충돌: E10 + E11 동시"""
        return {
            "claim_id": claim_id,
            "patient_id": f"PAT-{self.rng.randint(10000, 99999)}",
            "icd_codes": f"{self.rng.choice(self.ICD_POOLS['diabetes_t1'])},"
                         f"{self.rng.choice(self.ICD_POOLS['diabetes_t2'])}",
            "ndc_codes": self.rng.choice(self.NDC_POOLS["insulin"]),
            "hcc_codes": "HCC18,HCC19",
            "provider_id": f"PRV-{self.rng.randint(1000, 9999)}",
            "claim_date": self._random_date(),
            "claim_amount": round(self.rng.uniform(500, 15000), 2),
            "anomaly_type": "ICD_CONFLICT",
            "expected_result": "CRITICAL"
        }

    def _generate_glp1_misuse(self, claim_id: str) -> Dict:
        """GLP-1 오남용: 적응증 없이 GLP-1 처방"""
        # 고혈압 환자에게 GLP-1 (적응증 없음)
        return {
            "claim_id": claim_id,
            "patient_id": f"PAT-{self.rng.randint(10000, 99999)}",
            "icd_codes": self.rng.choice(self.ICD_POOLS["hypertension"]),
            "ndc_codes": self.rng.choice(self.NDC_POOLS["glp1"]),
            "hcc_codes": "",
            "provider_id": f"PRV-{self.rng.randint(1000, 9999)}",
            "claim_date": self._random_date(),
            "claim_amount": round(self.rng.uniform(800, 3000), 2),
            "anomaly_type": "GLP1_MISUSE",
            "expected_result": "CRITICAL"
        }

    def _generate_hcc_upcoding(self, claim_id: str) -> Dict:
        """HCC Upcoding: 높은 HCC 코드에 낮은 ICD"""
        return {
            "claim_id": claim_id,
            "patient_id": f"PAT-{self.rng.randint(10000, 99999)}",
            "icd_codes": "E11.9", # 합병증 없는 당뇨
            "ndc_codes": self.rng.choice(self.NDC_POOLS["metformin"]),
            "hcc_codes": "HCC18", # 합병증 있는 당뇨 HCC (불일치!)
            "provider_id": f"PRV-{self.rng.randint(1000, 9999)}",
            "claim_date": self._random_date(),
            "claim_amount": round(self.rng.uniform(2000, 20000), 2),
            "anomaly_type": "HCC_UPCODING",
            "expected_result": "CRITICAL"
        }

    def _generate_ndc_mismatch(self, claim_id: str) -> Dict:
        """NDC 불일치: 고혈압 진단에 인슐린 처방"""
        return {
            "claim_id": claim_id,
            "patient_id": f"PAT-{self.rng.randint(10000, 99999)}",
            "icd_codes": self.rng.choice(self.ICD_POOLS["hypertension"]),
            "ndc_codes": self.rng.choice(self.NDC_POOLS["insulin"]),
            "hcc_codes": "",
            "provider_id": f"PRV-{self.rng.randint(1000, 9999)}",
            "claim_date": self._random_date(),
            "claim_amount": round(self.rng.uniform(200, 1500), 2),
            "anomaly_type": "NDC_MISMATCH",
            "expected_result": "WARNING"
        }

    def _generate_duplicate_flag(self, claim_id: str) -> Dict:
        """중복 의심 청구"""
        base = self._generate_normal_record(claim_id)
        base["anomaly_type"] = "DUPLICATE_SUSPECT"
        base["expected_result"] = "WARNING"
        base["claim_amount"] = round(base["claim_amount"] * 2, 2) # 비정상 금액
        return base

    def _random_date(self) -> str:
        start = datetime(2024, 1, 1)
        delta = timedelta(days=self.rng.randint(0, 365))
        return (start + delta).strftime("%Y-%m-%d")

# ============================================================
# Pandas 기반 배치 검증기
# ============================================================
class PandasBatchValidator:
    """
    Pandas DataFrame 기반 대용량 배치 검증.
    SageMaker Processing Job의 로컬 대체.
    """
    def __init__(self):
        from engine.rules import RxHCCRuleEngine
        self.engine = RxHCCRuleEngine()
        
    def validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrame의 각 행을 검증하고 결과 컬럼 추가.
        Returns: 원본 DataFrame에 validation_results, max_severity, is_flagged 컬럼 추가
        """
        from engine.rules import ClaimRecord
        
        results_list = []
        max_severity_list = []
        flagged_list = []
        
        severity_order = {"CRITICAL": 4, "WARNING": 3, "INFO": 2, "PASS": 1}
        
        for idx, row in df.iterrows():
            try:
                record = ClaimRecord.from_dict(row.to_dict())
                results = self.engine.validate(record)
                
                # 결과 직렬화
                results_json = json.dumps([r.to_dict() for r in results], ensure_ascii=False)
                
                # 최고 심각도
                max_sev = max(
                    (r.severity.value for r in results),
                    key=lambda s: severity_order.get(s, 0),
                    default="PASS"
                )
                
                is_flagged = max_sev in ("CRITICAL", "WARNING")
                
            except Exception as e:
                results_json = json.dumps([{
                    "rule_id": "ERROR", 
                    "severity": "CRITICAL", 
                    "message": str(e)
                }])
                max_sev = "CRITICAL"
                is_flagged = True
                
            results_list.append(results_json)
            max_severity_list.append(max_sev)
            flagged_list.append(is_flagged)
            
        df = df.copy()
        df["validation_results"] = results_list
        df["max_severity"] = max_severity_list
        df["is_flagged"] = flagged_list
        return df

    def get_summary(self, validated_df: pd.DataFrame) -> Dict:
        """검증 결과 요약 통계"""
        total = len(validated_df)
        flagged = validated_df["is_flagged"].sum()
        
        severity_counts = validated_df["max_severity"].value_counts().to_dict()
        
        anomaly_counts = {}
        if "anomaly_type" in validated_df.columns:
            anomaly_counts = validated_df["anomaly_type"].value_counts().to_dict()
            
        return {
            "total_claims": total,
            "flagged_claims": int(flagged),
            "pass_rate": round((total - flagged) / total * 100, 1) if total > 0 else 0,
            "severity_distribution": severity_counts,
            "anomaly_distribution": anomaly_counts,
            "total_amount_at_risk": round(
                validated_df[validated_df["is_flagged"]]["claim_amount"].sum(), 2
            ) if "claim_amount" in validated_df.columns else 0
        }

# ============================================================
# SageMaker 인터페이스 (옵션)
# ============================================================
class SageMakerProcessor:
    """SageMaker Processing Job 래퍼 (가용 시)"""
    def __init__(self, role: str = None, instance_type: str = "ml.m5.xlarge"):
        self.role = role or os.environ.get("SAGEMAKER_ROLE", "")
        self.instance_type = instance_type
        self._available = SAGEMAKER_AVAILABLE and bool(self.role)
        
    @property
    def is_available(self) -> bool:
        return self._available
        
    def run_processing_job(self, input_path: str, output_path: str) -> Dict:
        """SageMaker Processing Job 실행 (미구현 시 Pandas fallback)"""
        if not self._available:
            logger.info("SageMaker not available. Using Pandas fallback.")
            return self._pandas_fallback(input_path, output_path)
            
        # SageMaker 실행 로직 (필요 시 구현)
        try:
            # TODO: 실제 SageMaker Processing Job 구현
            raise NotImplementedError("SageMaker job not yet implemented")
        except Exception as e:
            logger.warning("SageMaker failed (%s), falling back to Pandas", e)
            return self._pandas_fallback(input_path, output_path)

    def _pandas_fallback(self, input_path: str, output_path: str) -> Dict:
        """Pandas 기반 로컬 처리"""
        df = pd.read_csv(input_path)
        validator = PandasBatchValidator()
        validated_df = validator.validate_dataframe(df)
        
        validated_df.to_csv(output_path, index=False)
        summary = validator.get_summary(validated_df)
        logger.info("Pandas fallback complete: %s", summary)
        return summary
