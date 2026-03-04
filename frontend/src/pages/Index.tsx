import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Shield, MessageSquare, Brain, Pill, FileText, Mic, ArrowRight, Zap, Eye, Bell } from "lucide-react";

const Index = () => {
  const navigate = useNavigate();

  const features = [
    { icon: MessageSquare, title: "Natural Conversations", description: "Chat naturally — our AI understands your medicine needs from plain language" },
    { icon: Brain, title: "5-Agent Pipeline", description: "Every request flows through specialized agents: conversation, pharmacy, inventory, prediction & action" },
    { icon: Mic, title: "Voice Ordering", description: "Speak your order — Web Speech API captures and processes voice commands" },
    { icon: FileText, title: "Prescription AI", description: "Upload prescription images — GPT-4o Vision extracts medicines automatically" },
    { icon: Bell, title: "Proactive Refills", description: "AI predicts when you'll run out and alerts you before it happens" },
    { icon: Eye, title: "Full Observability", description: "Every decision traced in LangSmith — complete audit trail for compliance" },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <header className="relative overflow-hidden">
        <div className="gradient-hero min-h-[85vh] flex items-center relative">
          <div className="absolute inset-0 opacity-[0.04]">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="absolute rounded-full border border-primary-foreground"
                style={{
                  width: `${300 + i * 150}px`,
                  height: `${300 + i * 150}px`,
                  top: "45%",
                  left: "55%",
                  transform: "translate(-50%, -50%)",
                }}
              />
            ))}
          </div>

          <div className="max-w-7xl mx-auto px-6 py-20 relative z-10">
            <div className="max-w-2xl">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl gradient-primary flex items-center justify-center shadow-elevated">
                  <Shield className="w-6 h-6 text-primary-foreground" />
                </div>
                <div className="h-px flex-1 max-w-[80px] bg-primary-foreground/20" />
                <span className="text-primary-foreground/50 text-sm font-medium tracking-wider uppercase">Autonomous Pharmacy AI</span>
              </div>

              <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold text-primary-foreground leading-[1.05] tracking-tight mb-6">
                Dhanvan
                <span className="block text-primary-foreground/60">SageAI</span>
              </h1>

              <p className="text-lg text-primary-foreground/60 leading-relaxed mb-10 max-w-lg">
                Your digital expert pharmacist that never sleeps. Intelligent prescriptions, proactive refills, and complete pharmacy automation — powered by a 5-agent AI pipeline.
              </p>

              <div className="flex flex-wrap gap-4">
                <Button
                  onClick={() => navigate("/login")}
                  className="gradient-primary text-primary-foreground px-8 h-12 text-base font-semibold rounded-xl shadow-elevated hover:opacity-90 transition-opacity"
                >
                  Get Started <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate("/login")}
                  className="border-primary-foreground/20 text-primary-foreground bg-transparent hover:bg-primary-foreground/5 px-8 h-12 text-base rounded-xl"
                >
                  View Demo
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Stats */}
      <section className="max-w-7xl mx-auto px-6 -mt-16 relative z-20">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { value: "5", label: "AI Agents", icon: Zap },
            { value: "52", label: "Medicines", icon: Pill },
            { value: "51", label: "Patient Records", icon: FileText },
            { value: "24/7", label: "Availability", icon: Shield },
          ].map((stat) => (
            <div key={stat.label} className="bg-card border border-border rounded-xl p-5 shadow-card text-center">
              <stat.icon className="w-5 h-5 text-primary mx-auto mb-2" />
              <p className="text-2xl font-bold text-foreground">{stat.value}</p>
              <p className="text-xs text-muted-foreground mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-foreground mb-3">Intelligent Pharmacy, Reimagined</h2>
          <p className="text-muted-foreground max-w-lg mx-auto">Every decision made by a named, observable AI agent — not hardcoded logic.</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <div key={feature.title} className="bg-card border border-border rounded-xl p-6 shadow-card hover:shadow-elevated transition-all group">
              <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center mb-4 group-hover:gradient-primary transition-all">
                <feature.icon className="w-5 h-5 text-secondary-foreground group-hover:text-primary-foreground transition-colors" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Agent Pipeline Visual */}
      <section className="bg-muted border-y border-border py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-2xl font-bold text-foreground text-center mb-12">The 5-Agent Pipeline</h2>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {[
              { name: "User", color: "bg-foreground text-background" },
              { name: "Conversation", color: "gradient-primary text-primary-foreground" },
              { name: "Pharmacy Design", color: "gradient-primary text-primary-foreground" },
              { name: "Inventory", color: "gradient-primary text-primary-foreground" },
              { name: "Prediction", color: "gradient-primary text-primary-foreground" },
              { name: "Action", color: "gradient-accent text-accent-foreground" },
              { name: "Database", color: "bg-foreground text-background" },
            ].map((node, i) => (
              <div key={node.name} className="flex items-center gap-3">
                <div className={`px-4 py-2.5 rounded-xl text-sm font-semibold ${node.color}`}>
                  {node.name}
                </div>
                {i < 6 && <ArrowRight className="w-4 h-4 text-muted-foreground" />}
              </div>
            ))}
          </div>
          <p className="text-center text-sm text-muted-foreground mt-8">
            Named after <strong>Dhanvantari (धन्वन्)</strong> — the Hindu god of medicine and Ayurveda
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-6 py-12 text-center">
        <p className="text-sm text-muted-foreground">
          Dhanvan-SageAI — LangGraph + GPT-4o + React · Built for hackathon demonstration
        </p>
      </footer>
    </div>
  );
};

export default Index;
