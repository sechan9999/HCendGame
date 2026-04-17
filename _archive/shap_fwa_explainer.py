"""
FWA Detection System - SHAP 기반 설명 가능한 AI (Explainable AI)
SHAP-based Explainability for FWA Detection

의료 감사 및 법적 대응을 위한 FWA 탐지 근거 시각화
Visualizes FWA detection reasoning for medical audits and legal compliance
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import seaborn as sns
from typing import Dict, List, Optional, Tuple
import warnings
import logging
from datetime import datetime, timedelta
import json
import os

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── SHAP 스타일 색상 팔레트 ──────────────────────────────────────────
COLORS = {
    "primary": "#1B3A6B",
    "secondary": "#0D6E75",
    "accent": "#2E86AB",
    "positive": "#E07B39",   # FWA 기여 (빨간 계열)
    "negative": "#27AE60",   # 정상 기여 (파란 계열)
    "critical": "#C0392B",
    "warning": "#E67E22",
    "normal": "#27AE60",
    "light_bg": "#F8F9FA",
    "border": "#DEE2E6",
}

# ─── 1. SHAP 값 계산기 (SHAP Value Calculator) ───────────────────────

class FWASHAPExplainer:
    """
    FWA 탐지 결과에 대한 SHAP 기반 설명 생성기
    
    실제 환경: shap.DeepExplainer 또는 shap.GradientExplainer 사용
    데모 환경: 모의 SHAP 값으로 시각화 시연
    """

    def __init__(self, feature_names: Optional[List[str]] = None):
        self.feature_names = feature_names or [
            "청구 금액 (Claim Amount)",
            "HCC 위험 점수 (HCC Score)",
            "HCC 위험 등급 (HCC Tier)",
            "Provider 대비 금액 비율",
            "HCC 편차 (Upcoding 신호)",
            "Provider 월 청구 건수",
            "Provider 고유 환자 수",
            "NDC 약물 코드 존재",
            "GLP-1 약물 여부",
            "주말 청구 여부",
            "월별 청구 빈도",
            "ICD 코드 챕터",
            "청구 월",
        ]
        self.n_features = len(self.feature_names)

    def compute_shap_values(
        self,
        claim_data: Dict,
        fwa_probability: float = None
    ) -> Dict:
        """
        청구 데이터에 대한 SHAP 값 계산
        
        실제 배포 시 아래 코드로 교체:
        ```python
        import shap
        explainer = shap.DeepExplainer(model, background_data)
        shap_values = explainer.shap_values(X_tensor)
        ```
        """
        np.random.seed(hash(str(claim_data)) % 1000)

        # 기본 SHAP 값 (정규분포 기반 시뮬레이션)
        base_shap = np.random.randn(self.n_features) * 0.15

        # claim_data 기반 조정 (실제 데이터 반영)
        fwa_prob = fwa_probability or 0.5

        if claim_data.get("is_fwa") or fwa_prob > 0.7:
            # FWA 케이스: 주요 특징들이 양수 기여
            base_shap[0] += 0.35   # 고액 청구
            base_shap[1] += 0.28   # 높은 HCC
            base_shap[2] += 0.22   # 높은 위험 등급
            base_shap[3] += 0.30   # Provider 평균 초과
            base_shap[4] += 0.40   # HCC 편차 큼 (업코딩)
            base_shap[7] += 0.18   # NDC 존재
            base_shap[8] += 0.45   # GLP-1 약물 (핵심 신호)
            base_shap[9] += 0.15   # 주말 청구
        else:
            # 정상 케이스: 주요 특징들이 음수 기여
            base_shap[0] -= 0.20
            base_shap[1] -= 0.15
            base_shap[4] -= 0.25
            base_shap[8] -= 0.30

        return {
            "shap_values": base_shap,
            "base_value": 0.05,   # 평균 FWA 비율 (5%)
            "feature_names": self.feature_names,
            "fwa_probability": fwa_probability or (0.05 + sum(np.maximum(base_shap, 0))),
        }

    def compute_batch_shap(self, n_samples: int = 100) -> np.ndarray:
        """배치 SHAP 값 계산 (전체 데이터셋 특징 중요도)"""
        np.random.seed(42)
        shap_matrix = []

        for i in range(n_samples):
            is_fwa = i < int(n_samples * 0.15)  # 15% FWA 시뮬레이션
            base = np.random.randn(self.n_features) * 0.12

            if is_fwa:
                base[4] += np.random.uniform(0.3, 0.6)   # HCC 편차
                base[8] += np.random.uniform(0.3, 0.5)   # GLP-1
                base[3] += np.random.uniform(0.2, 0.4)   # 금액 비율
                base[0] += np.random.uniform(0.2, 0.4)   # 청구 금액
                base[1] += np.random.uniform(0.1, 0.3)   # HCC 점수
            shap_matrix.append(base)

        return np.array(shap_matrix)


# ─── 2. SHAP 시각화 클래스 ─────────────────────────────────────────────

class FWASHAPVisualizer:
    """
    FWA 탐지 결과의 종합 SHAP 시각화
    의료 감사원이 이해할 수 있는 인사이트 제공
    """

    def __init__(self, explainer: FWASHAPExplainer):
        self.explainer = explainer
        plt.rcParams.update({
            'font.family': 'DejaVu Sans',
            'axes.spines.top': False,
            'axes.spines.right': False,
            'axes.grid': True,
            'grid.alpha': 0.3,
            'figure.facecolor': 'white',
        })

    def plot_waterfall(
        self,
        claim_data: Dict,
        fwa_probability: float,
        save_path: str = "shap_waterfall.png"
    ):
        """
        워터폴 차트: 각 특징이 FWA 확률에 기여하는 방향과 크기 시각화
        Waterfall chart showing each feature's contribution to FWA probability
        """
        result = self.explainer.compute_shap_values(claim_data, fwa_probability)
        shap_vals = result["shap_values"]
        feature_names = result["feature_names"]
        base_value = result["base_value"]

        # 절댓값 기준 상위 8개만 표시
        top_idx = np.argsort(np.abs(shap_vals))[-8:][::-1]
        shap_top = shap_vals[top_idx]
        names_top = [feature_names[i] for i in top_idx]

        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor(COLORS["light_bg"])
        ax.set_facecolor(COLORS["light_bg"])

        # 워터폴 바 그리기
        cumulative = base_value
        bar_starts = []
        bar_heights = []
        bar_colors = []

        for val in shap_top:
            bar_starts.append(cumulative)
            bar_heights.append(val)
            bar_colors.append(COLORS["positive"] if val > 0 else COLORS["negative"])
            cumulative += val

        y_pos = range(len(names_top))
        bars = ax.barh(
            y_pos, bar_heights, left=bar_starts,
            color=bar_colors, height=0.6, alpha=0.85,
            edgecolor='white', linewidth=1.5
        )

        # 값 레이블
        for i, (start, height, val) in enumerate(zip(bar_starts, bar_heights, shap_top)):
            x_pos = start + height + (0.01 if height >= 0 else -0.01)
            ha = 'left' if height >= 0 else 'right'
            ax.text(
                x_pos, i,
                f"{'+'if val > 0 else ''}{val:.3f}",
                va='center', ha=ha,
                fontsize=9, fontweight='bold',
                color=COLORS["positive"] if val > 0 else COLORS["negative"]
            )

        # 베이스라인
        ax.axvline(x=base_value, color=COLORS["primary"], linestyle=':', alpha=0.7, linewidth=1.5)
        ax.axvline(x=0.5, color=COLORS["critical"], linestyle='--', alpha=0.6, linewidth=1.5)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(names_top, fontsize=10)
        ax.set_xlabel("SHAP Value (FWA 확률 기여도)", fontsize=11)

        risk_level = "CRITICAL" if fwa_probability >= 0.8 else ("WARNING" if fwa_probability >= 0.5 else "NORMAL")
        ax.set_title(
            f"FWA 탐지 근거 분석 — Risk Score: {fwa_probability*100:.1f}% ({risk_level})",
            fontsize=13, fontweight='bold', color=COLORS["primary"], pad=15
        )

        # 범례
        pos_patch = mpatches.Patch(color=COLORS["positive"], alpha=0.85, label="FWA 가능성 높임 (↑)")
        neg_patch = mpatches.Patch(color=COLORS["negative"], alpha=0.85, label="FWA 가능성 낮춤 (↓)")
        ax.legend(handles=[pos_patch, neg_patch], loc='lower right', fontsize=9)

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=COLORS["light_bg"])
        plt.close()
        logger.info(f"워터폴 차트 저장: {save_path}")
        return save_path

    def plot_global_importance(
        self,
        n_samples: int = 500,
        save_path: str = "shap_global_importance.png"
    ):
        """
        전역 특징 중요도: 어떤 특징이 전반적으로 FWA 탐지에 중요한지
        Global feature importance across all claims
        """
        shap_matrix = self.explainer.compute_batch_shap(n_samples)
        mean_abs_shap = np.mean(np.abs(shap_matrix), axis=0)
        feature_names = self.explainer.feature_names

        # 정렬
        sorted_idx = np.argsort(mean_abs_shap)
        sorted_shap = mean_abs_shap[sorted_idx]
        sorted_names = [feature_names[i] for i in sorted_idx]

        fig, ax = plt.subplots(figsize=(11, 7))
        fig.patch.set_facecolor(COLORS["light_bg"])
        ax.set_facecolor(COLORS["light_bg"])

        # 그라데이션 색상
        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(sorted_shap)))
        bars = ax.barh(sorted_names, sorted_shap, color=colors, height=0.7, alpha=0.9)

        # 상위 3개 강조
        for i, (bar, val) in enumerate(zip(bars, sorted_shap)):
            ax.text(val + 0.003, bar.get_y() + bar.get_height()/2,
                    f"{val:.4f}", va='center', fontsize=9,
                    color=COLORS["primary"], fontweight='bold')
            if i >= len(sorted_shap) - 3:
                bar.set_edgecolor(COLORS["critical"])
                bar.set_linewidth(2)

        ax.set_xlabel("평균 |SHAP 값| (Mean |SHAP Value|)", fontsize=11)
        ax.set_title(
            "FWA 탐지 전역 특징 중요도\n(Global Feature Importance — Higher = More Important for Fraud Detection)",
            fontsize=13, fontweight='bold', color=COLORS["primary"]
        )
        ax.axvline(x=np.mean(sorted_shap), color=COLORS["accent"], linestyle='--',
                   alpha=0.7, label=f"평균값 ({np.mean(sorted_shap):.4f})")
        ax.legend(fontsize=9)

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=COLORS["light_bg"])
        plt.close()
        logger.info(f"전역 중요도 저장: {save_path}")
        return save_path

    def plot_beeswarm(
        self,
        n_samples: int = 300,
        save_path: str = "shap_beeswarm.png"
    ):
        """
        Beeswarm 플롯: 특징 값과 SHAP 기여도의 분포
        """
        shap_matrix = self.explainer.compute_batch_shap(n_samples)
        feature_names = self.explainer.feature_names

        mean_abs_shap = np.mean(np.abs(shap_matrix), axis=0)
        top_k = 8
        top_idx = np.argsort(mean_abs_shap)[-top_k:][::-1]

        shap_sub = shap_matrix[:, top_idx]
        names_sub = [feature_names[i] for i in top_idx]

        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor(COLORS["light_bg"])
        ax.set_facecolor(COLORS["light_bg"])

        for i, (name, shap_col) in enumerate(zip(names_sub, shap_sub.T)):
            # Beeswarm 효과를 위한 y 지터
            y_jitter = i + np.random.uniform(-0.3, 0.3, len(shap_col))
            sc = ax.scatter(
                shap_col, y_jitter,
                c=shap_col, cmap='RdBu_r', vmin=-0.5, vmax=0.5,
                alpha=0.5, s=12, rasterized=True
            )

        cbar = plt.colorbar(sc, ax=ax, shrink=0.6)
        cbar.set_label("SHAP Value\n(음수: 정상, 양수: FWA)", fontsize=9)

        ax.set_yticks(range(len(names_sub)))
        ax.set_yticklabels(names_sub, fontsize=10)
        ax.axvline(x=0, color='black', linewidth=1, alpha=0.5)
        ax.set_xlabel("SHAP Value (FWA 기여도)", fontsize=11)
        ax.set_title(
            "FWA 특징 분포 Beeswarm 분석\n(각 점 = 청구 건 1개, 색 = SHAP 값)",
            fontsize=13, fontweight='bold', color=COLORS["primary"]
        )
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=COLORS["light_bg"])
        plt.close()
        logger.info(f"Beeswarm 차트 저장: {save_path}")
        return save_path

    def plot_comprehensive_report(
        self,
        claim_data: Dict,
        fwa_probability: float,
        attention_weights: List[float],
        save_path: str = "fwa_shap_report.png"
    ):
        """
        종합 FWA 분석 리포트: SHAP + Attention + 리스크 요약 한 페이지
        """
        fig = plt.figure(figsize=(18, 12))
        fig.patch.set_facecolor(COLORS["light_bg"])
        fig.suptitle(
            f"FWA 종합 분석 리포트  |  Risk Score: {fwa_probability*100:.1f}%  |  "
            f"{'CRITICAL' if fwa_probability >= 0.8 else 'WARNING' if fwa_probability >= 0.5 else 'NORMAL'}",
            fontsize=16, fontweight='bold', color=COLORS["primary"], y=0.98
        )

        gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

        # ── 1. 리스크 게이지 (Risk Gauge) ─────────────────────────────
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.set_facecolor(COLORS["light_bg"])
        theta = np.linspace(0, np.pi, 100)
        ax1.plot(np.cos(theta), np.sin(theta), 'lightgray', linewidth=20)

        risk_theta = np.linspace(0, np.pi * fwa_probability, 100)
        risk_color = COLORS["critical"] if fwa_probability >= 0.8 else (
            COLORS["warning"] if fwa_probability >= 0.5 else COLORS["normal"])
        ax1.plot(np.cos(risk_theta), np.sin(risk_theta), color=risk_color, linewidth=20)

        ax1.text(0, 0.2, f"{fwa_probability*100:.1f}%",
                 ha='center', va='center', fontsize=28, fontweight='bold', color=risk_color)
        ax1.text(0, -0.15, "FWA Risk Score",
                 ha='center', va='center', fontsize=10, color=COLORS["primary"])
        ax1.set_xlim(-1.3, 1.3); ax1.set_ylim(-0.3, 1.3)
        ax1.set_aspect('equal'); ax1.axis('off')
        ax1.set_title("리스크 스코어", fontsize=12, fontweight='bold', color=COLORS["primary"])

        # ── 2. SHAP 워터폴 ─────────────────────────────────────────────
        ax2 = fig.add_subplot(gs[0, 1:])
        ax2.set_facecolor(COLORS["light_bg"])
        result = self.explainer.compute_shap_values(claim_data, fwa_probability)
        shap_vals = result["shap_values"]
        feature_names = result["feature_names"]

        top_idx = np.argsort(np.abs(shap_vals))[-7:][::-1]
        shap_top = shap_vals[top_idx]
        names_top = [feature_names[i] for i in top_idx]

        bar_colors = [COLORS["positive"] if v > 0 else COLORS["negative"] for v in shap_top]
        y_pos = range(len(names_top))
        ax2.barh(y_pos, shap_top, color=bar_colors, height=0.55, alpha=0.85,
                 edgecolor='white', linewidth=1)
        ax2.axvline(x=0, color='black', linewidth=1)
        ax2.set_yticks(y_pos); ax2.set_yticklabels(names_top, fontsize=9)
        ax2.set_title("SHAP 특징 기여도 분석", fontsize=12, fontweight='bold', color=COLORS["primary"])
        ax2.set_xlabel("SHAP 값 (양수=FWA 기여, 음수=정상 기여)")

        # ── 3. Attention 가중치 ────────────────────────────────────────
        ax3 = fig.add_subplot(gs[1, :2])
        ax3.set_facecolor(COLORS["light_bg"])
        months = [f"M-{len(attention_weights)-i}" for i in range(len(attention_weights))]
        attn_colors = [COLORS["critical"] if w > 0.12 else
                       (COLORS["warning"] if w > 0.08 else COLORS["accent"])
                       for w in attention_weights]
        bars = ax3.bar(months, attention_weights, color=attn_colors, alpha=0.85, edgecolor='white')
        avg_attn = np.mean(attention_weights)
        ax3.axhline(y=avg_attn, color=COLORS["primary"], linestyle='--', alpha=0.7,
                    label=f"평균 ({avg_attn:.3f})")
        ax3.set_title("시간별 이상 집중도 (Attention Weights)",
                      fontsize=12, fontweight='bold', color=COLORS["primary"])
        ax3.set_xlabel("청구 월 (최근 → 과거)"); ax3.set_ylabel("Attention Weight")
        ax3.legend(fontsize=9)

        # ── 4. 탐지 근거 요약 ────────────────────────────────────────
        ax4 = fig.add_subplot(gs[1, 2])
        ax4.set_facecolor(COLORS["light_bg"])
        ax4.axis('off')

        top3_idx = np.argsort(shap_vals)[-3:][::-1]
        evidence_text = f"탐지 근거 요약\n{'─'*28}\n\n"
        evidence_text += f"FWA 확률: {fwa_probability*100:.1f}%\n\n"
        evidence_text += "주요 FWA 신호:\n"
        for i, idx in enumerate(top3_idx):
            if shap_vals[idx] > 0:
                evidence_text += f"  {i+1}. {feature_names[idx][:20]}\n     기여도: +{shap_vals[idx]:.4f}\n"
        evidence_text += f"\n생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        ax4.text(0.05, 0.95, evidence_text,
                 transform=ax4.transAxes, fontsize=9,
                 verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle='round,pad=0.8', facecolor='white',
                           edgecolor=COLORS["critical"], linewidth=2))
        ax4.set_title("근거 요약", fontsize=12, fontweight='bold', color=COLORS["primary"])

        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=COLORS["light_bg"])
        plt.close()
        logger.info(f"종합 리포트 저장: {save_path}")
        return save_path


# ─── 3. 메인 실행 ────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("FWA SHAP 설명 가능성 분석 시작")

    explainer = FWASHAPExplainer()
    visualizer = FWASHAPVisualizer(explainer)

    # FWA 의심 케이스 시뮬레이션
    fwa_claim = {
        "patient_id": "P-88421",
        "provider_id": "DR-0042",
        "claim_amount": 12500,
        "hcc_score": 2.8,
        "icd_code": "E10",
        "ndc_code": "00169413701",  # Ozempic
        "is_fwa": True,
    }

    attn_weights = np.random.dirichlet(np.ones(12) * 2).tolist()
    attn_weights[0] *= 2.5  # 최근 월에 집중

    # 시각화 생성
    output_dir = "/sessions/intelligent-keen-bohr/mnt/FWAhackerthon_v4/"

    visualizer.plot_waterfall(fwa_claim, fwa_probability=0.87, save_path=os.path.join(output_dir, "shap_waterfall.png"))
    visualizer.plot_global_importance(n_samples=500, save_path=os.path.join(output_dir, "shap_global_importance.png"))
    visualizer.plot_beeswarm(n_samples=300, save_path=os.path.join(output_dir, "shap_beeswarm.png"))
    visualizer.plot_comprehensive_report(
        fwa_claim, fwa_probability=0.87,
        attention_weights=attn_weights,
        save_path=os.path.join(output_dir, "fwa_shap_report.png")
    )

    logger.info("SHAP 시각화 완료!")
    print("\nGenerated files:")
    for f in ["shap_waterfall.png", "shap_global_importance.png", "shap_beeswarm.png", "fwa_shap_report.png"]:
        print(f"  OK {os.path.join(output_dir, f)}")
