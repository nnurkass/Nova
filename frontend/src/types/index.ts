export type TaskStatusType = 'pending' | 'running' | 'completed' | 'failed';

export interface TenderLot {
  id: number | string;
  lot_number: string;
  name_ru: string;
  amount: number;
  count?: number;
  unit?: string;
  description_ru?: string;
}

export interface Tender {
  id: number | string;
  number: string;
  name_ru: string;
  total_sum: number;
  organizer_name_ru: string;
  organizer_bin: string;
  status: string;
  publish_date?: string;
  end_date?: string;
  trade_type?: string;
  lots: TenderLot[];
  score?: number;
  recommendation?: string;
}

export interface ABCWork {
  code: string;
  name: string;
  unit: string;
  quantity: number;
  price?: number | null;
}

export interface ABCMaterial {
  code: string;
  name: string;
  unit: string;
  quantity: number;
  price?: number | null;
}

export interface StockItem {
  code: string;
  name: string;
  unit: string;
  required_quantity: number;
  in_stock_quantity: number;
  deficit_quantity: number;
  coverage_percent: number;
  status: 'IN_STOCK' | 'PARTIAL' | 'DEFICIT';
  unit_price: number;
  total_deficit_cost: number;
}

export interface StockSummary {
  total_items: number;
  fully_in_stock: number;
  partial_stock: number;
  full_deficit: number;
  in_stock_covered_value: number;
  total_required_cost: number;
  total_deficit_cost: number;
}

export interface StockCheck {
  summary: StockSummary;
  items: Record<string, StockItem>;
}

export interface PurchaseOrderItem {
  code: string;
  name: string;
  unit: string;
  required_quantity: number;
  order_quantity: number;
  unit_price_kzt: number;
  total_amount_kzt: number;
}

export interface PurchaseOrder {
  order_id: string;
  supplier_id: string;
  supplier_name: string;
  supplier_bin?: string;
  supplier_city?: string;
  items: PurchaseOrderItem[];
  total_amount_kzt: number;
  priority: 'URGENT' | 'NORMAL';
  lead_time_days: number;
  payment_terms: string;
  created_at: string;
  // Compatibility fields if single item representation
  code?: string;
  name?: string;
  unit?: string;
  required_quantity?: number;
  order_quantity?: number;
}

export interface TaskResult {
  task: string;
  selected_tender?: Tender | null;
  tenders?: Tender[];
  work_list: ABCWork[];
  materials_list: ABCMaterial[];
  stock_check: StockCheck;
  purchase_orders: PurchaseOrder[];
  executive_summary?: string;
  visited_nodes?: string[];
  current_agent?: string;
  error?: string;
}

export interface TaskItem {
  task_id: string;
  status: TaskStatusType;
  progress: number;
  current_agent?: string;
  message?: string;
  result?: TaskResult;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskRequest {
  task: string;
  region?: string;
  budget_max?: number;
}

export interface StreamEvent {
  event: 'pipeline_start' | 'node_start' | 'node_complete' | 'thought' | 'pipeline_complete' | 'error';
  node?: string;
  step_index?: number;
  total_steps?: number;
  agent_title?: string;
  message?: string;
  status?: string;
  data?: Record<string, any>;
  state?: TaskResult;
  timestamp?: string;
}

export interface TerminalLog {
  id: string;
  timestamp: string;
  node: string;
  agentName: string;
  message: string;
  level: 'info' | 'success' | 'warning' | 'error' | 'thought';
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sender?: 'user' | 'coo' | 'procurement' | 'pto' | 'supply';
  senderTitle?: string;
  timestamp: string;
  thought?: string;
  state?: TaskResult;
  suggestions?: string[];
  isStreaming?: boolean;
}

export interface ChatRequestPayload {
  message: string;
  history?: Array<{
    role: string;
    content: string;
    sender?: string;
  }>;
  task_id?: string;
  current_state?: TaskResult;
}

export interface ChatResponsePayload {
  response: string;
  sender: string;
  sender_title: string;
  thought?: string;
  state?: TaskResult;
  suggestions: string[];
}
