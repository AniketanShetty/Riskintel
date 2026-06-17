export type FSMState =
  | "INTAKE"
  | "TRIAGE"
  | "PENDING_VERIFICATION"
  | "VERIFIED"
  | "OPTIMIZATION"
  | "READY"
  | "REJECTED"
  | "DEAD_LETTER"; // For error handling/DLQ context if needed

export interface FSMNodeData extends Record<string, unknown> {
  label: string;
  state: FSMState;
  isActive: boolean;
  isCompleted: boolean;
  isPending: boolean;
  sessionId?: string;
  metadata?: any;
}
