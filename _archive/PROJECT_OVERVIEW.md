# 🏥 RxHCC Integrity - AI 보험 청구 무결성 검증 시스템
# RxHCC Integrity - AI Insurance Claim Verification System

RxHCC Integrity는 **보험 청구 데이터(진단코드, 약물코드, 위험조정계수)의 정합성을 AI 기반 규칙 엔진으로 실시간 검증**하여 부정 청구(Fraud), 낭비(Waste), 남용(Abuse)을 조기에 탐지하는 지능형 시스템입니다.

**RxHCC Integrity** is an intelligent system that **verifies the integrity of insurance claim data (ICD, NDC, HCC codes) in real-time using an AI-based rule engine**, designed to detect Fraud, Waste, and Abuse (FWA) early in the process.

---

## 🇰🇷 주요 기능 (Introduction)
이 시스템은 의료 데이터의 복잡한 상호 연관성을 분석하여 다음과 같은 핵심 가치를 제공합니다:

1.  **🔍 실시간 정합성 검사 (Real-time Validation)**
    - 입력된 **진단코드(ICD)**, **약물코드(NDC)**, **위험조정계수(HCC)** 간의 논리적 모순을 즉시 탐지합니다.
    - 예: 고혈압 환자에게 인슐린 처방, 1형 당뇨와 2형 당뇨 동시 진단 등.

2.  **🚨 이상 징후 자동 탐지 (Automatic Anomaly Detection)**
    - **코드 충돌(ICD Conflict):** 의학적으로 양립 불가능한 진단 코드 감지.
    - **약물 오남용(Drug Misuse):** 적응증 없는 고가 약물(GLP-1 등) 처방 감지.
    - **업코딩(Upcoding):** 환자의 상태보다 과도하게 높은 위험 등급(HCC) 청구 감지.

3.  **📊 데이터 시각화 & 분석 (Analytics Dashboard)**
    - 검증 결과를 한눈에 볼 수 있는 대시보드를 제공합니다.
    - 심각도(Critical/Warning), 이상 유형, Provider별 위반 현황 등을 시각적으로 분석할 수 있습니다.

4.  **☁️ 클라우드 확장성 (Cloud Scalability)**
    - AWS S3, SageMaker 등과 연동되어 대용량 배치 데이터 처리도 가능하도록 설계되었습니다.

---

## 🇺🇸 Key Features (Introduction)
This system analyzes complex correlations within medical data to provide the following core values:

1.  **🔍 Real-time Validation**
    - Instantly detects logical contradictions between input **ICD (Diagnosis)**, **NDC (Drug)**, and **HCC (Risk Adjustment)** codes.
    - *Example: Prescribing insulin to a hypertension patient, or diagnosing Type 1 and Type 2 diabetes simultaneously.*

2.  **🚨 Automatic Anomaly Detection**
    - **ICD Conflict:** Detects medically incompatible diagnosis codes.
    - **Drug Misuse:** Identifies prescriptions of high-cost drugs (e.g., GLP-1) without proper indication.
    - **Upcoding:** Detects claims with HCC risk scores excessively higher than supported by the patient's condition.

3.  **📊 Analytics Dashboard**
    - Provides a comprehensive dashboard to visualize validation results.
    - You can analyze severity distribution (Critical/Warning), anomaly types, and violation status by provider.

4.  **☁️ Cloud Scalability**
    - Designed to scale with cloud services like AWS S3 and SageMaker, enabling processing of large-scale batch data.

---

## 🛠️ 기술 스택 (Tech Stack)
- **Frontend:** Streamlit (Python UI Framework)
- **Logic:** Python (Rule Engine, Pandas)
- **Workflow:** LangGraph (Stateful Agent Workflow)
- **Cloud:** AWS (S3, SageMaker Ready)
