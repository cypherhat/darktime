import { useEffect, useRef, useState, useMemo } from "react";
import * as d3 from "d3";
import type { Archive, Entry, Relationship } from "./types";
import { entriesOf } from "./archive";
interface Node extends d3.SimulationNodeDatum {
  id: string;
  entry: Entry;
  degree: number;
}
interface Edge extends d3.SimulationLinkDatum<Node> {
  record: Relationship;
}
export default function Connections({
  data,
  focus,
  onSelect,
  includeInferred,
}: {
  data: Archive;
  focus: string;
  onSelect: (id: string) => void;
  includeInferred: boolean;
}) {
  const ref = useRef<SVGSVGElement>(null);
  const [size, setSize] = useState(800);
  const [expanded, setExpanded] = useState(false);
  const controls = useRef<(a: string) => void>(() => {});
  const rows = useMemo(
    () =>
      data.relationships.filter(
        (r) =>
          includeInferred ||
          !(
            /tentative|conjecture|interpretation|allegation|hypothesis|contested|claim/i.test(
              r.evidence || "",
            ) || r.toId === "milner-group"
          ),
      ),
    [data, includeInferred],
  );
  const graph = useMemo(() => {
    const all = entriesOf(data);
    const counts = new Map<string, number>();
    for (const r of rows) {
      counts.set(r.fromId, (counts.get(r.fromId) || 0) + 1);
      counts.set(r.toId, (counts.get(r.toId) || 0) + 1);
    }
    let ids: Set<string>;
    if (focus) {
      ids = new Set([
        focus,
        ...rows
          .filter((r) => r.fromId === focus || r.toId === focus)
          .flatMap((r) => [r.fromId, r.toId]),
      ]);
    } else {
      ids = new Set(
        [...counts]
          .sort((a, b) => b[1] - a[1])
          .slice(0, expanded ? counts.size : 65)
          .map(([id]) => id),
      );
    }
    const nodes: Node[] = all
      .filter((e) => ids.has(e.id) && e.kind !== "event")
      .map((entry) => ({
        id: entry.id,
        entry,
        degree: counts.get(entry.id) || 0,
      }));
    const retained = new Set(nodes.map((n) => n.id));
    const edges: Edge[] = rows
      .filter((r) => retained.has(r.fromId) && retained.has(r.toId))
      .map((record) => ({
        source: record.fromId,
        target: record.toId,
        record,
      }));
    return { nodes, edges };
  }, [data, rows, focus, expanded]);
  useEffect(() => {
    const observer = new ResizeObserver(([box]) =>
      setSize(Math.max(500, box.contentRect.width)),
    );
    observer.observe(ref.current!.parentElement!);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    const svg = d3.select(ref.current!);
    svg.selectAll("*").remove();
    const h = 580;
    svg.attr("viewBox", `0 0 ${size} ${h}`);
    const root = svg.append("g");
    const color = (n: Node) =>
      n.entry.kind === "organization" ? "#9fabc8" : "#c9aa76";
    const nodes = graph.nodes.map((n) => ({ ...n }));
    const edges = graph.edges.map((e) => ({ ...e }));
    const line = root
      .append("g")
      .selectAll("line")
      .data(edges)
      .join("line")
      .attr("stroke", (e) =>
        /tentative|conjecture|interpretation|allegation|hypothesis|contested|claim/i.test(
          e.record.evidence || "",
        )
          ? "#8d738c"
          : "#596653",
      )
      .attr("stroke-opacity", 0.4)
      .attr("stroke-width", 1)
      .attr("stroke-dasharray", (e) =>
        /tentative|conjecture|interpretation|allegation|hypothesis|contested|claim/i.test(
          e.record.evidence || "",
        )
          ? "3 4"
          : null,
      );
    line
      .append("title")
      .text(
        (e) => `${e.record.label} · ${e.record.evidence || "Source account"}`,
      );
    const node = root
      .append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .attr("role", "button")
      .attr("tabindex", 0)
      .attr("aria-label", (n) => `${n.entry.name}, ${n.degree} connections`)
      .style("cursor", "pointer")
      .on("click", (_, n) => onSelect(n.id))
      .on("keydown", (ev: KeyboardEvent, n) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          onSelect(n.id);
        }
      });
    node
      .append("circle")
      .attr("r", (n) =>
        n.id === focus ? 13 : Math.min(10, 4 + Math.sqrt(n.degree)),
      )
      .attr("fill", color)
      .attr("stroke", (n) => (n.id === focus ? "#f5ecd6" : "#1b211a"))
      .attr("stroke-width", 2);
    node
      .append("title")
      .text(
        (n) =>
          `${n.entry.name} · ${n.degree} connections · ${n.entry.evidence || "Source account"}`,
      );
    node
      .append("text")
      .text((n) => n.entry.name)
      .attr("x", 13)
      .attr("y", 4)
      .attr("fill", "#c4ceb7")
      .attr("font-size", 10)
      .attr("paint-order", "stroke")
      .attr("stroke", "#181d18")
      .attr("stroke-width", 3)
      .style("display", (n) =>
        focus || graph.nodes.length <= 70 || n.degree > 6 ? "" : "none",
      );
    const simulation = d3
      .forceSimulation(nodes)
      .randomSource(d3.randomLcg(0.42))
      .force(
        "link",
        d3
          .forceLink<Node, Edge>(edges)
          .id((n) => n.id)
          .distance(focus ? 120 : 90),
      )
      .force("charge", d3.forceManyBody().strength(focus ? -350 : -220))
      .force("center", d3.forceCenter(size / 2, h / 2))
      .force(
        "collision",
        d3
          .forceCollide<Node>()
          .radius((n) => (focus ? 40 : Math.min(35, 12 + n.degree))),
      );
    simulation.on("tick", () => {
      line
        .attr("x1", (e) => (e.source as Node).x!)
        .attr("y1", (e) => (e.source as Node).y!)
        .attr("x2", (e) => (e.target as Node).x!)
        .attr("y2", (e) => (e.target as Node).y!);
      node.attr("transform", (n) => `translate(${n.x},${n.y})`);
    });
    // Bound render time: settle deterministically once, then permit user-driven navigation.
    simulation.stop();
    simulation.tick(240);
    line
      .attr("x1", (e) => (e.source as Node).x!)
      .attr("y1", (e) => (e.source as Node).y!)
      .attr("x2", (e) => (e.target as Node).x!)
      .attr("y2", (e) => (e.target as Node).y!);
    node.attr("transform", (n) => `translate(${n.x},${n.y})`);
    const fit = () => {
      if (!nodes.length) return d3.zoomIdentity;
      const minX = d3.min(nodes, (n) => n.x!)! - 40,
        maxX = d3.max(nodes, (n) => n.x!)! + 150,
        minY = d3.min(nodes, (n) => n.y!)! - 35,
        maxY = d3.max(nodes, (n) => n.y!)! + 35;
      const k = Math.min(
        1.6,
        (size - 50) / (maxX - minX),
        (h - 50) / (maxY - minY),
      );
      return d3.zoomIdentity
        .translate(
          size / 2 - (k * (minX + maxX)) / 2,
          h / 2 - (k * (minY + maxY)) / 2,
        )
        .scale(k);
    };
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .extent([
        [0, 0],
        [size, h],
      ])
      .scaleExtent([0.15, 8])
      .on("zoom", (ev) => root.attr("transform", ev.transform.toString()));
    svg.call(zoom).call(zoom.transform, fit());
    controls.current = (a) => {
      const t = svg
        .transition()
        .duration(
          matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 300,
        );
      if (a === "reset") t.call(zoom.transform, fit());
      else t.call(zoom.scaleBy, a === "in" ? 1.5 : 1 / 1.5);
    };
    return () => {
      simulation.stop();
      svg.interrupt();
      svg.on(".zoom", null);
    };
  }, [graph, size, focus, onSelect]);
  return (
    <div className="graph-panel">
      <div className="chart-toolbar">
        <span>
          {graph.nodes.length} ENTITIES · {graph.edges.length} CITED CONNECTIONS
        </span>
        <div>
          {!focus && (
            <button onClick={() => setExpanded(!expanded)}>
              {expanded ? "Core 65" : "Show all"}
            </button>
          )}
          <button
            aria-label="Zoom out connections"
            onClick={() => controls.current("out")}
          >
            −
          </button>
          <button
            aria-label="Zoom in connections"
            onClick={() => controls.current("in")}
          >
            +
          </button>
          <button onClick={() => controls.current("reset")}>Fit graph</button>
        </div>
      </div>
      <div className="graph-canvas">
        <svg
          ref={ref}
          aria-label="Interactive people and organization connections"
        />
      </div>
      {!graph.nodes.length && (
        <p className="empty">No connections match this selection.</p>
      )}
      <div className="chart-footer">
        <span>
          ● People &nbsp;{" "}
          <span style={{ color: "#9fabc8" }}>● Organizations</span>
        </span>
        <span>Dashed edges: author inference / tentative roster</span>
      </div>
    </div>
  );
}
