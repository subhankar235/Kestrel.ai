"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ExternalLink, Link2, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  posts as allPosts,
  formatDate,
  relationshipLabel,
  type Post,
  type PostRelationship,
} from "@/lib/mock-data";

const filters: { key: "ALL" | PostRelationship; label: string }[] = [
  { key: "ALL", label: "All posts" },
  { key: "STORY_CONTINUATION", label: "Continuations" },
  { key: "PREDICTION_RESOLUTION", label: "Resolutions" },
  { key: "TOPIC_RESURRECTION", label: "Resurrections" },
  { key: "CONCEPT_GAP", label: "Concept gaps" },
];

function PostCard({ post }: { post: Post }) {
  const [open, setOpen] = useState(false);

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
        {post.chapter ? (
          <Badge variant="outline" className="font-mono text-[10px]">
            Chapter {post.chapter}
          </Badge>
        ) : null}
        {post.verdict ? (
          <Badge
            variant="secondary"
            className={
              post.verdict === "correct"
                ? "bg-success/15 text-success"
                : post.verdict === "wrong"
                  ? "bg-destructive/15 text-destructive"
                  : "bg-warning/15 text-warning"
            }
          >
            verdict: {post.verdict}
          </Badge>
        ) : null}
        <span className="ml-auto font-mono text-[11px] text-muted-foreground">
          {formatDate(post.createdAt)} UTC
        </span>
      </div>

      <h2 className="font-display text-xl font-semibold leading-snug">{post.title}</h2>
      <p className="mt-3 whitespace-pre-line text-[15px] leading-relaxed text-foreground/85">
        {post.text}
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
              <dd className="mt-1 text-foreground/85">{post.rationale.whySelected}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-widest text-muted-foreground">Why now</dt>
              <dd className="mt-1 text-foreground/85">{post.rationale.whyNow}</dd>
            </div>
            {post.rationale.memoryRelationship ? (
              <div>
                <dt className="text-xs uppercase tracking-widest text-muted-foreground">
                  Memory relationship
                </dt>
                <dd className="mt-1 text-foreground/85">{post.rationale.memoryRelationship}</dd>
              </div>
            ) : null}
            <div>
              <dt className="text-xs uppercase tracking-widest text-muted-foreground">
                Editorial score
              </dt>
              <dd className="mt-1 font-mono">{post.score.toFixed(2)} / threshold 0.72</dd>
            </div>
          </dl>
        ) : null}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted-foreground">Sources:</span>
        {post.sources.map((s) => (
          <a
            key={s.url + s.label}
            href={s.url}
            target="_blank"
            rel="noreferrer"
            aria-label={`Source: ${s.label}`}
            className="inline-flex items-center gap-1 rounded-lg border border-[var(--surface-border)] px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:text-accent"
          >
            {s.label}
            <ExternalLink className="size-3" />
          </a>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {post.concepts.map((c) => (
          <span
            key={c}
            className="rounded-md bg-secondary px-2 py-0.5 font-mono text-[10px] text-muted-foreground"
          >
            #{c}
          </span>
        ))}
      </div>
    </article>
  );
}

export default function FeedPage() {
  const [filter, setFilter] = useState<"ALL" | PostRelationship>("ALL");
  const posts = useMemo(
    () => (filter === "ALL" ? allPosts : allPosts.filter((p) => p.relationship === filter)),
    [filter],
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
          Live · checking for updates
        </span>
      </div>

      <div className="mx-auto max-w-3xl space-y-5">
        {posts.length === 0 ? (
          <div className="surface-card p-10 text-center">
            <p className="font-display text-lg">No posts of this kind yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Ada is still researching — memory-driven posts appear as conditions are met.
            </p>
          </div>
        ) : (
          posts.map((p) => <PostCard key={p.id} post={p} />)
        )}
      </div>
    </div>
  );
}
