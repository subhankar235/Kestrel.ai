import { Badge } from "@/components/ui/badge";
import type { PostRelationship } from "@/types/feed";

interface PredictionBadgeProps {
  relationship: PostRelationship;
}

const relationshipLabels: Record<PostRelationship, string> = {
  STORY_CONTINUATION: "Continuation",
  PREDICTION_RESOLUTION: "Prediction",
  TOPIC_RESURRECTION: "Resurrected",
  CONCEPT_GAP: "Concept Gap",
};

const relationshipColors: Record<PostRelationship, string> = {
  STORY_CONTINUATION: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  PREDICTION_RESOLUTION: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
  TOPIC_RESURRECTION: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
  CONCEPT_GAP: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300",
};

export function PredictionBadge({ relationship }: PredictionBadgeProps) {
  return (
    <Badge
      variant="secondary"
      className={`text-xs ${relationshipColors[relationship]}`}
    >
      {relationshipLabels[relationship]}
    </Badge>
  );
}
