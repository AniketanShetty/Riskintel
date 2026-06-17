import type { Node, Edge } from "@xyflow/react";
import type { FSMState, FSMNodeData } from "./types";
import type { ApplicationDetailResponse } from "@/api/contracts";

const STATE_ORDER: Record<string, number> = {
  "INTAKE": 0,
  "TRIAGE": 1,
  "PENDING_VERIFICATION": 2,
  "VERIFIED": 3,
  "OPTIMIZATION": 4,
  "READY": 5,
  "REJECTED": 99,
};

export const generateGraph = (app: ApplicationDetailResponse): { nodes: Node<FSMNodeData>[], edges: Edge[] } => {
  const currentState = app.current_state as FSMState;
  const currentIdx = STATE_ORDER[currentState] ?? -1;

  const createNodeData = (state: FSMState, label: string): FSMNodeData => {
    // Determine active logic for composite states (VERIFIED is basically ready for OPTIMIZATION)
    let isActive = currentState === state;
    if (state === "PENDING_VERIFICATION" && currentState === "VERIFIED") {
      isActive = false; // verified means passed this node
    }

    return {
      label,
      state,
      isActive,
      isCompleted: STATE_ORDER[state] < currentIdx || (state === "PENDING_VERIFICATION" && currentState === "VERIFIED"),
      isPending: STATE_ORDER[state] > currentIdx,
      sessionId: app.id,
    };
  };

  const nodes: Node<FSMNodeData>[] = [
    {
      id: "intake",
      type: "intakeNode",
      position: { x: 250, y: 50 },
      data: createNodeData("INTAKE", "App Received"),
    },
    {
      id: "triage",
      type: "triageNode",
      position: { x: 250, y: 200 },
      data: createNodeData("TRIAGE", `Gate: ${app.bureau_gate_status || 'Pending'}`),
    },
  ];

  const edges: Edge[] = [
    { id: "e-intake-triage", source: "intake", target: "triage", animated: currentState === "INTAKE" },
  ];

  if (currentState === "REJECTED") {
    nodes.push({
      id: "rejected",
      type: "rejectedNode",
      position: { x: 500, y: 350 },
      data: createNodeData("REJECTED", "Application Declined"),
    });
    edges.push({ id: "e-triage-reject", source: "triage", target: "rejected", animated: false, style: { stroke: 'var(--color-destructive)' } });
  } else {
    nodes.push(
      {
        id: "verification",
        type: "verificationNode",
        position: { x: 250, y: 350 },
        data: createNodeData("PENDING_VERIFICATION", "Webhooks Processing"),
      },
      {
        id: "optimization",
        type: "optimizationNode",
        position: { x: 250, y: 500 },
        data: createNodeData("OPTIMIZATION", "Pricing Engine"),
      },
      {
        id: "ready",
        type: "readyNode",
        position: { x: 250, y: 650 },
        data: createNodeData("READY", "Counter-Offer Generated"),
      }
    );
    
    edges.push(
      { id: "e-triage-verify", source: "triage", target: "verification", animated: currentState === "TRIAGE" },
      { id: "e-verify-opt", source: "verification", target: "optimization", animated: currentState === "PENDING_VERIFICATION" || currentState === "VERIFIED" },
      { id: "e-opt-ready", source: "optimization", target: "ready", animated: currentState === "OPTIMIZATION" }
    );
  }

  return { nodes, edges };
};
