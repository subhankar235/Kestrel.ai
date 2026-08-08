import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { RationalePanel } from "./rationale-panel";
import { PredictionBadge } from "./prediction-badge";
import type { Post } from "@/types/feed";

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffDay > 0) return `${diffDay}d ago`;
  if (diffHour > 0) return `${diffHour}h ago`;
  if (diffMin > 0) return `${diffMin}m ago`;
  return "just now";
}

interface PostCardProps {
  post: Post;
}

export function PostCard({ post }: PostCardProps) {
  return (
    <article className="mb-4">
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <time dateTime={post.createdAt} title={post.createdAt}>
              {formatRelativeTime(post.createdAt)}
            </time>
            {post.relationship && <PredictionBadge relationship={post.relationship} />}
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="whitespace-pre-wrap">{post.text}</p>

          {post.sources.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {post.sources.map((source, i) => (
                <a
                  key={i}
                  href={source}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-muted-foreground hover:text-foreground underline"
                  aria-label={`Source: ${new URL(source).hostname}`}
                >
                  {new URL(source).hostname}
                </a>
              ))}
            </div>
          )}

          <RationalePanel rationale={post.rationale} />
        </CardContent>
      </Card>
    </article>
  );
}
