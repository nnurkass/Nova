import { StreamEvent, TaskItem, TaskRequest, TaskResult } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

export async function fetchHealth(): Promise<{
  status: string;
  service: string;
  components: Record<string, string>;
}> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return await res.json();
  } catch (err) {
    return {
      status: 'offline',
      service: 'Nova Multi-Agent Construction AI',
      components: {
        database: 'offline',
        goszakup_api: 'mock',
        llm_provider: 'mock',
      },
    };
  }
}

export async function fetchTasks(limit = 20): Promise<TaskItem[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/tasks?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch tasks');
    return await res.json();
  } catch (err) {
    console.warn('API fetchTasks error:', err);
    return [];
  }
}

export async function fetchTask(taskId: string): Promise<TaskItem> {
  const res = await fetch(`${API_BASE}/api/v1/tasks/${taskId}`);
  if (!res.ok) throw new Error(`Task ${taskId} not found`);
  return await res.json();
}

export async function createTask(payload: TaskRequest): Promise<{ task_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/api/v1/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create task');
  return await res.json();
}

export function connectTaskStream(
  taskId: string,
  taskPrompt: string,
  onEvent: (event: StreamEvent) => void,
  onComplete: (finalState?: TaskResult) => void,
  onError: (error: any) => void
): () => void {
  const url = `${API_BASE}/api/v1/tasks/${taskId}/stream?task=${encodeURIComponent(taskPrompt)}`;
  let eventSource: EventSource | null = null;

  try {
    eventSource = new EventSource(url);

    eventSource.onmessage = (e) => {
      try {
        const parsed: StreamEvent = JSON.parse(e.data);
        onEvent(parsed);

        if (parsed.event === 'pipeline_complete') {
          onComplete(parsed.state);
          eventSource?.close();
        } else if (parsed.event === 'error') {
          onError(parsed.message || 'Stream error');
          eventSource?.close();
        }
      } catch (err) {
        console.error('SSE JSON parse error:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.warn('EventSource connection error:', err);
      eventSource?.close();
      onError(err);
    };
  } catch (err) {
    onError(err);
  }

  return () => {
    if (eventSource) {
      eventSource.close();
    }
  };
}

export function connectTaskWebSocket(
  taskId: string,
  onEvent: (event: StreamEvent) => void,
  onComplete: () => void,
  onError: (error: any) => void
): () => void {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const wsUrl = `${protocol}//${host}/ws/tasks/${taskId}`;

  let ws: WebSocket | null = null;
  try {
    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const parsed: StreamEvent = JSON.parse(event.data);
        onEvent(parsed);
        if (parsed.event === 'pipeline_complete') {
          onComplete();
          ws?.close();
        }
      } catch (err) {
        console.error('WS Parse Error:', err);
      }
    };

    ws.onerror = (err) => {
      onError(err);
      ws?.close();
    };
  } catch (err) {
    onError(err);
  }

  return () => {
    if (ws) {
      ws.close();
    }
  };
}

export async function sendChatMessage(
  payload: import('../types').ChatRequestPayload
): Promise<import('../types').ChatResponsePayload> {
  const res = await fetch(`${API_BASE}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Chat API error: ${res.statusText}`);
  }
  return await res.json();
}
