import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield, Heart, ArrowRight } from "lucide-react";

const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const success = await login(email, password);
    setLoading(false);
    if (success) {
      navigate("/dashboard");
    } else {
      setError("Invalid credentials. Try the demo accounts below.");
    }
  };

  const fillDemo = (role: "patient" | "pharmacist") => {
    if (role === "patient") {
      setEmail("patient@dhanvan.ai");
      setPassword("patient123");
    } else {
      setEmail("pharmacist@dhanvan.ai");
      setPassword("pharma123");
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-1/2 gradient-hero items-center justify-center p-12 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="absolute rounded-full border border-primary-foreground/20"
              style={{
                width: `${200 + i * 120}px`,
                height: `${200 + i * 120}px`,
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
              }}
            />
          ))}
        </div>
        <div className="relative z-10 text-center max-w-md">
          <div className="w-20 h-20 rounded-2xl gradient-primary flex items-center justify-center mx-auto mb-8 shadow-elevated">
            <Shield className="w-10 h-10 text-primary-foreground" />
          </div>
          <h1 className="text-4xl font-bold text-primary-foreground mb-4 tracking-tight">
            Dhanvan-SageAI
          </h1>
          <p className="text-primary-foreground/70 text-lg leading-relaxed">
            Autonomous Pharmacy Intelligence — your digital expert pharmacist that never sleeps.
          </p>
          <div className="mt-8 flex items-center justify-center gap-2 text-primary-foreground/50 text-sm">
            <Heart className="w-4 h-4" />
            <span>Named after Dhanvantari, the guardian of health</span>
          </div>
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-8 text-center">
            <div className="w-14 h-14 rounded-xl gradient-primary flex items-center justify-center mx-auto mb-4">
              <Shield className="w-7 h-7 text-primary-foreground" />
            </div>
            <h1 className="text-2xl font-bold text-foreground">Dhanvan-SageAI</h1>
          </div>

          <h2 className="text-2xl font-bold text-foreground mb-2">Welcome back</h2>
          <p className="text-muted-foreground mb-8">Sign in to access your pharmacy dashboard</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="your@email.de" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full gradient-primary text-primary-foreground" disabled={loading}>
              {loading ? "Signing in..." : "Sign In"}
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </form>

          <div className="mt-8 p-4 rounded-xl bg-muted border border-border">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Demo Accounts</p>
            <div className="space-y-2">
              <button onClick={() => fillDemo("patient")} className="w-full text-left p-3 rounded-lg bg-card hover:bg-secondary transition-colors border border-border">
                <span className="text-sm font-medium text-foreground">Patient — Anna Müller</span>
                <span className="text-xs text-muted-foreground block">patient@dhanvan.ai / patient123</span>
              </button>
              <button onClick={() => fillDemo("pharmacist")} className="w-full text-left p-3 rounded-lg bg-card hover:bg-secondary transition-colors border border-border">
                <span className="text-sm font-medium text-foreground">Pharmacist — Dr. Karl Lehmann</span>
                <span className="text-xs text-muted-foreground block">pharmacist@dhanvan.ai / pharma123</span>
              </button>
            </div>
          </div>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <button onClick={() => navigate("/register")} className="text-primary font-medium hover:underline">
              Register here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
