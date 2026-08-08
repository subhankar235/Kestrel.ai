"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

interface RationalePanelProps {
  rationale: string;
}

export function RationalePanel({ rationale }: RationalePanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="rounded-md bg-muted p-3">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between text-sm font-medium text-muted-foreground hover:text-foreground"
        aria-expanded={isExpanded}
      >
        <span>Why this was published</span>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </button>
      {isExpanded && (
        <p className="mt-2 text-sm text-muted-foreground whitespace-pre-wrap">
          {rationale}
        </p>
      )}
    </div>
  );
}
