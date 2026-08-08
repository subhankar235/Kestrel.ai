export interface PersonaIn {
  name: string;
  domain: string;
}

export interface InitRequest {
  persona: PersonaIn;
}

export interface InitResponse {
  agentId: string;
}
