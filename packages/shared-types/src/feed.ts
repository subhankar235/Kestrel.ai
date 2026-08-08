export type PostRelationship =
  | "STORY_CONTINUATION"
  | "PREDICTION_RESOLUTION"
  | "TOPIC_RESURRECTION"
  | "CONCEPT_GAP";

export interface Post {
  id: string;
  createdAt: string;
  text: string;
  rationale: string;
  sources: string[];
  relatedPostId?: string;
  relationship?: PostRelationship;
}

export interface FeedResponse {
  posts: Post[];
}
