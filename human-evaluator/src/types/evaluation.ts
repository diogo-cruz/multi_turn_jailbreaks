// TypeScript types for jailbreak evaluation

export interface ConversationTurn {
  round: number;
  user: string;
  assistant: string;
  score: number | string; // Can be numeric or "refused"
  summary?: string;
  token_usage?: {
    model: string;
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    cost: string;
  };
  evaluator_token_usage?: any;
  // Human evaluation fields
  human_score?: number;
  human_evaluator?: string;
  human_eval_timestamp?: string;
}

export interface EvaluationConfig {
  target_base_url: string;
  target_model: string;
  target_temp: number;
  attacker_base_url: string;
  attacker_model: string;
  attacker_temp: number;
  evaluator_model?: string;
  test_case: string;
  turn_type: 'single' | 'multi';
  jailbreak_tactic: string;
  task: string;
  max_rounds: number;
  category: string;
  timestamp: string;
  reasoning?: string;
  samples: number;
  gen_score_rubric: boolean;
  gen_score_rubric_test_cases?: any;
}

export interface EvaluationCriteria {
  criteria: string;
}

export interface GoalAchieved {
  goal_achieved: boolean;
}

export interface EvaluationFile {
  config: EvaluationConfig;
  criteria?: EvaluationCriteria;
  turns: ConversationTurn[];
  goalAchieved?: GoalAchieved;
  filename: string;
  humanEvaluated: boolean;
  humanEvaluator?: string;
}

export interface DirectoryInfo {
  path: string;
  totalFiles: number;
  evaluatedFiles: number;
  pendingFiles: number;
  files: {
    filename: string;
    humanEvaluated: boolean;
    humanEvaluator?: string;
  }[];
}

export interface StrongRejectCriteria {
  refusal: {
    description: string;
    scale: string;
  };
  convincingness: {
    description: string;
    scale: string;
  };
  specificity: {
    description: string;
    scale: string;
  };
  finalScore: {
    formula: string;
    successThreshold: string;
  };
}