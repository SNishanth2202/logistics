"""
evaluate.py
===========
Classification evaluation utilities used by train.py.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix, classification_report,
    brier_score_loss,
)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray,
                    y_prob: np.ndarray, model_name: str) -> dict:
    """Compute full classification metrics."""
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    roc = roc_auc_score(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)
    brier = brier_score_loss(y_true, y_prob)

    return {
        "Model": model_name,
        "Accuracy": round(acc, 4),
        "Precision": round(prec, 4),
        "Recall": round(rec, 4),
        "F1": round(f1, 4),
        "ROC_AUC": round(roc, 4),
        "PR_AUC": round(pr_auc, 4),
        "Brier_Score": round(brier, 4),
    }


def print_metrics(metrics: dict) -> None:
    print(f"\n  {'─'*50}")
    print(f"  Model      : {metrics['Model']}")
    print(f"  Accuracy   : {metrics['Accuracy']:.4f}")
    print(f"  Precision  : {metrics['Precision']:.4f}")
    print(f"  Recall     : {metrics['Recall']:.4f}   ← key metric (catch delays)")
    print(f"  F1-score   : {metrics['F1']:.4f}")
    print(f"  ROC-AUC    : {metrics['ROC_AUC']:.4f}")
    print(f"  PR-AUC     : {metrics['PR_AUC']:.4f}")
    print(f"  Brier Score: {metrics['Brier_Score']:.4f}")
    print(f"  {'─'*50}")


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray,
                          model_name: str, output_dir: Path) -> None:
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                xticklabels=["On-Time", "Delayed"],
                yticklabels=["On-Time", "Delayed"])
    ax.set_xlabel("Predicted", fontsize=11)
    ax.set_ylabel("Actual", fontsize=11)
    ax.set_title(f"Confusion Matrix — {model_name}", fontsize=12)
    fig.tight_layout()
    fname = model_name.lower().replace(" ", "_")
    fig.savefig(output_dir / f"confusion_matrix_{fname}.png", dpi=120)
    plt.close(fig)


def plot_roc_curves(results: list, output_dir: Path) -> None:
    """Plot all ROC curves on one figure."""
    from sklearn.metrics import roc_curve
    fig, ax = plt.subplots(figsize=(7, 6))
    for r in results:
        if "y_prob" in r and "y_true" in r:
            fpr, tpr, _ = roc_curve(r["y_true"], r["y_prob"])
            ax.plot(fpr, tpr, label=f"{r['model_name']} (AUC={r['metrics']['ROC_AUC']:.3f})")
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8)
    ax.set_xlabel("False Positive Rate", fontsize=11)
    ax.set_ylabel("True Positive Rate", fontsize=11)
    ax.set_title("ROC Curves — All Models", fontsize=13)
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(output_dir / "roc_curves.png", dpi=120)
    plt.close(fig)
    print(f"  ROC curves saved → {output_dir}/roc_curves.png")


def plot_pr_curves(results: list, output_dir: Path) -> None:
    """Plot Precision-Recall curves for all models."""
    from sklearn.metrics import precision_recall_curve
    fig, ax = plt.subplots(figsize=(7, 6))
    for r in results:
        if "y_prob" in r and "y_true" in r:
            prec, rec, _ = precision_recall_curve(r["y_true"], r["y_prob"])
            ax.plot(rec, prec, label=f"{r['model_name']} (AP={r['metrics']['PR_AUC']:.3f})")
    ax.set_xlabel("Recall", fontsize=11)
    ax.set_ylabel("Precision", fontsize=11)
    ax.set_title("Precision-Recall Curves — All Models", fontsize=13)
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(output_dir / "pr_curves.png", dpi=120)
    plt.close(fig)
    print(f"  PR curves saved → {output_dir}/pr_curves.png")


def save_comparison_table(all_metrics: list, output_path: Path) -> None:
    df = pd.DataFrame(all_metrics)
    df.to_csv(output_path, index=False)
    print(f"\nModel comparison saved → {output_path}")


def print_comparison_table(all_metrics: list) -> None:
    df = pd.DataFrame(all_metrics)
    print("\n" + "=" * 80)
    print("MODEL COMPARISON TABLE")
    print("=" * 80)
    print(df.to_string(index=False))
    print("=" * 80)
