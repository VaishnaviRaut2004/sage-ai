// Type definitions for Dhanvan-SageAI pharmacy system
// Live data is fetched from the backend API — these types are used for TypeScript safety.

export interface Medicine {
  product_id: string;
  name: string;
  pzn: string;
  price: number;
  units_per_pack: number;
  package_size_raw: string;
  description: string;
  stock_level: number;
  prescription_required: boolean;
  reorder_threshold: number;
}

export interface Patient {
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  email: string;
  role: "patient";
  has_valid_prescription: boolean;
  total_orders?: number;
  total_spend?: number;
}

export interface Order {
  order_id: string;
  patient_id: string;
  patient_name: string;
  medicine_name: string;
  product_id: string;
  pzn: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  dosage_frequency: string;
  purchase_date: string;
  prescription_required: boolean;
  prescription_image_url?: string;
  status: "pending" | "approved" | "fulfilled" | "rejected";
  delivery_address: {
    street: string;
    city: string;
    postal_code: string;
    country: string;
  };
  payment_info: {
    method: "card" | "insurance" | "cash";
    status: "paid" | "pending";
  };
  invoice_id?: string;
  langsmith_trace_id?: string;
  langsmith_trace_url?: string;
  created_at: string;
}

export interface RefillAlert {
  alert_id: string;
  patient_id: string;
  patient_name: string;
  medicine_name: string;
  expected_runout_date: string;
  days_remaining: number;
  last_purchase_date: string;
  notified: boolean;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "agent";
  agent_name?: string;
  text: string;
  timestamp: string;
  order_card?: Order;
  type?: "text" | "order_confirmation" | "alert" | "error";
}
