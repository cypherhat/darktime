import React, {
  useState,
  useCallback,
  useMemo,
  useEffect,
  useRef,
  lazy,
  Suspense,
} from "react";
import { createRoot } from "react-dom/client";
import {
  Search,
  ArrowUpRight,
  Network,
  Clock,
  Users,
  Building2,
  BookOpen,
  X,
  Download,
  Menu,
  ChevronLeft,
  ChevronRight,
  GitBranch,
  Link as LinkIcon,
} from "lucide-react";
import type { Archive, Entry, Citation, Source } from "./types";
import {
  catalog,
  loadArchive,
  loadFullArchive,
  entriesOf,
  matches,
  dateLabel,
} from "./archive";
import { lifecycleEvents, entityProjection } from "./lifecycle";
import "./style.css";
const EventNarrative = lazy(() => import("./EventNarrative"));
const TimelineInspector = lazy(() => import("./TimelineInspector"));
const Timeline = lazy(() => import("./Timeline"));
const Connections = lazy(() => import("./Connections"));
const PAGE_SIZE = 24;
function initialScope() {
  const url = new URL(location.href);
  const scope = url.searchParams.get("collection");
  if (scope === "all") return scope;
  const valid = scope
    ?.split(",")
    .filter((id) => catalog.sources.some((source) => source.id === id));
  if (valid?.length) return valid.join(",");
  const record = decodeURIComponent(location.hash.slice(1));
  return catalog.recordSources[record]?.[0] || "tragedy";
}
function selectedSourcesForScope(scope: string) {
  return scope === "all" ? catalog.sources.map((s) => s.id) : scope.split(",");
}
function labelFor(e: Entry, scope: string) {
  return (
    e.sourceSummaries?.find(
      (a) => scope === "all" || scope.split(",").includes(a.sourceId),
    )?.summary ||
    e.accounts?.find(
      (a) => scope === "all" || scope.split(",").includes(a.sourceId),
    )?.description ||
    e.description
  );
}
function CitationList({
  citations,
  sources,
}: {
  citations: Citation[];
  sources: Source[];
}) {
  return (
    <div className="citation-list">
      {citations.map((c, i) => {
        const source = sources.find((s) => s.id === c.sourceId);
        if (!source) return null;
        return (
          <div className="citation" key={`${c.sourceId}-${i}`}>
            <span>{source.title}</span>
            <strong>
              {source.pageCount ? "PDF" : "Transcription"} pp.{" "}
              {c.pages.join(", ")}
            </strong>
            {c.printedPages && (
              <small>
                Printed-page references:{" "}
                {c.printedPages
                  .map((p) => `${p.pdfPage} → ${p.printed}`)
                  .join("; ")}
              </small>
            )}
            {c.note && <small>{c.note}</small>}
            {source.url ? (
              <small>
                Offline source record · {source.author || source.title}
              </small>
            ) : (
              <small>
                Local research file: {source.localPath} · page numbers refer to
                the PDF.
              </small>
            )}
          </div>
        );
      })}
    </div>
  );
}
function Pager({
  page,
  total,
  onChange,
}: {
  page: number;
  total: number;
  onChange: (p: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  return (
    <div className="pager">
      <span>
        {total
          ? `${page * PAGE_SIZE + 1}–${Math.min((page + 1) * PAGE_SIZE, total)}`
          : "0"}{" "}
        of {total} records
      </span>
      <div>
        <button
          aria-label="Previous page"
          disabled={!page}
          onClick={() => onChange(page - 1)}
        >
          <ChevronLeft size={15} />
        </button>
        <span>
          Page {page + 1} / {pages}
        </span>
        <button
          aria-label="Next page"
          disabled={page + 1 >= pages}
          onClick={() => onChange(page + 1)}
        >
          <ChevronRight size={15} />
        </button>
      </div>
    </div>
  );
}
function App() {
  const [scope, setScope] = useState(initialScope);
  const [data, setData] = useState<Archive | null>(null);
  const [error, setError] = useState("");
  const [view, setView] = useState("Timelines");
  const [query, setQuery] = useState("");
  const [active, setActive] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(
    decodeURIComponent(location.hash.slice(1)) || null,
  );
  const [highlighted, setHighlighted] = useState<string | null>(null);
  const [inspected, setInspected] = useState<string | null>(null);
  const highlight = useCallback((id: string) => {
    setHighlighted(id);
    setInspected(id);
  }, []);
  const [menu, setMenu] = useState(false);
  const [page, setPage] = useState(0);
  const [timelinePage, setTimelinePage] = useState(0);
  const [evidenceFilter, setEvidenceFilter] = useState("all");
  const [sort, setSort] = useState("name");
  const [focus, setFocus] = useState("");
  const [includeInferred, setIncludeInferred] = useState(true);
  const [range, setRange] = useState<[number, number] | null>(null);
  const [overlayLinks, setOverlayLinks] = useState(true);
  const [entityFilter, setEntityFilter] = useState("");
  const [entityTracks, setEntityTracks] = useState<string[]>(() =>
    (new URL(location.href).searchParams.get("tracks") || "")
      .split(",")
      .filter(Boolean),
  );
  const [entityMode, setEntityMode] = useState(() =>
    new URL(location.href).searchParams.has("tracks"),
  );
  const [trackToAdd, setTrackToAdd] = useState("");
  const [connectionPage, setConnectionPage] = useState(0);
  const detailRef = useRef<HTMLElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError("");
    loadArchive(scope)
      .then((next) => {
        if (cancelled) return;
        setData(next);
        setActive(next.lanes.map((l) => l.id));
        setRange(null);
        setEntityFilter("");
        setFocus("");
        setQuery("");
        setPage(0);
      })
      .catch(
        () =>
          !cancelled &&
          setError(
            "Unable to load this collection. Check your connection and reload.",
          ),
      );
    return () => {
      cancelled = true;
    };
  }, [scope]);
  useEffect(() => {
    setPage(0);
    setTimelinePage(0);
    setConnectionPage(0);
  }, [query, view, evidenceFilter, sort, focus, includeInferred]);
  useEffect(() => setTimelinePage(0), [range, entityFilter, active]);
  useEffect(() => {
    const sync = () => {
      const id = decodeURIComponent(location.hash.slice(1));
      const target = new URL(location.href).searchParams.get("collection");
      if (
        target &&
        target !== scope &&
        (target === "all" ||
          target
            .split(",")
            .every((id) => catalog.sources.some((s) => s.id === id)))
      )
        setScope(target);
      else if (
        id &&
        !catalog.recordSources[id]?.some((sourceId) =>
          scope.split(",").includes(sourceId),
        ) &&
        scope !== "all"
      )
        setScope(catalog.recordSources[id]?.[0] || scope);
      setSelected(id || null);
    };
    window.addEventListener("popstate", sync);
    window.addEventListener("hashchange", sync);
    return () => {
      window.removeEventListener("popstate", sync);
      window.removeEventListener("hashchange", sync);
    };
  }, [scope]);
  useEffect(() => {
    if (!selected) return;
    previousFocus.current = document.activeElement as HTMLElement;
    const old = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSelected(null);
        history.replaceState(null, "", location.pathname + location.search);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = old;
      document.removeEventListener("keydown", onKey);
      previousFocus.current?.focus();
    };
  }, [selected]);
  useEffect(() => {
    if (selected && data) {
      detailRef.current?.scrollTo(0, 0);
      detailRef.current?.querySelector<HTMLElement>("button")?.focus();
    }
  }, [selected, data]);
  const select = useCallback((id: string) => {
    setSelected(id);
    history.pushState(
      null,
      "",
      `${location.pathname}${location.search}#${encodeURIComponent(id)}`,
    );
  }, []);
  const close = () => {
    setSelected(null);
    history.replaceState(null, "", location.pathname + location.search);
  };
  const changeScope = (id: string) => {
    close();
    setInspected(null);
    setHighlighted(null);
    setScope(id);
    const url = new URL(location.href);
    url.searchParams.set("collection", id);
    url.hash = "";
    history.pushState(null, "", url);
  };
  const all = useMemo(
    () => (data ? [...entriesOf(data), ...lifecycleEvents(data)] : []),
    [data],
  );
  const byId = useMemo(() => new Map(all.map((e) => [e.id, e])), [all]);
  const entry = byId.get(selected || "");
  const events = useMemo(
    () =>
      data?.events.filter(
        (e) =>
          matches(e, query) &&
          (!entityFilter ||
            e.people?.includes(entityFilter) ||
            e.organizations?.includes(entityFilter)) &&
          (!range ||
            (Number(e.date!.slice(0, 4)) <= range[1] &&
              Number((e.endDate || e.date!).slice(0, 4)) >= range[0])),
      ) || [],
    [data, query, range, entityFilter],
  );
  const sharedEntities = useMemo(() => {
    if (!data || selectedSourcesForScope(scope).length < 2) return [];
    const sourceIds = selectedSourcesForScope(scope);
    return [...data.people, ...data.organizations]
      .filter(
        (e) =>
          sourceIds.filter((id) => e.citations.some((c) => c.sourceId === id))
            .length > 1,
      )
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [data, scope]);
  const diagram = useMemo(() => {
    if (!data || !entityMode) return data;
    const lifecycle = lifecycleEvents(data).filter(
      (event) =>
        matches(event, query) &&
        (!range ||
          (Number(event.date!.slice(0, 4)) <= range[1] &&
            Number((event.endDate || event.date!).slice(0, 4)) >= range[0])),
    );
    return entityProjection(
      data,
      entityTracks,
      [...events, ...lifecycle],
      selectedSourcesForScope(scope),
    );
  }, [data, entityMode, entityTracks, events, query, range, scope]);
  const diagramActive = useMemo(
    () => (entityMode ? diagram?.lanes.map((lane) => lane.id) || [] : active),
    [entityMode, diagram, active],
  );
  const plottedEvents = useMemo(
    () =>
      (diagram?.events || [])
        .filter((event) =>
          event.lanes?.some((id) => diagramActive.includes(id)),
        )
        .sort((a, b) => a.date!.localeCompare(b.date!)),
    [diagram, diagramActive],
  );
  const viewEntityTimeline = (id: string) => {
    close();
    setInspected(null);
    setEntityMode(true);
    setEntityTracks([id]);
    setView("Timelines");
    setEntityFilter("");
    setQuery("");
    setRange(null);
    const url = new URL(location.href);
    url.searchParams.set("tracks", id);
    history.replaceState(null, "", url);
    document
      .querySelector(".workspace")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  useEffect(() => {
    const url = new URL(location.href);
    if (entityMode && entityTracks.length)
      url.searchParams.set("tracks", entityTracks.join(","));
    else url.searchParams.delete("tracks");
    history.replaceState(null, "", url);
  }, [entityMode, entityTracks]);
  const records = useMemo(() => {
    const rows =
      view === "Characters"
        ? data?.people
        : view === "Organizations"
          ? data?.organizations
          : events;
    return (rows || [])
      .filter(
        (e) =>
          matches(e, query) &&
          (evidenceFilter === "all" ||
            (evidenceFilter === "tentative" && !!e.roster) ||
            (evidenceFilter === "bracketed" && !!e.roster?.bracketed) ||
            (evidenceFilter === "role" && !e.roster?.bracketed)),
      )
      .sort((a, b) =>
        view === "Events"
          ? a.date!.localeCompare(b.date!)
          : sort === "connections"
            ? data!.relationships.filter(
                (r) => r.fromId === b.id || r.toId === b.id,
              ).length -
              data!.relationships.filter(
                (r) => r.fromId === a.id || r.toId === a.id,
              ).length
            : a.name.localeCompare(b.name),
      );
  }, [data, view, events, query, evidenceFilter, sort]);
  const connectionRows = useMemo(
    () =>
      data?.relationships.filter(
        (r) =>
          (!focus || r.fromId === focus || r.toId === focus) &&
          (includeInferred ||
            !(
              /tentative|conjecture|interpretation|allegation|hypothesis|contested|claim/i.test(
                r.evidence || "",
              ) || r.toId === "milner-group"
            )) &&
          `${byId.get(r.fromId)?.name} ${byId.get(r.toId)?.name} ${r.label} ${r.evidence}`
            .toLowerCase()
            .includes(query.toLowerCase()),
      ) || [],
    [data, focus, includeInferred, query, byId],
  );
  const selectedSources = useMemo(
    () =>
      scope === "all" ? catalog.sources.map((s) => s.id) : scope.split(","),
    [scope],
  );
  const source = catalog.sources.find((s) => s.id === scope);
  const toggleSource = (id: string) => {
    const next = selectedSources.includes(id)
      ? selectedSources.filter((s) => s !== id)
      : [...selectedSources, id];
    if (next.length)
      changeScope(
        next.length === catalog.sources.length
          ? "all"
          : catalog.sources
              .filter((s) => next.includes(s.id))
              .map((s) => s.id)
              .join(","),
      );
  };
  const counts = data
    ? {
        people: data.people.length,
        events: data.events.length,
        organizations: data.organizations.length,
        relationships: data.relationships.length,
        lanes: data.lanes.length,
      }
    : selectedSources.reduce(
        (sum, id) => {
          const c = catalog.counts[id];
          return {
            people: sum.people + c.people,
            events: sum.events + c.events,
            organizations: sum.organizations + c.organizations,
            relationships: sum.relationships + c.relationships,
            lanes: sum.lanes + c.lanes,
          };
        },
        { people: 0, events: 0, organizations: 0, relationships: 0, lanes: 0 },
      );
  const nav = [
    ["Timelines", Clock],
    ["Characters", Users],
    ["Events", Network],
    ["Organizations", Building2],
    ["Connections", GitBranch],
    ["Sources", BookOpen],
  ] as const;
  const link = (id: string, label?: string) => {
    const e = byId.get(id);
    return e ? (
      <button
        className="entity-link"
        key={id + label}
        onClick={() => select(id)}
      >
        {label || e.name}
        <ArrowUpRight size={13} />
      </button>
    ) : null;
  };
  const exportData = async () => {
    const complete = await loadFullArchive();
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(complete, null, 2)], {
        type: "application/json",
      }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "dark-time-archive.json";
    a.click();
    URL.revokeObjectURL(url);
  };
  const openGraph = (id: string) => {
    close();
    setFocus(id);
    setView("Connections");
    setQuery("");
  };
  return (
    <div
      className={`shell ${inspected && view === "Timelines" ? "inspector-open" : ""}`}
    >
      <aside className={menu ? "sidebar open" : "sidebar"}>
        <a
          className="brand"
          href={location.pathname}
          onClick={(e) => {
            e.preventDefault();
            setView("Timelines");
            close();
          }}
        >
          <span className="brand-mark">
            D<span>∕</span>T
          </span>
          <span>
            DARK TIME<small>A LIVING HISTORICAL ATLAS</small>
          </span>
        </a>
        <div className="nav-label">THE ARCHIVE</div>
        <nav aria-label="Archive sections">
          {nav.map(([n, Icon]) => (
            <button
              className={view === n ? "active" : ""}
              aria-current={view === n ? "page" : undefined}
              key={n}
              onClick={() => {
                setView(n);
                setMenu(false);
              }}
            >
              <Icon size={17} />
              {n}
              <span>
                {n === "Characters"
                  ? counts.people
                  : n === "Events"
                    ? counts.events
                    : n === "Organizations"
                      ? counts.organizations
                      : n === "Connections"
                        ? counts.relationships
                        : n === "Sources"
                          ? catalog.sources.length
                          : counts.lanes}
              </span>
            </button>
          ))}
        </nav>
        <details className="sidebar-note">
          <summary>Collections</summary>
          <span className="tiny-label">
            COLLECTIONS / {catalog.sources.length}
          </span>
          <div className="collection-nav">
            <button
              className={scope === "all" ? "chosen" : ""}
              onClick={() => changeScope("all")}
            >
              All collections <span>{catalog.counts.all.events}</span>
            </button>
            {catalog.sources.map((s) => (
              <button
                className={scope === s.id ? "chosen" : ""}
                key={s.id}
                onClick={() => changeScope(s.id)}
              >
                {s.title}
                <span>{catalog.counts[s.id].events}</span>
              </button>
            ))}
          </div>
          <p>
            Each collection keeps its own provenance. Connections require a
            cited relationship.
          </p>
        </details>
        <footer>
          <span className="live-dot" /> An evolving record
          <small>LAST UPDATED · OCT 14, 2026</small>
        </footer>
      </aside>
      <main>
        <header>
          <button
            className="mobile-menu"
            aria-label="Open navigation"
            onClick={() => setMenu(!menu)}
          >
            <Menu />
          </button>
          <span>
            ARCHIVE / <b>{view.toUpperCase()}</b>
          </span>
          <button onClick={() => void exportData()}>
            <Download size={14} /> Export all collections
          </button>
        </header>
        <section className="intro">
          <div className="eyebrow">
            <span /> FOLLOW THE THREADS
          </div>
          <div className="intro-title">
            <h1>
              {view === "Timelines"
                ? "History doesn’t happen\nin a straight line."
                : view === "Characters"
                  ? "The people in the narrative."
                  : view === "Events"
                    ? "An inventory of moments."
                    : view === "Organizations"
                      ? "The structures of influence."
                      : view === "Connections"
                        ? "Follow the connections."
                        : "Every thread starts somewhere."}
            </h1>
            <span className="edition">
              DARK TIME
              <br />
              AN EXPANDING COLLECTION
            </span>
          </div>
          <p className="lead">
            {view === "Timelines"
              ? "Trace the people, institutions, and events within each source. Zoom into a moment, follow a shared thread, and examine the evidence."
              : view === "Connections"
                ? "Explore cited affiliations, professional roles, family relationships, and the interpretations connecting them."
                : view === "Sources"
                  ? "What we read, what it says, and what remains unresolved."
                  : "Search by name, title, alias, or description. Open a record to follow its affiliations and source-specific accounts."}
          </p>
        </section>
        <div className="collection-bar">
          <div>
            <span className="tiny-label">CURRENT COLLECTION</span>
            <strong>
              {scope === "all"
                ? "All collections"
                : source?.title || `${selectedSources.length} selected sources`}
            </strong>
          </div>
          <select
            aria-label="Select collection"
            value={scope}
            onChange={(e) => changeScope(e.target.value)}
          >
            <option value="all">All collections</option>
            {scope.includes(",") && (
              <option value={scope}>
                {selectedSources.length} selected sources
              </option>
            )}
            {catalog.sources.map((s) => (
              <option key={s.id} value={s.id}>
                {s.title}
              </option>
            ))}
          </select>
        </div>
        <div className="stats">
          {[
            [counts.people, "CHARACTERS"],
            [counts.events, "EVENTS"],
            [counts.organizations, "ORGANIZATIONS"],
            [counts.relationships, "CONNECTIONS"],
          ].map(([n, l]) => (
            <div key={l}>
              <strong>{String(n).padStart(2, "0")}</strong>
              <span>{l}</span>
            </div>
          ))}
        </div>
        {!data ? (
          <div className="loading" role="status">
            {error || "Opening the collection…"}
          </div>
        ) : (
          <section className="workspace">
            <div className="section-heading">
              <div>
                <span className="tiny-label">
                  {view === "Timelines"
                    ? "THE CONNECTED CHRONOLOGY"
                    : "EXPLORE THE COLLECTION"}
                </span>
                <h2>
                  {view === "Timelines" ? "Intersecting timelines" : view}
                </h2>
              </div>
              <label className="search">
                <Search size={16} />
                <input
                  aria-label="Search archive"
                  placeholder={
                    view === "Connections"
                      ? "Search connections…"
                      : "Names, aliases, descriptions…"
                  }
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                {query && (
                  <button
                    aria-label="Clear search"
                    onClick={() => setQuery("")}
                  >
                    <X size={14} />
                  </button>
                )}
              </label>
            </div>
            {view === "Timelines" ? (
              <>
                <div className="entity-timeline-controls">
                  <div
                    className="timeline-mode"
                    role="group"
                    aria-label="Timeline display"
                  >
                    <button
                      aria-pressed={!entityMode}
                      onClick={() => setEntityMode(false)}
                    >
                      Topic timelines
                    </button>
                    <button
                      aria-pressed={entityMode}
                      onClick={() => {
                        setEntityMode(true);
                        setEntityFilter("");
                        setQuery("");
                      }}
                    >
                      People & organization timelines
                    </button>
                  </div>
                  {entityMode && (
                    <>
                      <p className="view-note">
                        Choose people or organizations from the selected sources
                        to compare on aligned tracks. Birth, death and lifecycle
                        changes appear where cited; the first and last dated
                        references do not imply a lifespan.
                      </p>
                      <div className="entity-track-picker">
                        <label>
                          Add a person or organization
                          <select
                            aria-label="Add timeline entity"
                            value={trackToAdd}
                            onChange={(event) =>
                              setTrackToAdd(event.target.value)
                            }
                          >
                            <option value="">Choose a record…</option>
                            {all
                              .filter(
                                (record) =>
                                  record.kind !== "event" &&
                                  !entityTracks.includes(record.id),
                              )
                              .sort((a, b) => a.name.localeCompare(b.name))
                              .map((record) => (
                                <option key={record.id} value={record.id}>
                                  {record.name} · {record.kind}
                                </option>
                              ))}
                          </select>
                        </label>
                        <button
                          disabled={!trackToAdd}
                          onClick={() => {
                            setEntityTracks((previous) => [
                              ...previous,
                              trackToAdd,
                            ]);
                            setTrackToAdd("");
                          }}
                        >
                          Add timeline
                        </button>
                        {!!entityTracks.length && (
                          <button onClick={() => setEntityTracks([])}>
                            Clear tracks
                          </button>
                        )}
                      </div>
                      <div className="entity-track-chips">
                        {entityTracks.map((id) => (
                          <span key={id}>
                            {byId.get(id)?.name || id}
                            <button
                              aria-label={`Remove ${byId.get(id)?.name || id} timeline`}
                              onClick={() =>
                                setEntityTracks((previous) =>
                                  previous.filter((track) => track !== id),
                                )
                              }
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                    </>
                  )}
                </div>
                <div className="view-tools">
                  <label>
                    Period
                    <select
                      aria-label="Timeline period"
                      value={range ? range.join("-") : "all"}
                      onChange={(e) =>
                        setRange(
                          e.target.value === "all"
                            ? null
                            : (e.target.value.split("-").map(Number) as [
                                number,
                                number,
                              ]),
                        )
                      }
                    >
                      <option value="all">Full chronology</option>
                      <option value="1875-1914">1875–1914 · Origins</option>
                      <option value="1914-1919">1914–1919 · War & peace</option>
                      <option value="1919-1939">1919–1939 · Interwar</option>
                      <option value="1939-1949">
                        1939–1949 · War & reconstruction
                      </option>
                      <option value="1967-1972">
                        1967–1972 · Political upheaval
                      </option>
                      <option value="1950-1979">1950–1979 · Cold War</option>
                      <option value="1980-2014">
                        1980–2014 · Later networks
                      </option>
                    </select>
                  </label>
                  {!entityMode && (
                    <label>
                      Participant
                      <select
                        aria-label="Timeline participant"
                        value={entityFilter}
                        onChange={(e) => setEntityFilter(e.target.value)}
                      >
                        <option value="">All people & organizations</option>
                        {[...data.people, ...data.organizations]
                          .sort((a, b) => a.name.localeCompare(b.name))
                          .map((e) => (
                            <option key={e.id} value={e.id}>
                              {e.name}
                            </option>
                          ))}
                      </select>
                    </label>
                  )}
                  <span className="result-count">
                    {entityMode ? diagram?.events.length : events.length}{" "}
                    matching events
                  </span>
                </div>
                {selectedSources.length > 1 && !entityMode && (
                  <div className="overlay-options">
                    <label>
                      <input
                        type="checkbox"
                        checked={overlayLinks}
                        onChange={(e) => setOverlayLinks(e.target.checked)}
                      />{" "}
                      Show shared participants & source-claimed influence
                    </label>
                    <p>
                      Dashed arcs link shared participants across sources. Solid
                      arrows show influence claimed in a cited source; neither
                      is independent confirmation.
                    </p>
                    {sharedEntities.length > 0 ? (
                      <div className="shared-entities">
                        <span>Shared entities:</span>
                        {sharedEntities.slice(0, 16).map((e) => (
                          <button
                            key={e.id}
                            onClick={() => setEntityFilter(e.id)}
                          >
                            {e.name}
                          </button>
                        ))}
                        {sharedEntities.length > 16 && (
                          <button onClick={() => setView("Connections")}>
                            +{sharedEntities.length - 16} more
                          </button>
                        )}
                      </div>
                    ) : (
                      <p>
                        No cited shared identities in this selection. Timelines
                        are overlaid without inventing a connection.
                      </p>
                    )}
                  </div>
                )}
                <div className="timeline-selection-bar">
                  <details className="source-picker" open>
                    <summary>
                      Sources to overlay · {selectedSources.length} selected
                    </summary>
                    <fieldset className="source-selection">
                      <legend>Choose sources to overlay</legend>
                      {catalog.sources.map((s) => (
                        <label key={s.id}>
                          <input
                            type="checkbox"
                            aria-label={`Include ${s.title}`}
                            checked={selectedSources.includes(s.id)}
                            disabled={
                              selectedSources.length === 1 &&
                              selectedSources.includes(s.id)
                            }
                            onChange={() => toggleSource(s.id)}
                          />
                          <span>
                            {s.author === "Carroll Quigley"
                              ? `Quigley · ${s.shortTitle || s.title}`
                              : s.author === "Peter Dale Scott"
                                ? "Peter Dale Scott"
                                : "Carl Oglesby"}
                            <small>
                              {s.author === "Carroll Quigley"
                                ? "Historical study"
                                : s.id === "scott"
                                  ? "Political analysis"
                                  : "Interpretive account"}
                            </small>
                          </span>
                        </label>
                      ))}
                    </fieldset>
                  </details>
                  {highlighted && byId.get(highlighted) && (
                    <div className="selected-event-strip" aria-live="polite">
                      <strong>{byId.get(highlighted)!.name}</strong>
                      <span>Highlighted across threads</span>
                      <button
                        className="show-event-details"
                        onClick={() => setInspected(highlighted)}
                      >
                        <BookOpen size={16} /> Show details
                      </button>
                      <button onClick={() => setHighlighted(null)}>
                        Clear highlight
                      </button>
                    </div>
                  )}
                </div>
                {!entityMode && (
                  <details className="thread-controls">
                    <summary>
                      Timeline threads · {active.length} visible
                    </summary>
                    <div className="thread-heading">
                      <span className="tiny-label">
                        {active.length} / {data.lanes.length} THREADS VISIBLE
                      </span>
                      <div>
                        <button
                          onClick={() => setActive(data.lanes.map((l) => l.id))}
                        >
                          Show all
                        </button>
                        <button onClick={() => setActive([])}>Hide all</button>
                      </div>
                    </div>
                    <div className="thread-filters">
                      {data.lanes.map((l) => (
                        <button
                          key={l.id}
                          aria-pressed={active.includes(l.id)}
                          className={active.includes(l.id) ? "selected" : ""}
                          onClick={() =>
                            setActive(
                              active.includes(l.id)
                                ? active.filter((i) => i !== l.id)
                                : [...active, l.id],
                            )
                          }
                        >
                          <span style={{ background: l.color }} />
                          {l.name}
                        </button>
                      ))}
                    </div>
                  </details>
                )}
                {!diagramActive.length ? (
                  <div className="empty">
                    {entityMode
                      ? "Choose a person or organization to start its timeline."
                      : "Select a timeline thread to start exploring."}
                  </div>
                ) : (
                  <div className="timeline-layout">
                    <div className="lane-labels">
                      {diagram!.lanes
                        .filter((l) => diagramActive.includes(l.id))
                        .map((l) => (
                          <div key={l.id} style={{ color: l.color }}>
                            {l.name}
                            {entityMode && (
                              <small>
                                {byId.get(l.id.slice(7))?.kind === "person"
                                  ? (
                                      byId.get(l.id.slice(7))?.milestones || []
                                    ).some(
                                      (m) =>
                                        (m.kind === "birth" ||
                                          m.kind === "death") &&
                                        m.citations.some((c) =>
                                          selectedSources.includes(c.sourceId),
                                        ),
                                    )
                                    ? "Cited lifespan & events"
                                    : "Lifespan dates not yet recorded"
                                  : "Cited institutional record"}
                              </small>
                            )}
                            <small>
                              {l.sourceIds
                                ?.map(
                                  (id) =>
                                    catalog.sources.find(
                                      (source) => source.id === id,
                                    )?.shortTitle || "Source",
                                )
                                .join(" / ")}{" "}
                              ·{" "}
                              {
                                diagram!.events.filter((e) =>
                                  e.lanes?.includes(l.id),
                                ).length
                              }{" "}
                              EVENTS
                            </small>
                          </div>
                        ))}
                    </div>
                    <div className="timeline">
                      <Suspense
                        fallback={
                          <div className="loading">Loading timeline…</div>
                        }
                      >
                        <Timeline
                          data={diagram!}
                          events={diagram!.events}
                          active={diagramActive}
                          onSelect={highlight}
                          highlightedId={highlighted}
                          range={range}
                          overlayLinks={overlayLinks}
                          sourceIds={selectedSources}
                        />
                      </Suspense>
                    </div>
                  </div>
                )}
                <div className="below-chart">
                  <span>
                    {diagram!.events
                      .map((e) => e.date!.slice(0, 4))
                      .sort()[0] || "No dated record"}{" "}
                    —{" "}
                    {diagram!.events
                      .map((e) => (e.endDate || e.date!).slice(0, 4))
                      .sort()
                      .at(-1)}
                  </span>
                  <p>
                    Connectors identify the same event across threads, not
                    causation. Year and month dates show their precision as
                    bars; January 1 marks an unknown day within a year.
                  </p>
                </div>
                {!events.length && (
                  <p className="empty">
                    No events match these filters. Choose another period or
                    participant.
                  </p>
                )}
                <details className="event-list-fold">
                  <summary>Event list · {plottedEvents.length} events</summary>
                  <div className="section-heading recent-heading">
                    <h2>Events on these threads</h2>
                    <button
                      className="text-button"
                      onClick={() => setView("Events")}
                    >
                      Open event inventory <ArrowUpRight size={14} />
                    </button>
                  </div>
                  <p className="view-note">
                    Numbered markers match this list. Hover or focus a marker
                    for its full title, date and source summary; click to
                    highlight its connections and read the complete account in
                    the details panel.
                  </p>
                  <Pager
                    page={timelinePage}
                    total={plottedEvents.length}
                    onChange={setTimelinePage}
                  />
                  <div className="timeline-event-list">
                    {plottedEvents
                      .slice(
                        timelinePage * PAGE_SIZE,
                        (timelinePage + 1) * PAGE_SIZE,
                      )
                      .map((e, i) => (
                        <button
                          className="timeline-event-row"
                          key={e.id}
                          onClick={() => select(e.id)}
                        >
                          <span className="event-number">
                            {timelinePage * PAGE_SIZE + i + 1}
                          </span>
                          <div>
                            <span className="tiny-label">
                              {dateLabel(e)} · {e.precision}
                            </span>
                            <h3>{e.name}</h3>
                            <p>{labelFor(e, scope)}</p>
                            <span className="event-thread-names">
                              {e
                                .lanes!.filter((id) =>
                                  diagramActive.includes(id),
                                )
                                .map(
                                  (id) =>
                                    diagram!.lanes.find((l) => l.id === id)
                                      ?.name,
                                )
                                .join(" · ")}
                            </span>
                          </div>
                          <ArrowUpRight size={16} />
                        </button>
                      ))}
                  </div>
                  <Pager
                    page={timelinePage}
                    total={plottedEvents.length}
                    onChange={setTimelinePage}
                  />
                </details>
              </>
            ) : view === "Connections" ? (
              <>
                <div className="view-tools">
                  <label>
                    Focus
                    <select
                      aria-label="Connection focus"
                      value={focus}
                      onChange={(e) => setFocus(e.target.value)}
                    >
                      <option value="">Core network overview</option>
                      {[...data.people, ...data.organizations]
                        .sort((a, b) => a.name.localeCompare(b.name))
                        .map((e) => (
                          <option key={e.id} value={e.id}>
                            {e.name}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={includeInferred}
                      onChange={(e) => setIncludeInferred(e.target.checked)}
                    />{" "}
                    Include author-inferred / tentative connections
                  </label>
                  {focus && (
                    <button
                      className="text-button"
                      onClick={() => setFocus("")}
                    >
                      Clear focus
                    </button>
                  )}
                </div>
                <p className="view-note">
                  {focus
                    ? "The diagram shows this entity’s neighborhood. Click a node for details, then use “Explore connections” to move your focus."
                    : "The overview starts with 65 highly connected entities. Choose a focus for a readable neighborhood, or expand the graph."}{" "}
                  Search filters the cited relationship list below.
                </p>
                <Suspense
                  fallback={<div className="loading">Loading connections…</div>}
                >
                  <Connections
                    data={data}
                    focus={focus}
                    onSelect={select}
                    includeInferred={includeInferred}
                  />
                </Suspense>
                <h2 className="relation-list-title">
                  Cited relationship inventory
                </h2>
                <Pager
                  page={connectionPage}
                  total={connectionRows.length}
                  onChange={setConnectionPage}
                />
                <div className="relationship-list">
                  {connectionRows
                    .slice(
                      connectionPage * PAGE_SIZE,
                      (connectionPage + 1) * PAGE_SIZE,
                    )
                    .map((r) => (
                      <article className="relationship-row" key={r.id}>
                        <div className="relationship-endpoints">
                          {link(r.fromId)}
                          <span>→</span>
                          {link(r.toId)}
                        </div>
                        <p>{r.label}</p>
                        {r.description && (
                          <p className="relationship-summary">
                            {r.description}
                          </p>
                        )}
                        <small>
                          {r.evidence || "Source account"} ·{" "}
                          {r.citations
                            .map(
                              (c) =>
                                `${catalog.sources.find((s) => s.id === c.sourceId)?.title}: pp. ${c.pages.join(", ")}`,
                            )
                            .join(" · ")}
                        </small>
                      </article>
                    ))}
                </div>
                {!connectionRows.length && (
                  <p className="empty">
                    No cited relationships match these filters.
                  </p>
                )}
                <Pager
                  page={connectionPage}
                  total={connectionRows.length}
                  onChange={setConnectionPage}
                />
              </>
            ) : view === "Sources" ? (
              <>
                <p className="view-note">
                  All source records are listed here regardless of the selected
                  collection. PDF citations use file page numbers. The original
                  PDFs remain local research files.
                </p>
                {catalog.sources
                  .filter((s) =>
                    `${s.title} ${s.author || ""} ${s.description}`
                      .toLowerCase()
                      .includes(query.toLowerCase()),
                  )
                  .map((s, i) => (
                    <article className="source-card" key={s.id}>
                      <span className="tiny-label">
                        SOURCE {String(i + 1).padStart(3, "0")} · PDF DOCUMENT
                      </span>
                      <h2>{s.title}</h2>
                      {s.author && (
                        <p className="source-byline">
                          {s.author} · {s.published}
                          {s.written && ` · manuscript ${s.written}`} ·{" "}
                          {s.pageCount} PDF pages
                        </p>
                      )}
                      <p>{s.description}</p>
                      {s.localPath && (
                        <p>
                          <code>{s.localPath}</code>
                        </p>
                      )}
                      <p>{s.coverage}</p>
                      <p>
                        {s.pageConvention ||
                          "Page numbers refer to 1-based PDF file pages."}{" "}
                        Accessed {s.accessed}.
                      </p>
                      <div className="source-counts">
                        {catalog.counts[s.id].people} people ·{" "}
                        {catalog.counts[s.id].organizations} organizations ·{" "}
                        {catalog.counts[s.id].events} events ·{" "}
                        {catalog.counts[s.id].relationships} connections
                      </div>
                      <button
                        className="source-action"
                        onClick={() => {
                          changeScope(s.id);
                          setView("Timelines");
                        }}
                      >
                        Explore this collection <ArrowUpRight size={14} />
                      </button>
                      {s.evidenceIssues && (
                        <details>
                          <summary>
                            Source qualifications & conflicting accounts
                          </summary>
                          <div className="chapter-map">
                            {s.evidenceIssues.map((issue, i) => (
                              <div key={i}>
                                <span>{issue.description}</span>
                                <b>PDF {issue.pages.join(", ")}</b>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                      {s.chapters && (
                        <details>
                          <summary>Chapter coverage & PDF-page map</summary>
                          <div className="chapter-map">
                            {s.chapters.map((c) => (
                              <div key={c.title}>
                                <span>{c.title}</span>
                                <b>
                                  {c.pdfStart}–{c.pdfEnd}
                                </b>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </article>
                  ))}
                <article className="source-card">
                  <h2>A record that can change</h2>
                  <p>
                    Documented appointments, author interpretations, tentative
                    membership and bracketed conjectures have different
                    evidential weight. A shared surname, institution or theme
                    does not establish a cross-source connection.
                  </p>
                  <p>
                    Later materials can add source-specific accounts and
                    citations to stable identities. Dated revision histories
                    remain visible. The full archive can be exported as JSON.
                  </p>
                </article>
              </>
            ) : (
              <>
                <div className="view-tools">
                  {view !== "Events" && (
                    <>
                      <label>
                        Sort
                        <select
                          aria-label="Sort records"
                          value={sort}
                          onChange={(e) => setSort(e.target.value)}
                        >
                          <option value="name">Alphabetical</option>
                          <option value="connections">Most connected</option>
                        </select>
                      </label>
                      <label>
                        Evidence
                        <select
                          aria-label="Filter record evidence"
                          value={evidenceFilter}
                          onChange={(e) => setEvidenceFilter(e.target.value)}
                        >
                          <option value="all">All records</option>
                          <option value="tentative">
                            Quigley roster entries
                          </option>
                          <option value="bracketed">
                            Bracketed conjectures
                          </option>
                          <option value="role">
                            Without bracketed conjectures
                          </option>
                        </select>
                      </label>
                    </>
                  )}
                  <span className="result-count">
                    {records.length} matching records
                  </span>
                </div>
                <Pager page={page} total={records.length} onChange={setPage} />
                <div className={view === "Events" ? "event-list" : "directory"}>
                  {records
                    .slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
                    .map((e, i) => (
                      <button
                        className="record"
                        key={e.id}
                        onClick={() => select(e.id)}
                      >
                        <span className="record-index">
                          {String(page * PAGE_SIZE + i + 1).padStart(2, "0")}
                        </span>
                        <div>
                          <span className="tiny-label">
                            {e.kind === "event"
                              ? `${dateLabel(e)} · ${e.precision}`
                              : e.role}
                          </span>
                          <h3>{e.name}</h3>
                          <p>{labelFor(e, scope)}</p>
                          {e.roster?.bracketed && (
                            <span className="record-badge">
                              BRACKETED CONJECTURE
                            </span>
                          )}
                        </div>
                        <ArrowUpRight size={18} />
                      </button>
                    ))}
                </div>
                {!records.length && (
                  <p className="empty">
                    No matching records. Try a name, title, alias, or another
                    collection.
                  </p>
                )}
                <Pager
                  page={page}
                  total={records.length}
                  onChange={(p) => {
                    setPage(p);
                    document
                      .querySelector(".workspace")
                      ?.scrollIntoView({ behavior: "smooth", block: "start" });
                  }}
                />
              </>
            )}
          </section>
        )}
        <div className="provenance">
          <BookOpen size={16} />
          <p>
            <b>Attribution travels with every connection.</b> This atlas
            distinguishes source accounts and interpretations from independently
            corroborated facts. Bibliographic citations show where a claim
            appears.
          </p>
          <button onClick={() => setView("Sources")}>
            Source notes <ArrowUpRight size={14} />
          </button>
        </div>
        <div className="main-footer">
          DARK TIME <span>A living archive. An open investigation.</span>
        </div>
      </main>
      {inspected && data && view === "Timelines" && byId.get(inspected) && (
        <Suspense
          fallback={
            <div className="timeline-inspector">Loading event details…</div>
          }
        >
          <TimelineInspector
            data={data}
            entry={byId.get(inspected)!}
            onTimeline={viewEntityTimeline}
            onClose={() => setInspected(null)}
            onExplore={(id) => {
              setInspected(id);
              if (byId.get(id)?.kind === "event") setHighlighted(id);
            }}
          />
        </Suspense>
      )}
      {selected && data && (
        <div className="overlay" onClick={close}>
          <section
            ref={detailRef}
            className="detail"
            role="dialog"
            aria-modal="true"
            aria-label={entry?.name || "Record not found"}
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => {
              if (e.key === "Tab") {
                const elements = Array.from(
                  e.currentTarget.querySelectorAll<HTMLElement>(
                    "button,a,summary",
                  ),
                ).filter((el) => el.offsetParent !== null);
                const first = elements[0],
                  last = elements.at(-1);
                if (e.shiftKey && document.activeElement === first) {
                  e.preventDefault();
                  last?.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                  e.preventDefault();
                  first?.focus();
                }
              }
            }}
          >
            <button
              autoFocus
              className="close"
              aria-label="Close details"
              onClick={close}
            >
              <X />
            </button>
            {!entry ? (
              <>
                <h2>Record not found</h2>
                <p>This record is not in the current collection.</p>
                <button
                  className="entity-link"
                  onClick={() => changeScope("all")}
                >
                  Open all collections
                </button>
              </>
            ) : (
              <>
                <span className="tiny-label">
                  {entry.kind.toUpperCase()} / {entry.id}
                </span>
                <h2>{entry.name}</h2>
                <span className="detail-role">
                  {entry.kind === "event" ? dateLabel(entry) : entry.role}
                  {entry.precision && ` · ${entry.precision} precision`}
                </span>
                {entry.aliases?.length ? (
                  <p className="aliases">
                    Also known as: {entry.aliases.join(" · ")}
                  </p>
                ) : null}
                <p className="detail-description">{labelFor(entry, scope)}</p>
                {entry.kind === "event" && (
                  <Suspense
                    fallback={
                      <p className="view-note">Loading source account…</p>
                    }
                  >
                    <EventNarrative entry={entry} />
                  </Suspense>
                )}
                {entry.kind === "event" &&
                  data.eventLinks?.some(
                    (l) => l.fromId === entry.id || l.toId === entry.id,
                  ) && (
                    <section className="event-influences">
                      <h4>Influence described in the source</h4>
                      {data.eventLinks
                        .filter(
                          (l) => l.fromId === entry.id || l.toId === entry.id,
                        )
                        .map((l) => (
                          <div className="relation" key={l.id}>
                            <p>{l.label}</p>
                            <small>
                              {l.citations
                                .map(
                                  (c) =>
                                    `${catalog.sources.find((s) => s.id === c.sourceId)?.author || "Source"}, pp. ${c.pages.join(", ")}`,
                                )
                                .join(" · ")}
                            </small>
                            {link(l.fromId === entry.id ? l.toId : l.fromId)}
                          </div>
                        ))}
                    </section>
                  )}
                <div className="claim-label compact-evidence">
                  {entry.evidence ||
                    entry.status ||
                    "Source account · independent verification pending"}
                </div>
                {entry.kind !== "event" && (
                  <button
                    className="explore-connections"
                    onClick={() => viewEntityTimeline(entry.id)}
                  >
                    <Clock size={16} /> View timeline <ArrowUpRight size={14} />
                  </button>
                )}
                {entry.kind !== "event" && (
                  <button
                    className="explore-connections"
                    onClick={() => openGraph(entry.id)}
                  >
                    <GitBranch size={16} /> Explore connections{" "}
                    <ArrowUpRight size={14} />
                  </button>
                )}
                {entry.roster && (
                  <div className="roster-note">
                    <h4>Quigley’s tentative classification</h4>
                    <p>{entry.roster.sections.join(" · ")}</p>
                    <small>
                      {entry.roster.bracketed
                        ? "Bracketed in the appendix: the author says he lacked convincing evidence."
                        : "The appendix warns that this roster is incomplete and may assign individuals to the wrong circle."}
                    </small>
                  </div>
                )}
                {entry.kind === "organization" && (
                  <>
                    <h4>Founders / founding roles</h4>
                    <p>{entry.founders}</p>
                    <div className="links">
                      {entry.founderIds?.map((id) => link(id))}
                    </div>
                    <h4>Members / associates recorded in the archive</h4>
                    <p className="view-note">
                      Listed association may denote employment, governance,
                      authorship or cooperation. It may come from another
                      collection; source-specific links appear below.
                    </p>
                    <div className="links">
                      {entry.members?.length ? (
                        entry.members.map((id) => link(id))
                      ) : (
                        <p>Not established by the supplied source.</p>
                      )}
                    </div>
                  </>
                )}
                <h4>
                  {entry.kind === "event"
                    ? "Participants & organizations"
                    : "Connections & affiliations"}
                </h4>
                <div className="links">
                  {entry.kind === "event"
                    ? [...entry.people!, ...entry.organizations!].map((id) =>
                        link(id),
                      )
                    : data.relationships
                        .filter(
                          (r) => r.fromId === entry.id || r.toId === entry.id,
                        )
                        .map((r) => (
                          <div className="relation" key={r.id}>
                            <small>
                              {r.label}
                              <br />
                              {r.evidence || "Source account"} ·{" "}
                              {r.citations
                                .map(
                                  (c) =>
                                    `${catalog.sources.find((s) => s.id === c.sourceId)?.author || c.sourceId}, pp. ${c.pages.join(", ")}`,
                                )
                                .join(" · ")}
                            </small>
                            {link(r.fromId === entry.id ? r.toId : r.fromId)}
                          </div>
                        ))}
                </div>
                {entry.kind !== "event" && (
                  <>
                    <h4>Related events</h4>
                    <div className="links">
                      {data.events
                        .filter((e) =>
                          [...e.people!, ...e.organizations!].includes(
                            entry.id,
                          ),
                        )
                        .sort((a, b) => a.date!.localeCompare(b.date!))
                        .map((e) => link(e.id, `${dateLabel(e)} · ${e.name}`))}
                    </div>
                  </>
                )}
                {entry.accounts && entry.accounts.length > 1 && (
                  <>
                    <h4>Accounts across sources</h4>
                    {entry.accounts.map((a) => (
                      <article className="source-account" key={a.sourceId}>
                        <span className="tiny-label">
                          {
                            catalog.sources.find((s) => s.id === a.sourceId)
                              ?.title
                          }
                        </span>
                        <p>{a.description}</p>
                      </article>
                    ))}
                  </>
                )}
                <h4>Source references</h4>
                <CitationList
                  citations={entry.citations}
                  sources={catalog.sources}
                />
                <h4>Description history</h4>
                {entry.history.map((h, i) => (
                  <p className="history" key={`${h.date}-${i}`}>
                    <b>{h.date}</b>
                    <br />
                    {h.note}
                  </p>
                ))}
                <button
                  className="entity-link"
                  onClick={() => {
                    void navigator.clipboard?.writeText(location.href);
                  }}
                >
                  <LinkIcon size={14} /> Copy record link
                </button>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
export { App };
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
