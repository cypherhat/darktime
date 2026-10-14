import {useEffect,useRef,useState} from 'react';
import * as d3 from 'd3';
import type {Archive,Entry} from './types';
export function Timeline({data,events,active,onSelect}:{data:Archive;events:Entry[];active:string[];onSelect:(id:string)=>void}){
 const [size,setSize]=useState(0);
 const ref=useRef<SVGSVGElement>(null);const controls=useRef<(action:string)=>void>(()=>{});
 useEffect(()=>{
 const el=ref.current!;const svg=d3.select(el);const width=Math.max(el.parentElement!.clientWidth,650);const height=480;const left=0;
 svg.selectAll('*').remove();svg.attr('viewBox',`0 0 ${width} ${height}`);
 const lanes=data.lanes.filter(l=>active.includes(l.id));const y=(id:string)=>100+lanes.findIndex(l=>l.id===id)*75;
 const dates=data.events.map(e=>new Date(e.date!));const scale=d3.scaleUtc().domain([d3.utcMonth.offset(d3.min(dates)!,-3),d3.utcMonth.offset(d3.max(dates)!,3)]).range([left+45,width-45]);
 svg.append('defs').append('clipPath').attr('id','chart-clip').append('rect').attr('width',width).attr('height',height);
 const plot=svg.append('g').attr('clip-path','url(#chart-clip)');const axis=plot.append('g').attr('transform','translate(0,40)');const grid=plot.append('g');const connections=plot.append('g');const marks=plot.append('g');
 lanes.forEach(l=>{plot.append('line').attr('x1',0).attr('x2',width).attr('y1',y(l.id)).attr('y2',y(l.id)).attr('stroke',l.color).attr('stroke-opacity',.35);});
 const filtered=events.filter(e=>e.lanes?.some(l=>active.includes(l)));
 function draw(transform:d3.ZoomTransform){const x=transform.rescaleX(scale);axis.call(d3.axisTop(x).ticks(Math.max(3,width/130)).tickSize(0).tickPadding(12));axis.select('.domain').remove();grid.selectAll('*').remove();x.ticks(Math.max(3,width/130)).forEach(date=>grid.append('line').attr('x1',x(date)).attr('x2',x(date)).attr('y1',48).attr('y2',height-25).attr('stroke','#303630').attr('stroke-dasharray','2 5'));
 connections.selectAll('*').remove();marks.selectAll('*').remove();
 filtered.forEach(e=>{const px=x(new Date(e.date!));if(px < -180 || px>width+180)return;const belongs=e.lanes!.filter(l=>active.includes(l));if(belongs.length>1)connections.append('line').attr('x1',px).attr('x2',px).attr('y1',y(belongs[0])).attr('y2',y(belongs[belongs.length-1])).attr('stroke','#ded6c1').attr('stroke-opacity',.35).attr('stroke-dasharray','3 5');
 belongs.forEach(id=>{const l=lanes.find(l=>l.id===id)!;const g=marks.append('g').attr('transform',`translate(${px},${y(id)})`).attr('tabindex',0).attr('role','button').attr('aria-label',`${e.name}, ${e.date}`).style('cursor','pointer').on('click',()=>onSelect(e.id)).on('keydown',(ev:KeyboardEvent)=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();onSelect(e.id)}});g.append('title').text(`${e.name} · ${e.date} · ${e.precision}`);g.append('circle').attr('r',15).attr('fill','transparent');g.append('circle').attr('r',belongs.length>1?6:4.5).attr('fill',l.color).attr('stroke','#171b18').attr('stroke-width',2);
 // Greedy label placement keeps nearby records clickable while avoiding overlapping text.
 });});
 lanes.forEach(l=>{let end=-Infinity;filtered.filter(e=>e.lanes!.includes(l.id)).sort((a,b)=>a.date!.localeCompare(b.date!)).forEach(e=>{const px=x(new Date(e.date!));const label=e.name.length>28?e.name.slice(0,26)+'…':e.name;const labelWidth=label.length*6.3;if(px<8||px+labelWidth>width-8||px<end+14)return;marks.append('text').attr('x',px+10).attr('y',y(l.id)-15).attr('fill',l.color).attr('font-size',11).text(label).style('cursor','pointer').on('click',()=>onSelect(e.id));end=px+labelWidth;});});
 }
 const behavior=d3.zoom<SVGSVGElement,unknown>().scaleExtent([1,1200]).extent([[0,0],[width,height]]).translateExtent([[0,0],[width,height]]).on('zoom',ev=>draw(ev.transform));svg.call(behavior);draw(d3.zoomIdentity);
 controls.current=(a)=>{const selection=svg.transition().duration(matchMedia('(prefers-reduced-motion: reduce)').matches?0:350);if(a==='reset')selection.call(behavior.transform,d3.zoomIdentity);else if(a==='left'||a==='right')selection.call(behavior.translateBy,a==='left'?120:-120,0);else selection.call(behavior.scaleBy,a==='in'?1.8:1/1.8)};
 const observer=new ResizeObserver(()=>{if(Math.abs(el.parentElement!.clientWidth-width)>10){setSize(el.parentElement!.clientWidth)}});observer.observe(el.parentElement!);return()=>{observer.disconnect();svg.on('.zoom',null)};
 },[data,events,active,onSelect,size]);
 return <><div className="chart-toolbar"><span>SCROLL TO ZOOM · DRAG TO EXPLORE</span><div>{[['left','←'],['right','→'],['out','−'],['in','+'],['reset','Fit all']].map(([a,b])=><button key={a} aria-label={a==='in'?'Zoom in':a==='out'?'Zoom out':a==='reset'?'Fit all events':`Pan ${a}`} onClick={()=>controls.current(a)}>{b}</button>)}</div></div><div className="chart-scroll"><svg ref={ref} aria-label="Interactive intersecting event timelines"/></div><div className="chart-footer"><span><i/> Shared events connect multiple threads</span><span>DAY-LEVEL ZOOM · VECTOR RESOLUTION</span></div></>;
}
