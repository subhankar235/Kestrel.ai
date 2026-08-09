export interface DashboardPost {
  id: string;
  createdAt: string;
  text: string;
  topic?: string | null;
  rationale: string;
  sources: string[];
  relatedPostId?: string | null;
  relationship?: string | null;
}

export interface DashboardTopicDebt {
  id: string;
  title: string;
  score: number;
  reason: string;
  revisitCondition: string;
  status: string;
  createdAt: string;
}

export interface DashboardMemoryItem {
  id: string;
  text: string;
  score: number;
  metadata: Record<string, unknown>;
  concepts: string[];
  stories: string[];
  openQuestions: string[];
}

export interface DashboardSource {
  name: string;
  kind: string;
  configured: boolean;
  url?: string | null;
  items?: number;
  lastUsedAt?: string | null;
}

export interface DashboardCycleStatus {
  scheduleId: string;
  status: string;
  nextRunTime?: string | null;
  note?: string | null;
}

export interface DashboardCycleRun {
  id: string;
  cycleNumber: number;
  startedAt: string;
  finishedAt?: string | null;
  status: string;
  topic?: string | null;
  published: number;
  rejected: number;
  error?: string | null;
  details: Record<string, unknown>;
}

export interface AgentSummary {
  agentId: string;
  status: string;
  createdAt: string;
  name: string;
  domain: string;
  publishIntervalMinutes: number;
  observationPeriodHours: number;
}

export interface DashboardResponse {
  agentId: string;
  status: string;
  cycleCount: number;
  publishIntervalMinutes: number;
  observationPeriodHours: number;
  startMode: "immediate" | "scheduled";
  startAt?: string | null;
  persona: {
    name: string;
    domain: string;
    voiceConfig: Record<string, unknown>;
    createdAt: string;
  } | null;
  constitution: {
    version: string;
    rules: unknown;
    createdAt: string;
  } | null;
  posts: DashboardPost[];
  topicDebt: DashboardTopicDebt[];
  memory: DashboardMemoryItem[];
  cycle: DashboardCycleStatus | null;
  sources: DashboardSource[];
  cycles: DashboardCycleRun[];
}
