import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield, ArrowRight, User, Stethoscope } from "lucide-react";

const Register = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState<"patient" | "pharmacist">("patient");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [dob, setDob] = useState("");
  const [pharmacistCode, setPharmacistCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const success = await register({ name, email, password, role, dateOfBirth: dob, pharmacistCode });
    setLoading(false);
    if (success) {
      navigate("/dashboard");
    } else {
      setError(role === "pharmacist" ? "Invalid pharmacist registration code." : "Registration failed.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-background">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-xl gradient-primary flex items-center justify-center mx-auto mb-4">
            <Shield className="w-7 h-7 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold text-foreground">Create your account</h1>
          <p className="text-muted-foreground mt-1">Join Dhanvan-SageAI pharmacy platform</p>
        </div>

        {/* Role selector */}
        <div className="grid grid-cols-2 gap-3 mb-8">
          <button
            type="button"
            onClick={() => setRole("patient")}
            className={`p-4 rounded-xl border-2 transition-all text-left ${role === "patient" ? "border-primary bg-secondary" : "border-border bg-card hover:border-muted-foreground/30"}`}
          >
            <User className={`w-5 h-5 mb-2 ${role === "patient" ? "text-primary" : "text-muted-foreground"}`} />
            <span className="text-sm font-semibold text-foreground block">Patient</span>
            <span className="text-xs text-muted-foreground">Order medicines & track refills</span>
          </button>
          <button
            type="button"
            onClick={() => setRole("pharmacist")}
            className={`p-4 rounded-xl border-2 transition-all text-left ${role === "pharmacist" ? "border-primary bg-secondary" : "border-border bg-card hover:border-muted-foreground/30"}`}
          >
            <Stethoscope className={`w-5 h-5 mb-2 ${role === "pharmacist" ? "text-primary" : "text-muted-foreground"}`} />
            <span className="text-sm font-semibold text-foreground block">Pharmacist</span>
            <span className="text-xs text-muted-foreground">Manage inventory & approvals</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Full Name</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your full name" required />
          </div>
          <div className="space-y-2">
            <Label>Email</Label>
            <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="your@email.de" required />
          </div>
          <div className="space-y-2">
            <Label>Password</Label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Minimum 8 characters" required minLength={8} />
          </div>
          {role === "patient" && (
            <div className="space-y-2">
              <Label>Date of Birth</Label>
              <Input type="date" value={dob} onChange={(e) => setDob(e.target.value)} required />
            </div>
          )}
          {role === "pharmacist" && (
            <div className="space-y-2">
              <Label>Pharmacist Registration Code</Label>
              <Input type="password" value={pharmacistCode} onChange={(e) => setPharmacistCode(e.target.value)} placeholder="Enter your authorization code" required />
            </div>
          )}
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full gradient-primary text-primary-foreground" disabled={loading}>
            {loading ? "Creating account..." : "Create Account"}
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <button onClick={() => navigate("/login")} className="text-primary font-medium hover:underline">
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
};

export default Register;
