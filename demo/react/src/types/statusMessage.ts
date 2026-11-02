export type StatusMessageType = 'success' | 'error' | 'warning' | 'info' | 'loading';

export interface StatusMessage {
  id: string;
  type: StatusMessageType;
  message: string;
  description?: string;
  duration?: number; // ms before auto-dismiss (0 for persistent)
}
