import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import type { Archive, Entry } from "./types";
import { dateLabel, catalog } from "./archive";
interface Props {
  data: Archive;
  events: Entry[];
  active: string[];
  onSelect: (id: string) => void;
  range: [number, number] | null;
  overlayLinks: boolean;
  sourceIds: string[];
  highlightedId: string | null;
}
export default function Timeline({
  data,
  events,
  active,
  onSelect,
  range,
  overlayLinks,
  sourceIds,
  highlightedId,
}: Props) {
  const [hover, setHover] = useState<{
    entry: Entry;
    x: number;
    y: number;
  } | null>(null);
  const highlightedRef = useRef(highlightedId);
  highlightedRef.current = highlightedId;
  const applyHighlight = () => {
    const svg = d3.select(ref.current);
    const selected = highlightedRef.current;
    svg.selectAll<SVGElement, unknown>("[data-from]").each(function () {
      const related =
        this.dataset.from === selected || this.dataset.to === selected;
      d3.select(this)
        .attr("stroke-width", related ? 4 : this.dataset.baseWidth || 1)
        .attr(
          "stroke-opacity",
          selected ? (related ? 1 : 0.12) : this.dataset.baseOpacity || 0.3,
        )
        .classed("highlighted-connection", !!selected && related);
    });
    svg
      .selectAll<SVGElement, unknown>("[data-event-id]")
      .classed("highlighted-event", function () {
        return this.dataset.eventId === selected;
      })
      .attr("aria-pressed", function () {
        return this.dataset.eventId === selected ? "true" : "false";
      });
  };
  useEffect(applyHighlight, [highlightedId]);
  const ref = useRef<SVGSVGElement>(null);
  const [width, setWidth] = useState(800);
  const [windowLabel, setWindowLabel] = useState("");
  const zoomMemory = useRef<{
    data: Archive;
    range: string;
    transform: d3.ZoomTransform;
    width: number;
  } | null>(null);
  const controls = useRef<(a: string) => void>(() => {});
  const lanes = data.lanes.filter((l) => active.includes(l.id));
  const height = Math.max(280, 150 + lanes.length * 130);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new ResizeObserver(([box]) =>
      setWidth(Math.max(220, box.contentRect.width)),
    );
    observer.observe(el.parentElement!);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    const el = ref.current!;
    const svg = d3.select(el);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);
    const visibleLanes = data.lanes.filter((l) => active.includes(l.id));
    const y = (id: string) =>
      120 + visibleLanes.findIndex((l) => l.id === id) * 130;
    const dates = data.events.map((e) => new Date(e.date!));
    if (!dates.length) return;
    const domain: [Date, Date] = range
      ? [
          new Date(Date.UTC(range[0], 0, 1)),
          new Date(Date.UTC(range[1] + 1, 0, 1)),
        ]
      : [
          d3.utcMonth.offset(d3.min(dates)!, -6),
          d3.utcMonth.offset(
            d3.max(data.events.map((e) => new Date(e.endDate || e.date!)))!,
            6,
          ),
        ];
    const scale = d3
      .scaleUtc()
      .domain(domain)
      .range([35, width - 35]);
    svg
      .append("defs")
      .append("marker")
      .attr("id", "influence-arrow")
      .attr("viewBox", "0 0 10 10")
      .attr("refX", 9)
      .attr("refY", 5)
      .attr("markerWidth", 5)
      .attr("markerHeight", 5)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M 0 0 L 10 5 L 0 10 z")
      .attr("fill", "#cdb88a");
    svg
      .append("defs")
      .append("clipPath")
      .attr("id", "chart-clip")
      .append("rect")
      .attr("width", width)
      .attr("height", height);
    const plot = svg.append("g").attr("clip-path", "url(#chart-clip)");
    const grid = plot.append("g");
    const axis = plot.append("g").attr("transform", "translate(0,40)");
    const connectionLayer = plot.append("g");
    const markLayer = plot.append("g");
    visibleLanes.forEach((l) =>
      plot
        .append("line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", y(l.id))
        .attr("y2", y(l.id))
        .attr("stroke", l.color)
        .attr("stroke-opacity", 0.25)
        .attr("pointer-events", "none"),
    );
    markLayer.raise();
    const filtered = events
      .filter((e) => e.lanes?.some((l) => active.includes(l)))
      .sort((a, b) => a.date!.localeCompare(b.date!));
    const numbers = new Map(filtered.map((e, i) => [e.id, i + 1]));
    const showPreview = (event: MouseEvent | FocusEvent, entry: Entry) => {
      const box = el.closest(".timeline")!.getBoundingClientRect();
      const target = (event.currentTarget as Element).getBoundingClientRect();
      const px =
        "clientX" in event ? event.clientX : target.left + target.width / 2;
      const py = "clientY" in event ? event.clientY : target.top;
      setHover({
        entry,
        x: Math.max(10, Math.min(px - box.left + 15, box.width - 360)),
        y: Math.max(64, py - box.top - 160),
      });
    };
    const endOf = (e: Entry) => {
      if (e.endDate) return new Date(e.endDate);
      const date = new Date(e.date!);
      if (e.precision === "year") return d3.utcYear.offset(date, 1);
      if (e.precision === "month") return d3.utcMonth.offset(date, 1);
      return date;
    };
    function draw(transform: d3.ZoomTransform) {
      const x = transform.rescaleX(scale);
      const format = d3.utcFormat(
        x.domain()[1].valueOf() - x.domain()[0].valueOf() < 90 * 86400000
          ? "%d %b %Y"
          : "%b %Y",
      );
      setWindowLabel(
        `${format(x.invert(35))} — ${format(x.invert(width - 35))}`,
      );
      axis.call(
        d3
          .axisTop(x)
          .ticks(Math.max(3, width / 150))
          .tickFormat((date) =>
            d3.utcFormat(
              x.domain()[1].valueOf() - x.domain()[0].valueOf() >
                6 * 365 * 86400000
                ? "%Y"
                : x.domain()[1].valueOf() - x.domain()[0].valueOf() <
                    90 * 86400000
                  ? "%d %b %Y"
                  : "%b %Y",
            )(date as Date),
          )
          .tickSize(0)
          .tickPadding(12),
      );
      axis.select(".domain").remove();
      grid.selectAll("*").remove();
      x.ticks(Math.max(3, width / 130)).forEach((date) =>
        grid
          .append("line")
          .attr("x1", x(date))
          .attr("x2", x(date))
          .attr("y1", 48)
          .attr("y2", height - 20)
          .attr("stroke", "#303630")
          .attr("stroke-dasharray", "2 5"),
      );
      connectionLayer.selectAll("*").remove();
      markLayer.selectAll("*").remove();
      const positions = new Map<string, number>();
      visibleLanes.forEach((l) => {
        const ends = [-Infinity, -Infinity, -Infinity, -Infinity, -Infinity];
        const offsets = [0, -16, 16, -32, 32];
        filtered
          .filter((e) => e.lanes!.includes(l.id))
          .forEach((e) => {
            const px = x(new Date(e.date!));
            let track = ends.findIndex((end) => px >= end + 16);
            if (track < 0) track = ends.indexOf(Math.min(...ends));
            positions.set(`${e.id}:${l.id}`, y(l.id) + offsets[track]);
            ends[track] = px;
          });
      });
      const pointY = (e: Entry, id: string) =>
        positions.get(`${e.id}:${id}`) || y(id);

      if (overlayLinks && sourceIds.length > 1) {
        const sourceOf = (e: Entry) =>
          e.citations.find((c) => sourceIds.includes(c.sourceId))?.sourceId;
        const representative = (e: Entry) =>
          e.lanes!.find((id) => active.includes(id))!;
        const drawn = new Set<string>();
        let count = 0;
        const byId = new Map(filtered.map((e) => [e.id, e]));
        const arc = (a: Entry, b: Entry, label: string, solid = false) => {
          const ax = x(new Date(a.date!)),
            bx = x(new Date(b.date!)),
            ay = pointY(a, representative(a)),
            by = pointY(b, representative(b));
          if (Math.max(ax, bx) < 0 || Math.min(ax, bx) > width) return;
          const curve = connectionLayer
            .append("path")
            .attr("data-from", a.id)
            .attr("data-to", b.id)
            .attr("data-base-width", solid ? 1.4 : 1)
            .attr("data-base-opacity", solid ? 0.7 : 0.4)
            .attr(
              "d",
              `M${ax},${ay} C${ax + (bx - ax) * 0.33},${ay - 35} ${ax + (bx - ax) * 0.67},${by - 35} ${bx},${by}`,
            )
            .attr("fill", "none")
            .attr("stroke", solid ? "#cdb88a" : "#76977b")
            .attr("stroke-opacity", solid ? 0.7 : 0.4)
            .attr("stroke-width", solid ? 1.4 : 1)
            .attr("stroke-dasharray", solid ? null : "4 6")
            .attr("pointer-events", "stroke")
            .style("cursor", "pointer")
            .on("click", () => onSelect(b.id));
          if (solid) curve.attr("marker-end", "url(#influence-arrow)");
          curve.append("title").text(label);
        };
        for (const link of data.eventLinks || []) {
          const a = byId.get(link.fromId),
            b = byId.get(link.toId);
          if (
            a &&
            b &&
            link.citations.some((c) => sourceIds.includes(c.sourceId))
          )
            arc(
              a,
              b,
              `${link.label} · ${link.citations.map((c) => `${c.sourceId}, pp. ${c.pages.join(", ")}`).join("; ")}`,
              true,
            );
        }
        // Link chronological neighbors sharing an explicitly cited participant across sources.
        const entityEvents = new Map<string, Entry[]>();
        for (const e of filtered)
          for (const id of [...e.people!, ...e.organizations!])
            entityEvents.set(id, [...(entityEvents.get(id) || []), e]);
        for (const [id, related] of entityEvents) {
          const name =
            [
              ...data.people,
              ...data.organizations,
              ...(data.references || []),
            ].find((e) => e.id === id)?.name || id;
          for (let i = 1; i < related.length; i++) {
            const a = related[i - 1],
              b = related[i];
            if (sourceOf(a) === sourceOf(b)) continue;
            const key = [a.id, b.id].sort().join(":");
            if (drawn.has(key) || count >= 70) continue;
            drawn.add(key);
            count++;
            arc(
              a,
              b,
              `Shared participant: ${name}. This connection alone does not establish influence or causation.`,
            );
          }
        }
      }

      filtered.forEach((e) => {
        const px = x(new Date(e.date!));
        const end = x(endOf(e));
        if (end < -180 || px > width + 180) return;
        const belongs = e.lanes!.filter((l) => active.includes(l));
        if (belongs.length > 1)
          connectionLayer
            .append("line")
            .attr("data-from", e.id)
            .attr("data-to", e.id)
            .attr("data-base-width", 1)
            .attr("data-base-opacity", 0.3)
            .style("cursor", "pointer")
            .on("click", () => {
              setHover(null);
              onSelect(e.id);
            })
            .attr("x1", px)
            .attr("x2", px)
            .attr("y1", pointY(e, belongs[0]))
            .attr("y2", pointY(e, belongs[belongs.length - 1]))
            .attr("stroke", "#ded6c1")
            .attr("stroke-opacity", 0.3)
            .attr("stroke-dasharray", "3 5");
        belongs.forEach((id) => {
          const l = visibleLanes.find((l) => l.id === id)!;
          const g = markLayer
            .append("g")
            .attr("data-event-id", e.id)
            .attr("tabindex", 0)
            .attr("role", "button")
            .attr(
              "aria-label",
              `${e.name}, ${dateLabel(e)}, ${e.precision} precision`,
            )
            .style("cursor", "pointer")
            .on("mouseenter", (event: MouseEvent) => showPreview(event, e))
            .on("mouseleave", () => setHover(null))
            .on("focus", (event: FocusEvent) => showPreview(event, e))
            .on("blur", () => setHover(null))
            .on("click", () => {
              setHover(null);
              onSelect(e.id);
            })
            .on("keydown", (ev: KeyboardEvent) => {
              if (ev.key === "Enter" || ev.key === " ") {
                ev.preventDefault();
                setHover(null);
                onSelect(e.id);
              }
            });
          g.append("title").text(
            `${e.name} · ${dateLabel(e)} · ${e.precision} precision`,
          );
          if (end > px)
            g.append("line")
              .attr("x1", px)
              .attr("x2", end)
              .attr("y1", pointY(e, id))
              .attr("y2", pointY(e, id))
              .attr("stroke", l.color)
              .attr("stroke-width", 5)
              .attr("stroke-opacity", 0.35);
          g.append("circle")
            .attr("cx", px)
            .attr("cy", pointY(e, id))
            .attr("r", 12)
            .attr("fill", "transparent");
          g.append("circle")
            .attr("cx", px)
            .attr("cy", pointY(e, id))
            .attr("r", 7)
            .attr("fill", l.color)
            .attr("stroke", "#171b18")
            .attr("stroke-width", 1.7);
          g.append("text")
            .attr("x", px)
            .attr("y", pointY(e, id) + 2.5)
            .attr("text-anchor", "middle")
            .attr("font-size", 6.5)
            .attr("fill", "#151a13")
            .attr("font-weight", 700)
            .attr("pointer-events", "none")
            .text(numbers.get(e.id)!);
        });
      });
      visibleLanes.forEach((l) => {
        const ends = [-Infinity, -Infinity];
        filtered
          .filter((e) => e.lanes!.includes(l.id))
          .forEach((e) => {
            const px = x(new Date(e.date!));
            if (px < 5 || px > width - 12) return;
            const words = `#${numbers.get(e.id)} ${e.name}`.split(" ");
            const lines: string[] = [];
            for (const word of words) {
              if (
                !lines.length ||
                lines[lines.length - 1].length + word.length > 31
              )
                lines.push(word);
              else lines[lines.length - 1] += " " + word;
            }
            const labelWidth = Math.max(...lines.map((t) => t.length)) * 6;
            const row = ends.findIndex((end) => px > end + 18);
            if (row < 0 || px + labelWidth > width - 5) return;
            const label = markLayer
              .append("text")
              .attr("x", px + 12)
              .attr("y", y(l.id) + (row === 0 ? -48 : 48))
              .attr("fill", l.color)
              .attr("font-size", 11)
              .style("cursor", "pointer")
              .on("mouseenter", (event: MouseEvent) => showPreview(event, e))
              .on("mouseleave", () => setHover(null))
              .on("click", () => {
                setHover(null);
                onSelect(e.id);
              });
            lines.forEach((line, i) =>
              label
                .append("tspan")
                .attr("x", px + 12)
                .attr("dy", i ? 13 : 0)
                .text(line),
            );
            ends[row] = px + labelWidth;
          });
      });
      applyHighlight();
    }
    const behavior = d3
      .zoom<SVGSVGElement, unknown>()
      .filter((event) =>
        event.type === "wheel" ? event.ctrlKey || event.metaKey : !event.button,
      )
      .scaleExtent([1, 2000])
      .extent([
        [0, 0],
        [width, height],
      ])
      .translateExtent([
        [0, 0],
        [width, height],
      ])
      .on("zoom", (ev) => {
        setHover(null);
        zoomMemory.current = {
          data,
          range: JSON.stringify(range),
          transform: ev.transform,
          width,
        };
        draw(ev.transform);
      });
    svg.call(behavior);
    const saved = zoomMemory.current;
    svg.call(
      behavior.transform,
      saved?.data === data && saved.range === JSON.stringify(range)
        ? d3.zoomIdentity
            .translate((saved.transform.x * width) / saved.width, 0)
            .scale(saved.transform.k)
        : d3.zoomIdentity,
    );
    controls.current = (action) => {
      const transition = svg
        .transition()
        .duration(
          matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 350,
        );
      if (action === "reset")
        transition.call(behavior.transform, d3.zoomIdentity);
      else if (action === "left" || action === "right")
        transition.call(
          behavior.translateBy,
          action === "left" ? 120 : -120,
          0,
        );
      else transition.call(behavior.scaleBy, action === "in" ? 1.8 : 1 / 1.8);
    };
    return () => {
      svg.interrupt();
      svg.on(".zoom", null);
    };
  }, [
    data,
    events,
    active,
    onSelect,
    range,
    width,
    height,
    overlayLinks,
    sourceIds,
  ]);
  return (
    <>
      <div className="chart-toolbar">
        <span>CTRL + SCROLL TO ZOOM · DRAG TO EXPLORE</span>
        <div>
          {[
            ["left", "←"],
            ["right", "→"],
            ["out", "−"],
            ["in", "+"],
            ["reset", "Fit all"],
          ].map(([a, b]) => (
            <button
              key={a}
              aria-label={
                a === "in"
                  ? "Zoom in"
                  : a === "out"
                    ? "Zoom out"
                    : a === "reset"
                      ? "Fit all events"
                      : `Pan ${a}`
              }
              onClick={() => controls.current(a)}
            >
              {b}
            </button>
          ))}
        </div>
      </div>
      <div className="chart-scroll">
        <svg
          ref={ref}
          style={{ height }}
          aria-label="Interactive intersecting event timelines"
        />
      </div>
      <div className="chart-footer">
        <span>
          <i /> Shared event · bars show date precision / duration
        </span>
        <span aria-live="polite">{windowLabel}</span>
      </div>
      {hover && (
        <div
          className="timeline-tooltip"
          role="status"
          style={{ left: hover.x, top: hover.y }}
        >
          <span className="tiny-label">
            {dateLabel(hover.entry)} · {hover.entry.precision}
          </span>
          <strong>{hover.entry.name}</strong>
          <span className="tiny-label">
            {hover.entry.citations
              .map(
                (c) =>
                  catalog.sources.find((s) => s.id === c.sourceId)?.author ||
                  "Source",
              )
              .filter((s, i, a) => a.indexOf(s) === i)
              .join(" · ")}
          </span>
          <p>
            {hover.entry.sourceSummaries?.[0]?.summary ||
              hover.entry.description}
          </p>
          <small>
            Click or press Enter to highlight connections and explore details in
            the side panel.
          </small>
        </div>
      )}
    </>
  );
}
