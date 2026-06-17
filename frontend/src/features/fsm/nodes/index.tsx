import React from "react";
import { Handle, Position } from "@xyflow/react";
import type { NodeProps, Node } from "@xyflow/react";
import type { FSMNodeData } from "../types";
import { cn } from "@/lib/utils";

const NodeWrapper = ({ data, title, children, hasTarget, hasSource }: { data: FSMNodeData, title: string, children?: React.ReactNode, hasTarget?: boolean, hasSource?: boolean }) => {
  return (
    <div className={cn(
      "w-48 px-4 py-3 shadow-sm rounded-lg bg-background border-2 transition-all duration-200",
      data.isActive ? "border-blue-500 ring-4 ring-blue-500/20" : 
      data.isCompleted ? "border-success bg-success/5" : 
      "border-border opacity-60 grayscale"
    )}>
      {hasTarget && <Handle type="target" position={Position.Top} className="w-3 h-3 bg-muted-foreground" />}
      <div className="flex flex-col gap-1">
        <div className="font-semibold text-sm tracking-tight text-foreground">{title}</div>
        <div className="text-xs text-muted-foreground font-mono">{data.label}</div>
        {children}
      </div>
      {hasSource && <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-muted-foreground" />}
    </div>
  );
};

export const IntakeNode = React.memo(({ data }: NodeProps<Node<FSMNodeData>>) => {
  return <NodeWrapper data={data} title="1. Intake" hasSource />;
});
IntakeNode.displayName = "IntakeNode";

export const TriageNode = React.memo(({ data }: NodeProps<Node<FSMNodeData>>) => {
  return <NodeWrapper data={data} title="2. Triage Evaluation" hasTarget hasSource />;
});
TriageNode.displayName = "TriageNode";

export const VerificationNode = React.memo(({ data }: NodeProps<Node<FSMNodeData>>) => {
  return (
    <NodeWrapper data={data} title="3. Verification" hasTarget hasSource>
      {data.isActive && <div className="mt-2 text-[10px] uppercase font-bold text-blue-600 animate-pulse">Awaiting Webhooks...</div>}
    </NodeWrapper>
  );
});
VerificationNode.displayName = "VerificationNode";

export const OptimizationNode = React.memo(({ data }: NodeProps<Node<FSMNodeData>>) => {
  return <NodeWrapper data={data} title="4. Optimization" hasTarget hasSource />;
});
OptimizationNode.displayName = "OptimizationNode";

export const ReadyNode = React.memo(({ data }: NodeProps<Node<FSMNodeData>>) => {
  return (
    <NodeWrapper data={data} title="5. Ready" hasTarget>
      {data.isCompleted && <div className="mt-2 text-xs font-medium text-success">Offer Generated</div>}
    </NodeWrapper>
  );
});
ReadyNode.displayName = "ReadyNode";

export const RejectedNode = React.memo(({ data }: NodeProps<Node<FSMNodeData>>) => {
  return (
    <div className={cn(
      "w-48 px-4 py-3 shadow-sm rounded-lg bg-destructive/10 border-2 transition-all duration-200",
      data.isActive || data.isCompleted ? "border-destructive ring-4 ring-destructive/20 opacity-100" : "border-border opacity-40 grayscale"
    )}>
      <Handle type="target" position={Position.Top} className="w-3 h-3 bg-muted-foreground" />
      <div className="flex flex-col gap-1">
        <div className="font-semibold text-sm tracking-tight text-destructive">Rejected</div>
        <div className="text-xs text-muted-foreground font-mono">{data.label}</div>
      </div>
    </div>
  );
});
RejectedNode.displayName = "RejectedNode";
