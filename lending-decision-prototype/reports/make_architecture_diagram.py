"""One-off script to render the architecture diagram (Section 12) as a PNG."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.patheffects import withStroke

STAGES = [
    ("Customer / Loan Application", "api/main.py — LoanApplicationRequest", "#4C5FD5"),
    ("Feature Layer", "src/features.py, src/model_features.py", "#4C5FD5"),
    ("Credit Risk Model", "src/model_loader.py — Assignment-1 LightGBM", "#B3005E"),
    ("Probability of Default", "PD (float, 0-1)", "#B3005E"),
    ("Score Layer", "src/scoring.py — log-odds scorecard scaling", "#1F3864"),
    ("Risk Layer", "src/risk.py — VERY_LOW .. VERY_HIGH bands", "#1F3864"),
    ("Affordability Assessment", "src/affordability.py — DTI, installment, max amount", "#1F3864"),
    ("Policy Layer", "src/policy.py + config/lending_policy.yaml", "#1F3864"),
    ("Decision Layer", "src/decision.py — precedence + reason codes", "#1F3864"),
    ("APPROVE / REJECT / REFER / COUNTER_OFFER", "api response", "#2E7D32"),
]

fig, ax = plt.subplots(figsize=(7.5, 13))
ax.set_xlim(0, 10)
ax.set_ylim(0, len(STAGES) * 2 + 1)
ax.axis("off")
fig.patch.set_facecolor("white")

box_h = 1.35
gap = 2.0
y = len(STAGES) * gap

centers = []
for i, (title, subtitle, color) in enumerate(STAGES):
    y_top = y
    box = FancyBboxPatch((0.6, y_top - box_h), 8.8, box_h,
                          boxstyle="round,pad=0.08,rounding_size=0.18",
                          linewidth=1.4, edgecolor=color, facecolor=color, alpha=0.12)
    ax.add_patch(box)
    ax.text(5.0, y_top - box_h * 0.38, title, ha="center", va="center",
            fontsize=13, fontweight="bold", color=color)
    ax.text(5.0, y_top - box_h * 0.78, subtitle, ha="center", va="center",
            fontsize=9.2, color="#333333")
    centers.append(y_top - box_h)
    y -= gap

for i in range(len(STAGES) - 1):
    y_from = centers[i]
    y_to = y_from - (gap - box_h)
    arrow = FancyArrowPatch((5.0, y_from), (5.0, y_to + 0.05),
                             arrowstyle="-|>", mutation_scale=18,
                             linewidth=1.6, color="#555555")
    ax.add_patch(arrow)

ax.set_title("Lending Decision Prototype — Architecture (Section 12)",
             fontsize=14, fontweight="bold", pad=18)

plt.tight_layout()
plt.savefig("reports/architecture_diagram.png", dpi=160, facecolor="white", bbox_inches="tight")
print("saved reports/architecture_diagram.png")
