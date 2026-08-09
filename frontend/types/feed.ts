export type {
  PersonaIn,
  InitRequest,
  InitResponse,
  PostRelationship,
  Post,
  FeedResponse,
} from "shared-types";

export interface AgentInitOptions {
  publishIntervalMinutes: number;
  observationPeriodHours: number;
  startMode: "immediate" | "scheduled";
  startAt?: string;
}
