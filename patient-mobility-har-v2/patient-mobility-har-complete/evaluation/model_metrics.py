
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


def evaluate_model(y_true, y_pred, class_names, output_dir="evaluation/results"):
    """
    Evaluate a human activity recognition model using
    actual labels and predicted labels.
    """

    os.makedirs(output_dir, exist_ok=True)

    # Calculate performance metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(
        y_true, y_pred, average="weighted", zero_division=0
    )
    recall = recall_score(
        y_true, y_pred, average="weighted", zero_division=0
    )
    f1 = f1_score(
        y_true, y_pred, average="weighted", zero_division=0
    )

    print("\n===== MODEL PERFORMANCE METRICS =====")
    print(f"Accuracy  : {accuracy * 100:.2f}%")
    print(f"Precision : {precision * 100:.2f}%")
    print(f"Recall    : {recall * 100:.2f}%")
    print(f"F1-Score  : {f1 * 100:.2f}%")

    print("\n===== CLASSIFICATION REPORT =====")
    print(classification_report(
        y_true,
        y_pred,
        labels=list(range(len(class_names))),
        target_names=class_names,
        zero_division=0
    ))

    # Generate confusion matrix
    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=list(range(len(class_names)))
    )

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names
    )

    plt.title("Human Activity Recognition - Confusion Matrix")
    plt.xlabel("Predicted Activity")
    plt.ylabel("Actual Activity")
    plt.tight_layout()

    matrix_path = os.path.join(output_dir, "confusion_matrix.png")
    plt.savefig(matrix_path, dpi=300)
    plt.close()

    print(f"\nConfusion matrix saved to: {matrix_path}")

    return {
        "accuracy": round(float(accuracy) * 100, 2),
        "precision": round(float(precision) * 100, 2),
        "recall": round(float(recall) * 100, 2),
        "f1_score": round(float(f1) * 100, 2),
        "confusion_matrix": cm.tolist()
    }
