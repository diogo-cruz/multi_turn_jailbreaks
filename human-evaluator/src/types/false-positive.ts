// TypeScript types for false positive annotation system

export interface SuccessfulJailbreak {
  // Configuration from the first line
  config: {
    target_model: string;
    test_case: string;
    jailbreak_tactic: string;
    task: string;
    category: string;
    timestamp: string;
    turn_type: 'single' | 'multi';
  };
  
  // The final round that achieved the goal
  finalRound: {
    round: number;
    user: string;
    assistant: string;
    score: number | string;
  };
  
  // File information
  filename: string;
  relativePath: string; // relative to clean_results/final_runs/
  goalAchieved: boolean;
  
  // Annotation status
  fpAnnotated: boolean;
  fpEvaluator?: string;
  fpDecision?: 'true_positive' | 'false_positive';
  fpNote?: string;
}

export interface FalsePositiveAnnotation {
  relative_path: string;
  filename: string;
  test_case: string;
  jailbreak_tactic: string;
  target_model: string;
  task: string;
  final_round: number;
  evaluator: string;
  decision: 'true_positive' | 'false_positive';
  note: string;
  jailbroken_output: string;
  timestamp: string;
}

export interface FPDirectoryInfo {
  path: string;
  totalSuccessfulFiles: number;
  annotatedFiles: number;
  pendingFiles: number;
  files: {
    filename: string;
    fullPath: string;
    relativePath: string;
    fpAnnotated: boolean;
    fpEvaluator?: string;
    fpDecision?: 'true_positive' | 'false_positive';
  }[];
}

export interface FPScanResult {
  filename: string;
  relativePath: string;
  hasGoalAchieved: boolean;
  goalAchieved?: boolean;
  fpAnnotated: boolean;
  fpEvaluator?: string;
  isCorrupted: boolean;
}