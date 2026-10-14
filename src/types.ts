export interface Citation {
  sourceId: string;
  pages: number[];
  note?: string;
  printedPages?: { pdfPage: number; printed: string }[];
}
export interface Revision {
  date: string;
  note: string;
}
export interface SourceSummary {
  sourceId: string;
  summary: string;
  details: string[];
  context: string;
  precisionNote?: string;
}
export interface LifecycleMilestone {
  id: string;
  name: string;
  kind:
    | "birth"
    | "death"
    | "formation"
    | "transformation"
    | "dissolution"
    | "career";
  date: string;
  endDate?: string;
  precision: "day" | "month" | "year";
  description: string;
  details: string[];
  citations: Citation[];
}
export interface Entry {
  id: string;
  milestones?: LifecycleMilestone[];
  lifecycleFor?: string;
  name: string;
  kind: "person" | "organization" | "event";
  role: string;
  description: string;
  pages: number[];
  citations: Citation[];
  history: Revision[];
  sourceSummaries?: SourceSummary[];
  accounts?: { sourceId: string; description: string; role?: string }[];
  aliases?: string[];
  evidence?: string;
  founders?: string;
  founderIds?: string[];
  members?: string[];
  date?: string;
  endDate?: string;
  precision?: string;
  lanes?: string[];
  people?: string[];
  organizations?: string[];
  status?: string;
  roster?: {
    sections: string[];
    bracketed: boolean;
    sourceId: string;
    pages: number[];
  };
}
export interface Source {
  id: string;
  shortTitle?: string;
  title: string;
  url: string;
  accessed: string;
  description: string;
  author?: string;
  subtitle?: string;
  published?: string;
  written?: string;
  localPath?: string;
  pageCount?: number;
  pageConvention?: string;
  sha256?: string;
  coverage?: string;
  evidenceIssues?: { pages: number[]; description: string }[];
  chapters?: { title: string; pdfStart: number; pdfEnd: number }[];
}
export interface Lane {
  id: string;
  name: string;
  color: string;
  sourceIds?: string[];
}
export interface Relationship {
  id: string;
  fromId: string;
  toId: string;
  label: string;
  description?: string;
  pages: number[];
  citations: Citation[];
  evidence?: string;
  date?: string;
  endDate?: string;
}
export interface EventLink {
  id: string;
  fromId: string;
  toId: string;
  label: string;
  kind: string;
  citations: Citation[];
}
export interface Archive {
  eventLinks?: EventLink[];
  references?: Entry[];
  version: number;
  updated: string;
  sources: Source[];
  people: Entry[];
  organizations: Entry[];
  events: Entry[];
  lanes: Lane[];
  relationships: Relationship[];
}
export interface Catalog {
  version: number;
  updated: string;
  sources: Source[];
  counts: Record<
    string,
    {
      people: number;
      organizations: number;
      events: number;
      relationships: number;
      lanes: number;
    }
  >;
  recordSources: Record<string, string[]>;
}
