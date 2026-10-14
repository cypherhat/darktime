import type { Archive, Entry } from "./types";
/** Lifecycle dates are explicit cited data, never inferred from the first/last event. */
export function lifecycleEvents(data: Archive): Entry[] {
  return [...data.people, ...data.organizations].flatMap((record) =>
    (record.milestones || []).map((milestone) => ({
      id: `lifecycle:${record.id}:${milestone.id}`,
      name: `${record.name} · ${milestone.name}`,
      kind: "event" as const,
      lifecycleFor: record.id,
      role: milestone.kind,
      date: milestone.date,
      endDate: milestone.endDate,
      precision: milestone.precision,
      description: milestone.description,
      pages: milestone.citations[0]?.pages || [],
      citations: milestone.citations,
      people: record.kind === "person" ? [record.id] : [],
      organizations: record.kind === "organization" ? [record.id] : [],
      lanes: [],
      history: record.history,
      sourceSummaries: milestone.citations.map((citation) => ({
        sourceId: citation.sourceId,
        summary: milestone.description,
        details: milestone.details,
        context: `This cited ${milestone.kind} milestone belongs to ${record.name}'s lifecycle. It is distinct from the first or last event in which the record appears.`,
        precisionNote:
          milestone.precision === "year"
            ? "Only the year is given; January 1 is a plotting anchor."
            : undefined,
      })),
      evidence:
        "Lifecycle milestone · date and account attributed to cited source",
    })),
  );
}
export function entityProjection(
  data: Archive,
  ids: string[],
  events: Entry[],
  sourceIds: string[],
): Archive {
  const records = new Map(
    [...data.people, ...data.organizations, ...(data.references || [])].map(
      (record) => [record.id, record],
    ),
  );
  const colors = [
    "#d3b476",
    "#99b5cf",
    "#a1bc9b",
    "#c48b91",
    "#b09dbe",
    "#8dbdbb",
  ];
  const lanes = ids
    .filter((id) => records.has(id))
    .map((id, index) => ({
      id: `entity:${id}`,
      name: records.get(id)!.name,
      color: colors[index % colors.length],
      sourceIds: [
        ...new Set(
          records
            .get(id)!
            .citations.filter((c) => sourceIds.includes(c.sourceId))
            .map((c) => c.sourceId),
        ),
      ],
    }));
  const selected = events
    .filter((event) =>
      event.citations.some((c) => sourceIds.includes(c.sourceId)),
    )
    .map((event) => ({
      ...event,
      lanes: ids
        .filter((id) =>
          [...(event.people || []), ...(event.organizations || [])].includes(
            id,
          ),
        )
        .map((id) => `entity:${id}`),
    }))
    .filter((event) => event.lanes.length);
  return { ...data, lanes, events: selected };
}
