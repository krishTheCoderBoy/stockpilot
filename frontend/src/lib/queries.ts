export interface Category {
  id: string;
  name: string;
  parent_category_id: string | null;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  description: string | null;
  category_id: string | null;
  unit_price: string;
  unit_of_measure: string;
  reorder_point: string;
  min_order_quantity: string;
  max_stock_level: string | null;
  default_supplier_id: string | null;
  is_active: boolean;
}

export interface Warehouse {
  id: string;
  code: string;
  name: string;
  city: string;
  state: string;
  country: string;
  manager_id: string | null;
  capacity: string | null;
  warehouse_type: "MAIN" | "REGIONAL" | "TRANSIT";
  is_active: boolean;
}

export interface InventoryRow {
  id: string;
  product_id: string;
  warehouse_id: string;
  on_hand_quantity: string;
  reserved_quantity: string;
  available_quantity: string;
  average_unit_cost: string;
  safety_stock_override: string | null;
  last_movement_at: string | null;
}

export interface Movement {
  id: string;
  product_id: string;
  warehouse_id: string;
  movement_type: "RECEIVE" | "ISSUE" | "ADJUSTMENT_INCREASE" | "ADJUSTMENT_DECREASE" | "TRANSFER_OUT" | "TRANSFER_IN" | "DAMAGED" | "RETURNED";
  quantity: string;
  unit_cost: string | null;
  reference_type: "MANUAL" | "PURCHASE_ORDER" | "TRANSFER";
  reference_id: string | null;
  performed_by: string | null;
  notes: string | null;
  created_at: string;
}


export interface Supplier {
  id: string;
  code: string;
  name: string;
  contact_person: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  lead_time_days: number | null;
  is_active: boolean;
}

export interface POItem {
  id: string;
  product_id: string;
  ordered_quantity: string;
  received_quantity: string;
  unit_price: string;
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  supplier_id: string;
  warehouse_id: string;
  status: "DRAFT" | "SUBMITTED" | "APPROVED" | "ORDERED" | "PARTIALLY_RECEIVED" | "RECEIVED" | "CLOSED" | "CANCELLED";
  created_by: string;
  approved_by: string | null;
  notes: string | null;
  expected_date: string | null;
  created_at: string;
  updated_at: string;
  items: POItem[];
}


export type RiskLevel = "OK" | "LOW" | "STOCKOUT_RISK";

export interface Recommendation {
  product_id: string;
  sku: string;
  product_name: string;
  warehouse_id: string | null;
  supplier_id: string | null;
  supplier_name: string | null;
  lead_time_days: number;
  lead_time_source: "supplier" | "default";
  review_period_days: number;
  horizon_days: number;
  on_hand: string;
  reserved: string;
  current_available: string;
  incoming: string;
  safety_stock: string;
  safety_stock_source: "inventory_override" | "product_reorder_point";
  avg_daily_demand: string;
  forecast_demand: string;
  forecast_lower: string;
  forecast_upper: string;
  min_order_multiple: string;
  recommended_order: string;
  unit_price: string;
  days_of_cover: string | null;
  risk: RiskLevel;
  forecast_mode: "auto" | "rules";
  model_used: string;
  model_label: string;
  model_reason: string;
  history_length: number;
  backtest_mae: string | null;
  explanation: string;
  reasons: string[];
}

export interface RecommendationPage {
  total: number;
  skip: number;
  limit: number;
  items: Recommendation[];
}

export interface PlanningSummary {
  total_products: number;
  recommended_purchases: number;
  stockout_risk: number;
  low: number;
  ok: number;
}

export interface ForecastResponse {
  product_id: string;
  warehouse_id: string | null;
  model_used: string;
  model_label: string;
  model_reason: string;
  history_length: number;
  horizon_days: number;
  total_forecast_demand: string;
  total_lower: string;
  total_upper: string;
  backtest: {
    holdout_days: number;
    mae: string;
    mape: string | null;
    baseline_mae: string;
    baseline_mape: string | null;
  } | null;
  history: { bucket_start: string; quantity: string }[];
  forecast: { bucket_start: string; mean: string; lower: string; upper: string }[];
  generated_at: string;
}
