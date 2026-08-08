import { Badge } from "@/components/ui/badge";

interface RejectedTopicBadgeProps {
  reason?: string;
}

export function RejectedTopicBadge({ reason }: RejectedTopicBadgeProps) {
  return (
    <Badge variant="outline" className="text-xs text-muted-foreground">
      {reason || "Rejected"}
    </Badge>
  );
}
