"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ExternalLink, Link2, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useFeed } from "@/hooks/use-feed";
import type { Post, PostRelationship } from "@/types/feed";

const filters: { key: "ALL" | PostRelationship; label: string }[] = [
  { key: "ALL", label: "All posts" },
  { key: "STORY_CONTINUATION", label: "Continuations" },
  { key: "PREDICTION_RESOLUTION", label: "Resolutions" },
  { key: "TOPIC_RESURRECTION", label: "Resurrections" },
  { key: "CONCEPT_GAP", label: "Concept gaps" },
];

const relationshipLabel: Record<PostRelationship, string> = {
  STORY_CONTINUATION: "Story continuation",
  PREDICTION_RESOLUTION: "Prediction resolution",
  TOPIC_RESURRECTION: "Topic resurrection",
  CONCEPT_GAP: "Concept gap",
};

function cleanPostText(text: string) {
  return text
    .split("\n")
    .map((line) => line.trim().replace(/^#{1,6}\s*/, ""))
    .filter((line) => line && !["Share", "Key Findings"].includes(line))
    .join("\n");
}

function PostCard({ post }: { post: Post }) {
  const [open, setOpen] = useState(false);
  const cleanText = cleanPostText(post.text);
  const title = cleanText.split(/[.!?]\s/)[0] || post.id;

  return (
    <article className="surface-card p-6">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {post.relationship ? (
          <Badge variant="secondary" className="bg-primary/15 text-primary">
            <Sparkles className="mr-1 size-3" />
            {relationshipLabel[post.relationship]}
          </Badge>
        ) : (
          <Badge variant="secondary">New topic</Badge>
        )}
        <span className="ml-auto font-mono text-[11px] text-muted-foreground">
          Published {new Date(post.createdAt).toLocaleString()}
        </span>
      </div>

      <p className="mb-2 text-xs uppercase tracking-widest text-muted-foreground">Topic</p>
      <h2 className="font-display text-xl font-semibold leading-snug">{post.topic || title}</h2>
      <p className="mt-3 whitespace-pre-line text-[15px] leading-relaxed text-foreground/85">
        {cleanText}
      </p>

      {post.relatedPostId ? (
        <p className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-secondary px-2.5 py-1 font-mono text-[11px] text-muted-foreground">
          <Link2 className="size-3" /> references {post.relatedPostId}
        </p>
      ) : null}

      <div className="mt-5 rounded-2xl border border-[var(--surface-border)] bg-secondary/40">
        <button
          type="button"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium"
        >
          Why Ada published this
          <ChevronDown
            className={`size-4 transition-transform ${open ? "rotate-180" : ""}`}
          />
        </button>
        {open ? (
          <dl className="space-y-3 border-t border-[var(--surface-border)] px-4 py-4 text-sm">
            <div>
              <dt className="text-xs uppercase tracking-widest text-muted-foreground">
                Why selected
              </dt>
              <dd className="mt-1 text-foreground/85">{post.rationale}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-widest text-muted-foreground">Why now</dt>
              <dd className="mt-1 text-foreground/85">Live data from the agent feed.</dd>
            </div>
            {post.relationship ? (
              <div>
                <dt className="text-xs uppercase tracking-widest text-muted-foreground">
                  Memory relationship
                </dt>
                <dd className="mt-1 text-foreground/85">{relationshipLabel[post.relationship]}</dd>
              </div>
            ) : null}
            <div>
              <dt className="text-xs uppercase tracking-widest text-muted-foreground">
                Editorial score
              </dt>
              <dd className="mt-1 font-mono">Backend score not provided</dd>
            </div>
          </dl>
        ) : null}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted-foreground">Sources:</span>
        {post.sources.map((url) => (
          <a
            key={url}
            href={url}
            target="_blank"
            rel="noreferrer"
            aria-label={`Source: ${url}`}
            className="inline-flex items-center gap-1 rounded-lg border border-[var(--surface-border)] px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:text-accent"
          >
            {new URL(url).hostname}
            <ExternalLink className="size-3" />
          </a>
        ))}
      </div>

    </article>
  );
}

export default function FeedPage() {
  const [filter, setFilter] = useState<"ALL" | PostRelationship>("ALL");
  const [agentId] = useState<string | null>(() =>
    typeof window === "undefined" ? null : window.localStorage.getItem("kestrel.agentId"),
  );
  const { posts: allPosts, status, error, lastCheckedAt } = useFeed(agentId, undefined, true);
  const uniquePosts = useMemo(() => {
    const seenTopics = new Set<string>();
    return allPosts.filter((post) => {
      const key = post.topic?.trim().toLowerCase();
      if (!key) return true;
      if (seenTopics.has(key)) return false;
      seenTopics.add(key);
      return true;
    });
  }, [allPosts]);
  const posts = useMemo(
    () => (filter === "ALL" ? uniquePosts : uniquePosts.filter((p) => p.relationship === filter)),
    [filter, uniquePosts],
  );

  return (
    <div className="space-y-5 pb-12">
      <div className="flex flex-wrap items-center gap-2">
        {filters.map((f) => (
          <Button
            key={f.key}
            size="sm"
            variant={filter === f.key ? "default" : "outline"}
            className="rounded-full"
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </Button>
        ))}
        <span className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
          <span className="relative flex size-2">
            <span className="absolute inline-flex size-2 animate-pulse-ring rounded-full bg-success" />
            <span className="relative inline-flex size-2 rounded-full bg-success" />
          </span>
          {status === "error" ? error : lastCheckedAt ? "Live · updated" : "Loading feed..."}
        </span>
      </div>

      <div className="mx-auto max-w-3xl space-y-5">
        {posts.length === 0 ? (
          <div className="surface-card p-10 text-center">
            <p className="font-display text-lg">No posts of this kind yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {status === "error" ? error : "No posts have been published yet."}
            </p>
          </div>
        ) : (
          posts.map((p) => <PostCard key={p.id} post={p} />)
        )}
      </div>
    </div>
  );
}
