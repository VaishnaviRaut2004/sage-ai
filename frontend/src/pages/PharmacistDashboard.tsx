import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Shield, LogOut, Package, Bell, Users, Pill,
  Search, Download, ExternalLink, ChevronDown, ChevronUp,
  Check, X, RefreshCw, AlertTriangle
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

type Tab = "inventory" | "orders" | "alerts" | "patients";

interface Medicine {
  product_id: string; name: string; pzn: string; price: number;
  units_per_pack: number; package_size_raw: string; stock_level: number;
  prescription_required: boolean; reorder_threshold: number;
}
interface Order {
  order_id: string; patient_id: string; patient_name: string; medicine_name: string;
  product_id: string; pzn: string; quantity: number; unit_price: number; total_price: number;
  dosage_frequency: string; purchase_date: string; prescription_required: boolean;
  status: string; delivery_address: { street: string; city: string; postal_code: string; country: string };
  payment_info: { method: string; status: string }; invoice_id?: string;
  langsmith_trace_id?: string; langsmith_trace_url?: string; created_at: string;
}
interface RefillAlert {
  alert_id: string; patient_id: string; patient_name: string; medicine_name: string;
  expected_runout_date: string; days_remaining: number; last_purchase_date: string; notified: boolean;
  _id: string;
}
interface Patient {
  patient_id: string; name: string; age: number; gender: string; email: string;
  has_valid_prescription: boolean; total_orders: number; total_spend: number;
}

const statusColors: Record<string, string> = {
  pending: "bg-warning/15 text-warning border-warning/30",
  approved: "bg-info/15 text-info border-info/30",
  fulfilled: "bg-success/15 text-success border-success/30",
  rejected: "bg-destructive/15 text-destructive border-destructive/30",
};

const PharmacistDashboard = () => {
  const { user, logout, apiHeaders } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<Tab>("inventory");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [expandedOrder, setExpandedOrder] = useState<string | null>(null);

  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [alerts, setAlerts] = useState<RefillAlert[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch all data on mount
  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    await Promise.all([fetchMedicines(), fetchOrders(), fetchAlerts(), fetchPatients()]);
    setLoading(false);
  };

  const fetchMedicines = async () => {
    try {
      const res = await fetch("/api/medicines", { headers: apiHeaders() });
      if (res.ok) setMedicines(await res.json());
    } catch (err) { console.error("Failed to fetch medicines:", err); }
  };

  const fetchOrders = async () => {
    try {
      const res = await fetch("/api/orders", { headers: apiHeaders() });
      if (res.ok) setOrders(await res.json());
    } catch (err) { console.error("Failed to fetch orders:", err); }
  };

  const fetchAlerts = async () => {
    try {
      const res = await fetch("/api/refills/alerts", { headers: apiHeaders() });
      if (res.ok) setAlerts(await res.json());
    } catch (err) { console.error("Failed to fetch alerts:", err); }
  };

  const fetchPatients = async () => {
    try {
      const res = await fetch("/api/users", { headers: apiHeaders() });
      if (res.ok) setPatients(await res.json());
    } catch (err) { console.error("Failed to fetch patients:", err); }
  };

  const filteredMedicines = medicines.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase()) || m.pzn.includes(search)
  );

  const filteredOrders = orders.filter((o) =>
    statusFilter === "all" || o.status === statusFilter
  );

  const stockBadge = (level: number, threshold: number) => {
    if (level <= threshold) return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-stock-low/15 text-stock-low"><AlertTriangle className="w-3 h-3" />{level}</span>;
    if (level <= threshold * 2.5) return <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-stock-medium/15 text-stock-medium">{level}</span>;
    return <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-stock-high/15 text-stock-high">{level}</span>;
  };

  const updateOrderStatus = async (orderId: string, status: string) => {
    try {
      const res = await fetch(`/api/orders/${orderId}/status?status=${status}`, {
        method: "PATCH",
        headers: apiHeaders(),
      });
      if (res.ok) {
        setOrders((prev) => prev.map((o) => o.order_id === orderId ? { ...o, status } : o));
      }
    } catch (err) { console.error("Failed to update order:", err); }
  };

  const triggerReorder = async (productId: string) => {
    const qtyStr = window.prompt("Enter the amount of stock to add:", "100");
    if (!qtyStr) return; // User cancelled
    const qty = parseInt(qtyStr, 10);
    if (isNaN(qty) || qty <= 0) {
      alert("Please enter a valid positive number.");
      return;
    }

    try {
      const res = await fetch(`/api/medicines/${productId}/stock/add?amount=${qty}`, {
        method: "PATCH",
        headers: apiHeaders(),
      });
      if (res.ok) {
        fetchMedicines();
      }
    } catch (err) { console.error("Failed to reorder:", err); }
  };

  const runPredictionJob = async () => {
    try {
      await fetch("/api/refills/run", { method: "POST", headers: apiHeaders() });
      fetchAlerts();
    } catch (err) { console.error("Failed to run prediction:", err); }
  };

  const notifyAlert = async (alertId: string, alertName: string) => {
    try {
      const res = await fetch(`/api/refills/alerts/${alertId}/notify`, {
        method: "POST",
        headers: apiHeaders(),
      });
      if (res.ok) {
        toast({
          title: "Alert Sent",
          description: `Successfully sent refill reminder for ${alertName}.`,
        });
        fetchAlerts();
      }
    } catch (err) {
      console.error("Failed to send alert:", err);
      toast({
        title: "Failed",
        description: "Could not send the alert. Please try again.",
        variant: "destructive",
      });
    }
  };

  const downloadInvoice = async (invoiceId: string) => {
    try {
      const res = await fetch(`/api/invoices/${invoiceId}`, { headers: apiHeaders() });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `INV-${invoiceId}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (err) { console.error("Invoice download error:", err); }
  };

  const pendingCount = orders.filter((o) => o.status === "pending").length;

  const tabs: { id: Tab; icon: typeof Pill; label: string; count?: number }[] = [
    { id: "inventory", icon: Pill, label: "Inventory", count: medicines.length },
    { id: "orders", icon: Package, label: "Orders", count: pendingCount },
    { id: "alerts", icon: Bell, label: "Refill Alerts", count: alerts.length },
    { id: "patients", icon: Users, label: "Patients", count: patients.length },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Top nav */}
      <header className="bg-card border-b border-border sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg gradient-primary flex items-center justify-center">
              <Shield className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-bold text-foreground text-sm">Dhanvan-SageAI</h1>
              <p className="text-xs text-muted-foreground">Pharmacist Admin</p>
            </div>
          </div>

          <nav className="flex items-center gap-1 bg-muted rounded-xl p-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id
                  ? "bg-card shadow-sm text-foreground"
                  : "text-muted-foreground hover:text-foreground"
                  }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
                {tab.count !== undefined && tab.count > 0 && (
                  <span className={`w-5 h-5 rounded-full text-xs flex items-center justify-center font-bold ${tab.id === "orders" && tab.count > 0 ? "bg-warning text-warning-foreground" :
                    tab.id === "alerts" ? "bg-destructive text-destructive-foreground" :
                      "bg-muted-foreground/20 text-muted-foreground"
                    }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-foreground">{user?.name}</span>
            <button onClick={() => { logout(); navigate("/login"); }} className="text-muted-foreground hover:text-foreground transition-colors">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Inventory */}
        {activeTab === "inventory" && (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-foreground">Medicine Inventory</h2>
              <div className="relative w-72">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name or PZN..." className="pl-10 bg-muted border-0 rounded-xl" />
              </div>
            </div>

            <div className="bg-card border border-border rounded-xl overflow-hidden shadow-card">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border bg-muted/50">
                      <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Medicine</th>
                      <th className="text-left px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">PZN</th>
                      <th className="text-center px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Stock</th>
                      <th className="text-center px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Reorder At</th>
                      <th className="text-right px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Price</th>
                      <th className="text-center px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Rx</th>
                      <th className="text-right px-5 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredMedicines.map((med) => (
                      <tr key={med.product_id} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                        <td className="px-5 py-4">
                          <p className="font-medium text-sm text-foreground">{med.name}</p>
                          <p className="text-xs text-muted-foreground">{med.package_size_raw}</p>
                        </td>
                        <td className="px-5 py-4 font-mono text-xs text-muted-foreground">{med.pzn}</td>
                        <td className="px-5 py-4 text-center">{stockBadge(med.stock_level, med.reorder_threshold)}</td>
                        <td className="px-5 py-4 text-center text-sm text-muted-foreground">{med.reorder_threshold}</td>
                        <td className="px-5 py-4 text-right text-sm font-medium text-foreground">₹{med.price.toFixed(2)}</td>
                        <td className="px-5 py-4 text-center">
                          {med.prescription_required ? (
                            <Badge variant="outline" className="text-xs border-destructive/40 text-destructive">Rx</Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs border-success/40 text-success">OTC</Badge>
                          )}
                        </td>
                        <td className="px-5 py-4 text-right">
                          {med.stock_level <= med.reorder_threshold && (
                            <Button variant="ghost" size="sm" className="text-xs text-primary gap-1" onClick={() => triggerReorder(med.product_id)}>
                              <RefreshCw className="w-3 h-3" /> Reorder
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Orders */}
        {activeTab === "orders" && (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-foreground">All Orders</h2>
              <div className="flex items-center gap-2 bg-muted rounded-xl p-1">
                {["all", "pending", "approved", "fulfilled", "rejected"].map((s) => (
                  <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${statusFilter === s ? "bg-card shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                      }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              {filteredOrders.map((order) => (
                <div key={order.order_id} className="bg-card border border-border rounded-xl shadow-card overflow-hidden">
                  <div className="px-5 py-4 flex items-center gap-4 cursor-pointer hover:bg-muted/20 transition-colors" onClick={() => setExpandedOrder(expandedOrder === order.order_id ? null : order.order_id)}>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="font-semibold text-sm text-foreground">{order.patient_name}</h3>
                        <span className="font-mono text-xs text-muted-foreground">{order.order_id}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">{order.medicine_name} × {order.quantity}</p>
                    </div>
                    <div className="text-right mr-4">
                      <p className="font-bold text-sm text-foreground">₹{order.total_price?.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">{new Date(order.purchase_date || order.created_at).toLocaleDateString()}</p>
                    </div>
                    <Badge variant="outline" className={`text-xs ${statusColors[order.status] || ""}`}>
                      {order.status}
                    </Badge>
                    {order.status === "pending" && (
                      <div className="flex gap-1">
                        <Button size="sm" variant="ghost" className="text-success hover:bg-success/10 h-8 w-8 p-0" onClick={(e) => { e.stopPropagation(); updateOrderStatus(order.order_id, "approved"); }}>
                          <Check className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="ghost" className="text-destructive hover:bg-destructive/10 h-8 w-8 p-0" onClick={(e) => { e.stopPropagation(); updateOrderStatus(order.order_id, "rejected"); }}>
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    )}
                    {expandedOrder === order.order_id ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
                  </div>

                  {expandedOrder === order.order_id && (
                    <div className="border-t border-border px-5 py-4 bg-muted/30 animate-slide-in-up">
                      <div className="grid grid-cols-3 gap-6 text-sm">
                        <div>
                          <h4 className="font-semibold text-foreground mb-2">Delivery</h4>
                          <p className="text-muted-foreground">{order.delivery_address?.street}</p>
                          <p className="text-muted-foreground">{order.delivery_address?.postal_code} {order.delivery_address?.city}</p>
                          <p className="text-muted-foreground">{order.delivery_address?.country}</p>
                        </div>
                        <div>
                          <h4 className="font-semibold text-foreground mb-2">Payment</h4>
                          <p className="text-muted-foreground capitalize">{order.payment_info?.method}</p>
                          <Badge variant="outline" className="text-xs mt-1">{order.payment_info?.status}</Badge>
                        </div>
                        <div>
                          <h4 className="font-semibold text-foreground mb-2">Details</h4>
                          <p className="text-muted-foreground">PZN: {order.pzn}</p>
                          <p className="text-muted-foreground">Dosage: {order.dosage_frequency}</p>
                          <p className="text-muted-foreground">Rx: {order.prescription_required ? "Yes" : "No"}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 mt-4 pt-3 border-t border-border">
                        {order.invoice_id && (
                          <Button variant="ghost" size="sm" className="text-primary text-xs gap-1" onClick={() => downloadInvoice(order.invoice_id!)}>
                            <Download className="w-3 h-3" /> Invoice
                          </Button>
                        )}
                        {order.langsmith_trace_url && (
                          <a href={order.langsmith_trace_url} target="_blank" rel="noopener noreferrer">
                            <Button variant="ghost" size="sm" className="text-info text-xs gap-1">
                              <ExternalLink className="w-3 h-3" /> LangSmith Trace
                            </Button>
                          </a>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Refill Alerts */}
        {activeTab === "alerts" && (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-foreground">Refill Alerts</h2>
              <Button variant="outline" size="sm" className="gap-2 text-sm" onClick={runPredictionJob}>
                <RefreshCw className="w-3.5 h-3.5" /> Run Prediction Job
              </Button>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {alerts.map((alert) => (
                <div key={alert.alert_id} className={`bg-card border rounded-xl p-5 shadow-card ${alert.days_remaining <= 3 ? "border-destructive/30" : "border-warning/30"}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-foreground">{alert.patient_name}</h3>
                      <p className="text-sm text-muted-foreground">{alert.patient_id}</p>
                    </div>
                    <Badge className={alert.days_remaining <= 3 ? "bg-destructive text-destructive-foreground" : "bg-warning text-warning-foreground"}>
                      {alert.days_remaining}d remaining
                    </Badge>
                  </div>
                  <div className="text-sm space-y-1 mb-4">
                    <p className="text-foreground font-medium">{alert.medicine_name}</p>
                    <p className="text-muted-foreground">Runout: {new Date(alert.expected_runout_date).toLocaleDateString()}</p>
                    <p className="text-muted-foreground">Last purchase: {new Date(alert.last_purchase_date).toLocaleDateString()}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-xs gap-1"
                      onClick={() => notifyAlert(alert._id, alert.patient_name)}
                      disabled={alert.notified}
                    >
                      <Bell className="w-3 h-3" /> {alert.notified ? "Alert Sent" : "Send Alert"}
                    </Button>
                    {alert.notified && <Badge variant="outline" className="text-xs text-success border-success/40">Notified</Badge>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Patients */}
        {activeTab === "patients" && (
          <div className="animate-fade-in">
            <h2 className="text-xl font-bold text-foreground mb-6">Patient Records</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {patients.map((p) => (
                <div key={p.patient_id} className="bg-card border border-border rounded-xl p-5 shadow-card hover:shadow-elevated transition-shadow">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-full gradient-primary flex items-center justify-center text-primary-foreground text-sm font-bold">
                      {p.name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm text-foreground">{p.name}</h3>
                      <p className="text-xs text-muted-foreground">{p.patient_id}</p>
                    </div>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Age / Gender</span>
                      <span className="text-foreground">{p.age} / {p.gender}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Orders</span>
                      <span className="text-foreground">{p.total_orders}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total Spend</span>
                      <span className="text-foreground font-medium">₹{p.total_spend?.toFixed(2) || "0.00"}</span>
                    </div>
                    <div className="flex justify-between mt-2 pt-2 border-t border-border">
                      <span className="text-muted-foreground">Valid Rx</span>
                      {p.has_valid_prescription ? (
                        <Badge variant="outline" className="text-xs text-success border-success/40">Yes</Badge>
                      ) : (
                        <Badge variant="outline" className="text-xs text-muted-foreground">No</Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PharmacistDashboard;
