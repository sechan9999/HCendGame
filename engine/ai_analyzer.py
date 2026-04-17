"""
OpenAI-Powered FWA AI Analyzer
================================
기존 룰엔진 결과를 OpenAI GPT가 의학적 맥락에서 심층 분석.
Function Calling을 활용한 구조화된 판단.

Architecture:
  [Claim Data] → [Rule Engine] → [OpenAI Analysis] → [Structured Report]
"""
import os
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai package not installed. Run: pip install openai")


# ============================================================
# 1. AI 분석 결과 데이터 모델
# ============================================================
@dataclass
class AIAnalysisResult:
    """GPT가 반환하는 구조화된 분석 결과"""
    claim_id: str
    risk_level: str          # HIGH / MEDIUM / LOW / CLEAN
    confidence: float         # 0.0 ~ 1.0
    fraud_probability: float  # 0.0 ~ 1.0
    analysis_summary: str     # 한글 자연어 요약
    medical_reasoning: str    # 의학적 판단 근거
    recommended_action: str   # BLOCK / REVIEW / MONITOR / APPROVE
    anomaly_details: List[Dict] = field(default_factory=list)
    pattern_tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================
# 2. OpenAI Function Calling 스키마
# ============================================================
ANALYZE_CLAIM_FUNCTION = {
    "name": "submit_fwa_analysis",
    "description": "Submit structured FWA analysis result for a healthcare claim",
    "parameters": {
        "type": "object",
        "properties": {
            "risk_level": {
                "type": "string",
                "enum": ["HIGH", "MEDIUM", "LOW", "CLEAN"],
                "description": "Overall risk level"
            },
            "confidence": {
                "type": "number", "minimum": 0.0, "maximum": 1.0,
                "description": "Confidence in the analysis (0-1)"
            },
            "fraud_probability": {
                "type": "number", "minimum": 0.0, "maximum": 1.0,
                "description": "Estimated probability of fraud (0-1)"
            },
            "analysis_summary": {
                "type": "string",
                "description": "Korean language summary of findings"
            },
            "medical_reasoning": {
                "type": "string",
                "description": "Medical reasoning in Korean"
            },
            "recommended_action": {
                "type": "string",
                "enum": ["BLOCK", "REVIEW", "MONITOR", "APPROVE"],
                "description": "Recommended action"
            },
            "anomaly_details": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "severity": {"type": "string", "enum": ["CRITICAL", "WARNING", "INFO"]},
                        "description": {"type": "string"}
                    },
                    "required": ["type", "severity", "description"]
                }
            },
            "pattern_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags: upcoding, phantom_billing, unbundling, doctor_shopping, off_label, kickback"
            }
        },
        "required": ["risk_level", "confidence", "fraud_probability",
                      "analysis_summary", "medical_reasoning", "recommended_action"]
    }
}

PATTERN_DETECT_FUNCTION = {
    "name": "submit_pattern_analysis",
    "description": "Submit fraud pattern analysis across multiple claims",
    "parameters": {
        "type": "object",
        "properties": {
            "patterns_found": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "pattern_name": {"type": "string"},
                        "severity": {"type": "string", "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]},
                        "affected_claims": {"type": "array", "items": {"type": "string"}},
                        "description": {"type": "string"},
                        "evidence": {"type": "string"},
                        "estimated_impact_usd": {"type": "number"}
                    },
                    "required": ["pattern_name", "severity", "description", "evidence"]
                }
            },
            "overall_risk_assessment": {"type": "string"},
            "priority_actions": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["patterns_found", "overall_risk_assessment", "priority_actions"]
    }
}


# ============================================================
# 3. System Prompt
# ============================================================
SYSTEM_PROMPT = """You are an expert healthcare Fraud, Waste, and Abuse (FWA) analyst 
with deep knowledge of:
- ICD-10-CM diagnosis coding
- NDC (National Drug Code) pharmaceutical coding  
- HCC (Hierarchical Condition Category) risk adjustment
- Medicare/Medicaid billing regulations
- Common fraud schemes: upcoding, unbundling, phantom billing, doctor shopping, kickbacks

GUIDELINES:
1. Provide analysis_summary and medical_reasoning in Korean (한국어).
2. Use medical evidence and coding guidelines to support judgment.
3. Consider both false-positive and true-positive scenarios.
4. Flag complex patterns that simple rules might miss.
5. Be specific about which CMS guidelines or coding rules are relevant.

FRAUD PATTERN KNOWLEDGE:
- Upcoding: HCC18 without supporting complication ICD codes
- Unbundling: Separating bundled procedures to increase reimbursement
- Phantom Billing: Billing for services not rendered
- Doctor Shopping: Patient visiting multiple providers for same condition/drugs
- Off-Label Prescribing: Expensive drugs (GLP-1) without valid indication
- Kickback Schemes: Unusual referral patterns between specific providers
"""


# ============================================================
# 4. 메인 FWA AI Analyzer 클래스
# ============================================================
class FWAAIAnalyzer:
    """
    OpenAI GPT를 활용한 지능형 FWA 분석기.
    
    Usage:
        analyzer = FWAAIAnalyzer(api_key="sk-...")
        result = analyzer.analyze_claim(claim_data, rule_results)
        patterns = analyzer.detect_patterns(claims_summary, stats)
        answer = analyzer.investigate("이 프로바이더의 패턴을 분석해줘", context)
    """
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.client = OpenAI(api_key=self.api_key) if (OPENAI_AVAILABLE and self.api_key) else None
        logger.info(f"FWA AI Analyzer initialized (model={model}, api={'connected' if self.client else 'fallback'})")
    
    @property
    def is_connected(self) -> bool:
        return self.client is not None
    
    # ----------------------------------------------------------
    # 4-1. 단건 청구 AI 분석
    # ----------------------------------------------------------
    def analyze_claim(self, claim_data: Dict, rule_results: List[Dict], context: str = "") -> AIAnalysisResult:
        """단건 청구를 AI로 심층 분석"""
        if not self.client:
            return self._fallback_analysis(claim_data, rule_results)
        
        user_prompt = f"""Analyze this healthcare claim for FWA:

=== CLAIM DATA ===
- Claim ID: {claim_data.get('claim_id', 'N/A')}
- Patient ID: {claim_data.get('patient_id', 'N/A')}
- ICD Codes: {claim_data.get('icd_codes', 'N/A')}
- NDC Codes: {claim_data.get('ndc_codes', 'N/A')}
- HCC Codes: {claim_data.get('hcc_codes', 'N/A')}
- Provider ID: {claim_data.get('provider_id', 'N/A')}
- Claim Date: {claim_data.get('claim_date', 'N/A')}
- Claim Amount: ${claim_data.get('claim_amount', 0):,.2f}

=== RULE ENGINE RESULTS ===
{json.dumps(rule_results, ensure_ascii=False, indent=2)}

{f'=== CONTEXT ==={chr(10)}{context}' if context else ''}

Analyze: Are rule flags medically justified? Any additional concerns? Overall fraud risk?
Use submit_fwa_analysis function."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                tools=[{"type": "function", "function": ANALYZE_CLAIM_FUNCTION}],
                tool_choice={"type": "function", "function": {"name": "submit_fwa_analysis"}},
                temperature=0.1,
                max_tokens=2000
            )
            
            tool_call = response.choices[0].message.tool_calls[0]
            result_data = json.loads(tool_call.function.arguments)
            
            return AIAnalysisResult(
                claim_id=claim_data.get("claim_id", "UNKNOWN"),
                risk_level=result_data.get("risk_level", "MEDIUM"),
                confidence=result_data.get("confidence", 0.5),
                fraud_probability=result_data.get("fraud_probability", 0.5),
                analysis_summary=result_data.get("analysis_summary", ""),
                medical_reasoning=result_data.get("medical_reasoning", ""),
                recommended_action=result_data.get("recommended_action", "REVIEW"),
                anomaly_details=result_data.get("anomaly_details", []),
                pattern_tags=result_data.get("pattern_tags", [])
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._fallback_analysis(claim_data, rule_results)
    
    # ----------------------------------------------------------
    # 4-2. 배치 패턴 탐지
    # ----------------------------------------------------------
    def detect_patterns(self, claims_summary: List[Dict], flagged_stats: Dict) -> Dict:
        """다수 청구에서 복합 부정 패턴 AI 탐지"""
        if not self.client:
            return self._fallback_pattern_detection(claims_summary, flagged_stats)
        
        user_prompt = f"""Analyze flagged claims for complex fraud PATTERNS:

=== FLAGGED CLAIMS (samples) ===
{json.dumps(claims_summary[:30], ensure_ascii=False, indent=2)}

=== STATISTICS ===
{json.dumps(flagged_stats, ensure_ascii=False, indent=2)}

Look for: Provider-level patterns, patient doctor-shopping, temporal spikes, 
financial clustering, systematic upcoding/unbundling.
Use submit_pattern_analysis."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                tools=[{"type": "function", "function": PATTERN_DETECT_FUNCTION}],
                tool_choice={"type": "function", "function": {"name": "submit_pattern_analysis"}},
                temperature=0.2,
                max_tokens=3000
            )
            tool_call = response.choices[0].message.tool_calls[0]
            return json.loads(tool_call.function.arguments)
        except Exception as e:
            logger.error(f"Pattern detection error: {e}")
            return self._fallback_pattern_detection(claims_summary, flagged_stats)
    
    # ----------------------------------------------------------
    # 4-3. 대화형 조사 (Investigator Chat)
    # ----------------------------------------------------------
    def investigate(self, question: str, claims_context: str, chat_history: List[Dict] = None) -> str:
        """자연어 질문으로 청구 데이터 조사"""
        if not self.client:
            return "⚠️ OpenAI API key가 설정되지 않았습니다. Settings에서 API key를 입력하세요."
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + 
             "\n\nInvestigator mode. Answer in Korean. Cite claim IDs. Provide actionable insights."},
        ]
        if chat_history:
            messages.extend(chat_history[-10:])
        
        messages.append({"role": "user", "content": 
            f"=== 데이터 컨텍스트 ===\n{claims_context}\n\n=== 질문 ===\n{question}"})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages,
                temperature=0.3, max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ API 오류: {str(e)}"
    
    # ----------------------------------------------------------
    # Fallback 메서드
    # ----------------------------------------------------------
    def _fallback_analysis(self, claim: Dict, rules: List[Dict]) -> AIAnalysisResult:
        severities = [r.get("severity", "INFO") for r in rules]
        has_critical = "CRITICAL" in severities
        has_warning = "WARNING" in severities
        
        if has_critical:
            risk, action, prob = "HIGH", "REVIEW", 0.75
        elif has_warning:
            risk, action, prob = "MEDIUM", "MONITOR", 0.4
        else:
            risk, action, prob = "CLEAN", "APPROVE", 0.05
        
        msgs = [r.get("message", "") for r in rules if r.get("severity") in ("CRITICAL", "WARNING")]
        summary = " | ".join(msgs) if msgs else "룰엔진 검증 통과"
        
        return AIAnalysisResult(
            claim_id=claim.get("claim_id", "UNKNOWN"),
            risk_level=risk, confidence=0.6, fraud_probability=prob,
            analysis_summary=f"[룰 기반 분석] {summary}",
            medical_reasoning="OpenAI API 미연결 — 룰엔진 결과만 참조한 간이 분석입니다. API key를 설정하면 의학적 맥락 분석이 가능합니다.",
            recommended_action=action,
            anomaly_details=[
                {"type": r.get("rule_id", ""), "severity": r.get("severity", "INFO"),
                 "description": r.get("message", "")}
                for r in rules if r.get("severity") in ("CRITICAL", "WARNING")
            ],
            pattern_tags=[]
        )
    
    def _fallback_pattern_detection(self, claims: List[Dict], stats: Dict) -> Dict:
        return {
            "patterns_found": [],
            "overall_risk_assessment": "[룰 기반] OpenAI 미연결 — 고급 패턴 탐지 불가",
            "priority_actions": ["OpenAI API key 설정 후 재분석 권장"]
        }
