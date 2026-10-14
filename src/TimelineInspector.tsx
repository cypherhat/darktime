import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { X, ChevronLeft } from "lucide-react";
import { catalog, dateLabel, entriesOf } from "./archive";
import type { Archive, Entry } from "./types";
const EventNarrative = lazy(() => import("./EventNarrative"));
export default function TimelineInspector({
  data,
  entry,
  onExplore,
  onClose,
  onTimeline,
}: {
  data: Archive;
  entry: Entry;
  onExplore: (id: string) => void;
  onClose: () => void;
  onTimeline: (id: string) => void;
}) {
  const [tab, setTab] = useState("Connections");
  const [history, setHistory] = useState<string[]>([]);
  const body = useRef<HTMLDivElement>(null);
  const records = new Map(entriesOf(data).map((record) => [record.id, record]));
  useEffect(() => {
    body.current?.scrollTo(0, 0);
  }, [entry.id]);
  const explore = (id: string) => {
    setHistory((previous) => [...previous, entry.id]);
    onExplore(id);
  };
  const link = (id: string, label?: string) => {
    const record = records.get(id);
    return record ? (
      <button
        key={`${id}:${label || ""}`}
        className="inspector-link"
        onClick={() => explore(id)}
      >
        <strong>{record.name}</strong>
        <small>{label || record.kind}</small>
      </button>
    ) : null;
  };
  const participants = [
    ...(entry.people || []),
    ...(entry.organizations || []),
  ];
  const influence = (data.eventLinks || []).filter(
    (edge) => edge.fromId === entry.id || edge.toId === entry.id,
  );
  const relationships = data.relationships.filter(
    (edge) => edge.fromId === entry.id || edge.toId === entry.id,
  );
  const related = data.events.filter(
    (event) =>
      event.id !== entry.id &&
      (entry.kind === "event"
        ? [...(event.people || []), ...(event.organizations || [])].some((id) =>
            participants.includes(id),
          )
        : [...(event.people || []), ...(event.organizations || [])].includes(
            entry.id,
          )),
  );
  return (
    <aside className="timeline-inspector" aria-label="Timeline event details">
      <header>
        <button
          aria-label="Back in event details"
          disabled={!history.length}
          onClick={() => {
            const id = history.at(-1)!;
            setHistory((previous) => previous.slice(0, -1));
            onExplore(id);
          }}
        >
          <ChevronLeft size={18} />
        </button>
        <span className="tiny-label">EXPLORE THE SELECTED RECORD</span>
        <button aria-label="Close timeline details" onClick={onClose}>
          <X size={18} />
        </button>
      </header>
      <div className="inspector-body" ref={body}>
        <span className="tiny-label">
          {entry.kind} · {entry.date ? dateLabel(entry) : entry.role}
        </span>
        <h2>{entry.name}</h2>
        <p>{entry.sourceSummaries?.[0]?.summary || entry.description}</p>
        <div
          className="inspector-tabs"
          role="tablist"
          aria-label="Event detail sections"
        >
          {["Connections", "Source account"].map((name) => (
            <button
              key={name}
              role="tab"
              aria-selected={tab === name}
              onClick={() => setTab(name)}
            >
              {name}
            </button>
          ))}
        </div>
        <section role="tabpanel" aria-label={tab}>
          {tab === "Source account" ? (
            <>
              {entry.kind === "event" ? (
                <Suspense fallback={<p>Loading source account…</p>}>
                  <EventNarrative entry={entry} />
                </Suspense>
              ) : (
                entry.accounts?.map((account) => (
                  <article key={account.sourceId}>
                    <h4>
                      {
                        catalog.sources.find(
                          (source) => source.id === account.sourceId,
                        )?.title
                      }
                    </h4>
                    <p>{account.description}</p>
                  </article>
                ))
              )}
              <h4>Source references</h4>
              {entry.citations.map((citation, index) => (
                <p key={index} className="inspector-citation">
                  {
                    catalog.sources.find(
                      (source) => source.id === citation.sourceId,
                    )?.title
                  }{" "}
                  · pages {citation.pages.join(", ")}
                  {citation.note && ` · ${citation.note}`}
                </p>
              ))}
            </>
          ) : (
            <>
              {!!participants.length && (
                <>
                  <h4>Participants & organizations</h4>
                  {participants.map((id) => link(id))}
                </>
              )}
              {!!influence.length && (
                <>
                  <h4>Influence described in sources</h4>
                  {influence.map((edge) =>
                    link(
                      edge.fromId === entry.id ? edge.toId : edge.fromId,
                      edge.label,
                    ),
                  )}
                </>
              )}
              {!!relationships.length && (
                <>
                  <h4>Cited affiliations</h4>
                  {relationships.map((edge) =>
                    link(
                      edge.fromId === entry.id ? edge.toId : edge.fromId,
                      edge.label,
                    ),
                  )}
                </>
              )}
              <h4>
                {entry.kind === "event"
                  ? "Events with shared participants"
                  : "Events involving this record"}
              </h4>
              {entry.kind === "event" && (
                <p className="view-note">
                  Shared participants identify overlap; they do not by
                  themselves establish influence.
                </p>
              )}
              {related.length ? (
                related.map((event) => link(event.id, dateLabel(event)))
              ) : (
                <p>No other cited events in the selected sources.</p>
              )}
            </>
          )}
        </section>
      </div>
    </aside>
  );
}
