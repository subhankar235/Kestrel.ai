export interface PersonaIn {
  name: string;
  domain: string;
  voice?: string;
}

export interface InitRequest {
  persona: PersonaIn;
  publishIntervalMinutes?: number;
  observationPeriodHours?: number;
  startMode?: "immediate" | "scheduled";
  startAt?: string;
}

export interface InitResponse {
  agentId: string;
}
