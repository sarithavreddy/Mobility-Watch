import { api } from "./api";

export interface PerClassMetric {
  precision: number;
  recall: number;
  f1_score: number;
  support: number;
}

export interface MLMetrics {
  trained_at: string | null;
  data_source: "real" | "synthetic" | null;
  split_method: string | null;
  held_out_subjects: string[] | null;
  n_train_samples: number | null;
  n_test_samples: number | null;
  n_total_samples: number | null;
  labels: string[] | null;
  accuracy: number | null;
  precision_macro: number | null;
  recall_macro: number | null;
  f1_macro: number | null;
  per_class: Record<string, PerClassMetric> | null;
  confusion_matrix: number[][] | null;
  confusion_matrix_labels: string[] | null;
  model_type: string | null;
  dataset_info: Record<string, unknown> | null;
}

export async function getMLMetrics(): Promise<MLMetrics> {
  const { data } = await api.get<MLMetrics>("/ml/metrics");
  return data;
}
