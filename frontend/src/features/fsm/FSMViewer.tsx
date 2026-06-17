import React, { useMemo } from "react";
import { ReactFlow, Background, Controls } from "@xyflow/react";
import '@xyflow/react/dist/style.css';
import { IntakeNode, TriageNode, VerificationNode, OptimizationNode, ReadyNode, RejectedNode } from "./nodes";
import type { ApplicationDetailResponse } from "@/api/contracts";
import { generateGraph } from "./graphTransform";

// Statically memoize nodeTypes outside component
const nodeTypes = {
  intakeNode: IntakeNode,
  triageNode: TriageNode,
  verificationNode: VerificationNode,
  optimizationNode: OptimizationNode,
  readyNode: ReadyNode,
  rejectedNode: RejectedNode,
};

interface FSMViewerProps {
  application: ApplicationDetailResponse;
}

export const FSMViewer = React.memo(({ application }: FSMViewerProps) => {
  // Memoize graph transforms to prevent rerenders unless application data changes
  const { nodes, edges } = useMemo(() => generateGraph(application), [application]);

  return (
    <div className="h-full w-full bg-slate-50/50 rounded-xl border border-border overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.5}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={12} size={1} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
});
FSMViewer.displayName = "FSMViewer";
