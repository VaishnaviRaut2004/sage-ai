import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useVoice } from "@/hooks/useVoice";
import { Send, Mic, MicOff, Upload, FileText, Package, Bell, User, LogOut, Shield, ChevronRight, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useNavigate } from "react-router-dom";
import { PaymentInterface } from "@/components/PaymentInterface";

interface ChatMessage {
  id: string;
  sender: "user" | "agent";
  agent_name?: string;
  text: string;
  timestamp: string;
  type?: "text" | "order_confirmation" | "alert" | "error";
  order_card?: any;
}

interface Order {
  order_id: string;
  patient_id: string;
  patient_name: string;
  medicine_name: string;
  quantity: number;
  total_price: number;
  purchase_date: string;
  status: string;
  invoice_id?: string;
}

interface RefillAlert {
  alert_id: string;
  patient_id: string;
  medicine_name: string;
  expected_runout_date: string;
  days_remaining: number;
}

const PatientDashboard = () => {
  const { user, logout, apiHeaders } = useAuth();
  const navigate = useNavigate();
  const { isRecording, transcript, interimText, startRecording, stopRecording, speak } = useVoice();
  const [activeTab, setActiveTab] = useState<"chat" | "orders" | "alerts" | "profile">("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "agent",
      agent_name: "Conversation Agent",
      text: `Hello ${user?.name ?? "there"}! 👋 I'm your pharmacy assistant. I can help you order medicines, check refill status, or upload prescriptions. How can I help you today?`,
      timestamp: new Date().toISOString(),
      type: "text",
    },
  ]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [myOrders, setMyOrders] = useState<Order[]>([]);
  const [myAlerts, setMyAlerts] = useState<RefillAlert[]>([]);
  const [payingOrderId, setPayingOrderId] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Voice transcript auto-fill (final result)
  useEffect(() => {
    if (transcript) {
      setInput(transcript);
    }
  }, [transcript]);

  // Show interim text in input while speaking (real-time feedback)
  useEffect(() => {
    if (isRecording && interimText) {
      setInput(interimText);
    }
  }, [interimText, isRecording]);

  // Fetch orders and alerts on mount
  useEffect(() => {
    fetchOrders();
    fetchAlerts();
  }, []);

  const fetchOrders = async () => {
    try {
      const res = await fetch("/api/orders", { headers: apiHeaders() });
      if (res.ok) {
        const data = await res.json();
        setMyOrders(data);
      }
    } catch (err) { console.error("Failed to fetch orders:", err); }
  };

  const fetchAlerts = async () => {
    try {
      const res = await fetch("/api/refills/alerts", { headers: apiHeaders() });
      if (res.ok) {
        const data = await res.json();
        setMyAlerts(data);
      }
    } catch (err) { console.error("Failed to fetch alerts:", err); }
  };

  const sendChatMessage = async (userMessage: string) => {
    setIsProcessing(true);

    // Show "thinking" indicator
    const thinkingMsg: ChatMessage = {
      id: `thinking-${Date.now()}`,
      sender: "agent",
      agent_name: "Pipeline",
      text: "Processing through agent pipeline...",
      timestamp: new Date().toISOString(),
      type: "text",
    };
    setMessages((prev) => [...prev, thinkingMsg]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: apiHeaders(),
        body: JSON.stringify({
          message: userMessage,
          session_id: `session-${user?.patient_id || "anon"}`,
          patient_id: user?.patient_id || "",
        }),
      });

      // Remove thinking message
      setMessages((prev) => prev.filter((m) => m.id !== thinkingMsg.id));

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: "Unknown error" }));
        const errorMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          sender: "agent",
          agent_name: "System",
          text: `Error: ${errData.detail || "Failed to process request"}`,
          timestamp: new Date().toISOString(),
          type: "error",
        };
        setMessages((prev) => [...prev, errorMsg]);
        setIsProcessing(false);
        return;
      }

      const data = await res.json();

      // Agent reply
      const agentMsg: ChatMessage = {
        id: `agent-${Date.now()}`,
        sender: "agent",
        agent_name: data.intent === "ordering" ? "Action Agent" : "Conversation Agent",
        text: data.reply,
        timestamp: new Date().toISOString(),
        type: "text",
      };
      setMessages((prev) => [...prev, agentMsg]);

      // Speak the agent's reply aloud (Text-to-Speech)
      const cleanReply = data.reply?.replace(/\*\*/g, '').replace(/[#_~`]/g, '').replace(/\[.*?\]\(.*?\)/g, '').trim();
      if (cleanReply) speak(cleanReply);

      // If there's a trace link, show it
      if (data.trace_url) {
        const traceMsg: ChatMessage = {
          id: `trace-${Date.now()}`,
          sender: "agent",
          agent_name: "LangSmith",
          text: `🔗 Agent trace: ${data.trace_url}`,
          timestamp: new Date().toISOString(),
          type: "text",
        };
        setMessages((prev) => [...prev, traceMsg]);
      }

      // If an order was placed, show confirmation card and refresh orders
      if (data.intent === "ordering" && data.order_draft?.medicine) {
        const orderCard: ChatMessage = {
          id: `order-${Date.now()}`,
          sender: "agent",
          agent_name: "Action Agent",
          text: "",
          timestamp: new Date().toISOString(),
          type: "order_confirmation",
          order_card: {
            order_id: data.order_id || `ORD-${Date.now()}`,
            medicine_name: data.order_draft.medicine,
            quantity: data.order_draft.quantity || 1,
            total_price: (data.order_draft.unit_price || 0) * (data.order_draft.quantity || 1),
            delivery_address: { city: "Latur" },
            invoice_id: data.order_id,
          },
        };
        setMessages((prev) => [...prev, orderCard]);
        fetchOrders();
      }
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== thinkingMsg.id));
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        sender: "agent",
        agent_name: "System",
        text: "Connection error. Make sure the backend server is running.",
        timestamp: new Date().toISOString(),
        type: "error",
      };
      setMessages((prev) => [...prev, errorMsg]);
    }

    setIsProcessing(false);
  };

  const handleSend = () => {
    if (!input.trim() || isProcessing) return;
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: input,
      timestamp: new Date().toISOString(),
      type: "text",
    };
    setMessages((prev) => [...prev, userMsg]);
    const msg = input;
    setInput("");
    sendChatMessage(msg);
  };

  const toggleVoice = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handlePrescriptionUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setIsProcessing(true);
    const uploadMsg: ChatMessage = {
      id: `upload-${Date.now()}`,
      sender: "agent",
      agent_name: "Pharmacy Design Agent",
      text: "Analyzing your prescription image with AI Vision...",
      timestamp: new Date().toISOString(),
      type: "text",
    };
    setMessages((prev) => [...prev, uploadMsg]);

    try {
      const headers: Record<string, string> = {};
      const token = localStorage.getItem("dhanvan_token");
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch("/api/prescriptions/upload", {
        method: "POST",
        headers,
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        const medsText = data.medicines?.map((m: any) => `${m.name} (${m.dosage}, qty: ${m.quantity})`).join(", ") || "None detected";
        const resultMsg: ChatMessage = {
          id: `rx-result-${Date.now()}`,
          sender: "agent",
          agent_name: "Pharmacy Design Agent",
          text: `✅ Prescription processed successfully!\n\n**Doctor:** ${data.doctor_name || "Unknown"}\n**Medicines:** ${medsText}\n**Valid:** ${data.is_valid_prescription ? "Yes" : "Needs review"}\n\nClick **"Order All"** below to order all medicines at once, or order individually through chat.`,
          timestamp: new Date().toISOString(),
          type: "text",
        };
        setMessages((prev) => [...prev, resultMsg]);

        // Auto-trigger batch order for all prescription medicines
        if (data.medicines?.length > 0 && data.is_valid_prescription) {
          try {
            const orderRes = await fetch("/api/prescriptions/order-all", {
              method: "POST",
              headers,
            });
            if (orderRes.ok) {
              const orderData = await orderRes.json();
              const ordersList = orderData.orders?.map((o: any) => `• ${o.medicine} — Qty: ${o.quantity} — ₹${o.unit_price?.toFixed(2) || '0.00'} × ${o.quantity} = **₹${o.total?.toFixed(2) || '0.00'}**`).join("\n") || "";
              const grandTotal = orderData.grand_total?.toFixed(2) || "0.00";
              const invoiceId = orderData.consolidated_invoice_id;
              const batchMsg: ChatMessage = {
                id: `batch-order-${Date.now()}`,
                sender: "agent",
                agent_name: "Action Agent",
                text: `🎉 **All ${orderData.orders?.length} medicines ordered!**\n\n${ordersList}\n\n**Grand Total: ₹${grandTotal}** (+ 5% GST)\nPrescribed by Dr. ${orderData.doctor || "Unknown"}\n\n📄 [Download Invoice](#invoice-${invoiceId})`,
                timestamp: new Date().toISOString(),
                type: "text",
                order_card: invoiceId ? { invoice_id: invoiceId } : undefined,
              };
              setMessages((prev) => [...prev, batchMsg]);
              fetchOrders();
            }
          } catch (batchErr) {
            console.error("Batch order error:", batchErr);
          }
        }
      } else {
        const errMsg: ChatMessage = {
          id: `rx-error-${Date.now()}`,
          sender: "agent",
          agent_name: "System",
          text: "Failed to process prescription image. Please try again with a clearer photo.",
          timestamp: new Date().toISOString(),
          type: "error",
        };
        setMessages((prev) => [...prev, errMsg]);
      }
    } catch (err) {
      console.error("Upload error:", err);
    }
    setIsProcessing(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const downloadInvoice = async (invoiceId: string | undefined) => {
    if (!invoiceId) return;
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

  const sideNavItems = [
    { id: "chat" as const, icon: Send, label: "Chat" },
    { id: "orders" as const, icon: Package, label: "My Orders" },
    { id: "alerts" as const, icon: Bell, label: "Refill Alerts", badge: myAlerts.length },
    { id: "profile" as const, icon: User, label: "Profile" },
  ];

  return (
    <div className="flex h-screen bg-background">
      {/* Hidden file input for prescription upload */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handlePrescriptionUpload}
      />

      {/* Sidebar */}
      <aside className="w-64 bg-sidebar text-sidebar-foreground flex flex-col border-r border-sidebar-border">
        <div className="p-5 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg gradient-primary flex items-center justify-center">
            <Shield className="w-5 h-5 text-primary-foreground" />
          </div>
          <div>
            <h2 className="font-bold text-sm text-sidebar-foreground">Dhanvan-SageAI</h2>
            <p className="text-xs text-sidebar-foreground/50">Patient Portal</p>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {sideNavItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${activeTab === item.id
                ? "bg-sidebar-accent text-sidebar-primary"
                : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                }`}
            >
              <item.icon className="w-4 h-4" />
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge && item.badge > 0 && (
                <span className="w-5 h-5 rounded-full bg-destructive text-destructive-foreground text-xs flex items-center justify-center font-medium">
                  {item.badge}
                </span>
              )}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-sidebar-border">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center text-primary-foreground text-xs font-bold">
              {user?.name?.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">{user?.name}</p>
              <p className="text-xs text-sidebar-foreground/50">{user?.patient_id}</p>
            </div>
          </div>
          <button onClick={() => { logout(); navigate("/login"); }} className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-sidebar-foreground/60 hover:bg-sidebar-accent/50 transition-colors">
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col">
        {/* Refill alert banner */}
        {myAlerts.length > 0 && activeTab === "chat" && (
          <div className="bg-warning/10 border-b border-warning/20 px-6 py-3 flex items-center gap-3 animate-slide-in-up">
            <Bell className="w-4 h-4 text-warning" />
            <span className="text-sm text-foreground">
              <strong>{myAlerts[0].medicine_name}</strong> — refill needed in <strong>{myAlerts[0].days_remaining} days</strong>
            </span>
            <button onClick={() => setInput(`I need to refill my ${myAlerts[0].medicine_name}`)} className="ml-auto text-xs font-medium text-primary hover:underline">
              Order Refill
            </button>
          </div>
        )}

        {activeTab === "chat" && (
          <>
            {/* Chat messages */}
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"} animate-slide-in-up`}>
                  {msg.type === "order_confirmation" && msg.order_card ? (
                    <div className="max-w-md w-full bg-card border border-border rounded-xl shadow-card overflow-hidden">
                      <div className="gradient-primary px-4 py-3 flex items-center gap-2">
                        <Package className="w-4 h-4 text-primary-foreground" />
                        <span className="text-sm font-semibold text-primary-foreground">Order Confirmed</span>
                      </div>
                      <div className="p-4 space-y-3">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Medicine</span>
                          <span className="font-medium text-foreground">{msg.order_card.medicine_name}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Quantity</span>
                          <span className="font-medium text-foreground">{msg.order_card.quantity}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Total</span>
                          <span className="font-bold text-foreground">₹{msg.order_card.total_price?.toFixed(2) || "0.00"}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Delivery</span>
                          <span className="font-medium text-foreground">{msg.order_card.delivery_address?.city || "Latur"}</span>
                        </div>
                        <div className="pt-2 border-t border-border flex items-center justify-between">
                          <Badge variant="outline" className="text-xs">{msg.order_card.order_id}</Badge>
                          <Button variant="ghost" size="sm" className="text-primary text-xs gap-1" onClick={() => downloadInvoice(msg.order_card.invoice_id)}>
                            <Download className="w-3 h-3" /> Invoice
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className={`max-w-lg px-4 py-3 rounded-2xl ${msg.sender === "user"
                      ? "bg-chat-user text-primary-foreground rounded-br-md"
                      : msg.type === "error"
                        ? "bg-destructive/10 text-destructive rounded-bl-md border border-destructive/20"
                        : "bg-chat-agent text-chat-agent-foreground rounded-bl-md"
                      }`}>
                      {msg.agent_name && (
                        <span className="text-xs font-semibold opacity-70 block mb-1">{msg.agent_name}</span>
                      )}
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text?.replace(/📄 \[Download Invoice\].*$/m, '').trim()}</p>
                      {msg.order_card?.invoice_id && (
                        <Button variant="outline" size="sm" className="mt-3 gap-1.5 text-xs w-full" onClick={() => downloadInvoice(msg.order_card!.invoice_id)}>
                          <Download className="w-3.5 h-3.5" /> Download Full Prescription Invoice (PDF)
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              ))}
              {isProcessing && (
                <div className="flex justify-start animate-fade-in">
                  <div className="bg-chat-agent px-4 py-3 rounded-2xl rounded-bl-md">
                    <div className="flex gap-1.5">
                      {[0, 1, 2].map((i) => (
                        <div key={i} className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-pulse-soft" style={{ animationDelay: `${i * 0.2}s` }} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input bar */}
            <div className="border-t border-border px-6 py-4 bg-card">
              <div className="flex items-center gap-3 max-w-3xl mx-auto">
                <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-primary shrink-0" onClick={() => fileInputRef.current?.click()}>
                  <Upload className="w-5 h-5" />
                </Button>
                <div className="flex-1 relative">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    placeholder="Ask about medicines, order refills, or upload a prescription..."
                    className="pr-12 bg-muted border-0 rounded-xl h-11"
                    disabled={isProcessing}
                  />
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleVoice}
                  className={`shrink-0 ${isRecording ? "text-destructive animate-pulse-soft" : "text-muted-foreground hover:text-primary"}`}
                >
                  {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </Button>
                <Button onClick={handleSend} size="icon" className="gradient-primary text-primary-foreground shrink-0 rounded-xl" disabled={isProcessing || !input.trim()}>
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              {isRecording && (
                <div className="flex items-center justify-center gap-1 mt-3">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="w-1 bg-destructive rounded-full animate-wave" style={{ height: "16px", animationDelay: `${i * 0.15}s` }} />
                  ))}
                  <span className="text-xs text-destructive ml-2 font-medium">Listening...</span>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === "orders" && (
          <div className="flex-1 overflow-y-auto p-6">
            <h2 className="text-xl font-bold text-foreground mb-6">My Orders</h2>
            <div className="space-y-4">
              {myOrders.length === 0 ? (
                <div className="text-center py-20 text-muted-foreground">
                  <Package className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No orders yet. Start ordering through the chat!</p>
                </div>
              ) : (
                myOrders.map((order) => (
                  <div key={order.order_id} className="bg-card border border-border rounded-xl p-5 shadow-card hover:shadow-elevated transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-foreground">{order.medicine_name}</h3>
                        <p className="text-sm text-muted-foreground">{order.order_id}</p>
                      </div>
                      <Badge variant={order.status === "fulfilled" ? "default" : order.status === "pending" ? "secondary" : "outline"}>
                        {order.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Qty</span>
                        <p className="font-medium text-foreground">{order.quantity}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Total</span>
                        <p className="font-medium text-foreground">₹{order.total_price?.toFixed(2)}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Date</span>
                        <p className="font-medium text-foreground">{new Date(order.purchase_date).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <div className="flex justify-between items-center mt-3">
                      {order.invoice_id && (
                        <Button variant="ghost" size="sm" className="text-primary text-xs gap-1" onClick={() => downloadInvoice(order.invoice_id!)}>
                          <Download className="w-3 h-3" /> Download Invoice
                        </Button>
                      )}
                      {order.status === "pending" && (
                        <Button size="sm" onClick={() => setPayingOrderId(order.order_id)} className="text-xs">
                          Pay Now
                        </Button>
                      )}
                    </div>
                    {payingOrderId === order.order_id && (
                      <div className="mt-4 border-t pt-4">
                        <PaymentInterface
                          defaultAmount={order.total_price}
                          onCancel={() => setPayingOrderId(null)}
                          onPaymentComplete={async () => {
                            try {
                              const res = await fetch(`/api/orders/${order.order_id}/pay`, {
                                method: 'POST',
                                headers: apiHeaders()
                              });
                              if (res.ok) {
                                setPayingOrderId(null);
                                fetchOrders();
                              }
                            } catch (err) { }
                          }}
                        />
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === "alerts" && (
          <div className="flex-1 overflow-y-auto p-6">
            <h2 className="text-xl font-bold text-foreground mb-6">Refill Alerts</h2>
            <div className="space-y-4">
              {myAlerts.length === 0 ? (
                <div className="text-center py-20 text-muted-foreground">
                  <Bell className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No active refill alerts</p>
                </div>
              ) : (
                myAlerts.map((alert) => (
                  <div key={alert.alert_id} className={`bg-card border rounded-xl p-5 shadow-card ${alert.days_remaining <= 3 ? "border-destructive/30" : "border-warning/30"}`}>
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${alert.days_remaining <= 3 ? "bg-destructive/10" : "bg-warning/10"}`}>
                        <Bell className={`w-5 h-5 ${alert.days_remaining <= 3 ? "text-destructive" : "text-warning"}`} />
                      </div>
                      <div>
                        <h3 className="font-semibold text-foreground">{alert.medicine_name}</h3>
                        <p className="text-sm text-muted-foreground">Runs out: {new Date(alert.expected_runout_date).toLocaleDateString()}</p>
                      </div>
                      <Badge className={`ml-auto ${alert.days_remaining <= 3 ? "bg-destructive text-destructive-foreground" : "bg-warning text-warning-foreground"}`}>
                        {alert.days_remaining} days left
                      </Badge>
                    </div>
                    <Button size="sm" className="gradient-primary text-primary-foreground gap-1" onClick={() => { setActiveTab("chat"); setInput(`I need to refill my ${alert.medicine_name}`); }}>
                      Order Refill <ChevronRight className="w-3 h-3" />
                    </Button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === "profile" && (
          <div className="flex-1 overflow-y-auto p-6">
            <h2 className="text-xl font-bold text-foreground mb-6">My Profile</h2>
            <div className="bg-card border border-border rounded-xl p-6 shadow-card max-w-lg">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-full gradient-primary flex items-center justify-center text-primary-foreground text-xl font-bold">
                  {user?.name?.charAt(0)}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-foreground">{user?.name}</h3>
                  <p className="text-sm text-muted-foreground">{user?.email}</p>
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between py-2 border-b border-border">
                  <span className="text-muted-foreground text-sm">Patient ID</span>
                  <span className="font-mono text-sm text-foreground">{user?.patient_id}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-border">
                  <span className="text-muted-foreground text-sm">Role</span>
                  <Badge variant="secondary">Patient</Badge>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-muted-foreground text-sm">Orders</span>
                  <span className="font-medium text-sm text-foreground">{myOrders.length}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default PatientDashboard;
