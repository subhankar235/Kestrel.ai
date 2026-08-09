import { PostCard } from "./post-card";
import type { Post } from "@/types/feed";

interface StoryThreadProps {
  posts: Post[];
  chapterNumber: number;
}

export function StoryThread({ posts, chapterNumber }: StoryThreadProps) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm font-medium text-muted-foreground">
          Chapter {chapterNumber}
        </span>
        <div className="flex-1 h-px bg-border" />
      </div>
      <div className="space-y-4 pl-4 border-l-2 border-muted">
        {posts.map((post) => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>
    </div>
  );
}
