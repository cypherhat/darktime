import type { Archive, Entry, Catalog, SourceSummary } from "./types";
import manifest from "./data/catalog.json";
export const catalog = manifest as Catalog;
const modules = import.meta.glob<{ default: Archive }>(
  "./data/collections/*.json",
);
const loaders = Object.fromEntries(
  catalog.sources.map((s) => [
    s.id,
    () => modules[`./data/collections/${s.id}.json`](),
  ]),
);
export async function loadArchive(id: string): Promise<Archive> {
  const keys =
    id === "all"
      ? Object.keys(loaders)
      : id.split(",").filter((key) => key in loaders);
  const archives = await Promise.all(
    keys.map(
      async (key) =>
        (await loaders[key as keyof typeof loaders]()).default as Archive,
    ),
  );
  const unique = <T extends { id: string }>(items: T[]) =>
    Array.from(new Map(items.map((e) => [e.id, e])).values());
  return {
    ...archives[0],
    people: unique(archives.flatMap((a) => a.people)),
    organizations: unique(archives.flatMap((a) => a.organizations)),
    events: unique(archives.flatMap((a) => a.events)),
    relationships: unique(archives.flatMap((a) => a.relationships)),
    lanes: unique(archives.flatMap((a) => a.lanes)),
    references: unique(archives.flatMap((a) => a.references || [])),
    eventLinks: unique(archives.flatMap((a) => a.eventLinks || [])),
  };
}
export const entriesOf = (a: Archive): Entry[] =>
  Array.from(
    new Map(
      [
        ...a.people,
        ...a.organizations,
        ...a.events,
        ...(a.references || []),
      ].map((e) => [e.id, e]),
    ).values(),
  );
export function matches(e: Entry, query: string) {
  return [
    e.name,
    e.role,
    e.description,
    ...(e.aliases || []),
    ...(e.roster?.sections || []),
    ...(e.accounts || []).map((a) => a.description),
  ]
    .join(" ")
    .toLowerCase()
    .includes(query.toLowerCase());
}
export function dateLabel(e: Entry) {
  const start =
    e.precision === "year"
      ? e.date!.slice(0, 4)
      : e.precision === "month"
        ? e.date!.slice(0, 7)
        : e.date!;
  const end = e.endDate
    ? e.precision === "year"
      ? e.endDate.slice(0, 4)
      : e.precision === "month"
        ? e.endDate.slice(0, 7)
        : e.endDate
    : "";
  return start + (end ? " – " + end : "");
}

const narrativeModules = import.meta.glob<{
  default: Record<string, SourceSummary[]>;
}>("./data/narratives/*.json");
export async function loadNarratives(sourceId: string) {
  return (await narrativeModules[`./data/narratives/${sourceId}.json`]())
    .default;
}
export async function loadFullArchive() {
  const archive = await loadArchive("all");
  const books = await Promise.all(
    catalog.sources.map((s) => loadNarratives(s.id)),
  );
  return {
    ...archive,
    events: archive.events.map((e) => ({
      ...e,
      sourceSummaries: books.flatMap((book) => book[e.id] || []),
    })),
  };
}
