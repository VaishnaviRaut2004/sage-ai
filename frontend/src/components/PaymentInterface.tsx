import { useState, lazy, Suspense } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { QrCode, Send, Loader2 } from "lucide-react";

interface PaymentInfo {
    upiId: string;
    mobileNumber: string;
    amount: string;
    description: string;
}

interface PaymentInterfaceProps {
    onPaymentComplete?: (amount: number) => void;
    defaultAmount?: number;
    recipientName?: string;
    onCancel?: () => void;
}

// Lazy load the QR code component
const QRCodeSVG = lazy(() =>
    import("qrcode.react").then((module) => ({
        default: module.QRCodeSVG,
    }))
);

export function PaymentInterface({
    onPaymentComplete,
    defaultAmount = 0,
    recipientName = "Dhanvan Pharmacy",
    onCancel,
}: PaymentInterfaceProps) {
    const [paymentInfo, setPaymentInfo] = useState({
        upiId: "9730245214@ybl",
        mobileNumber: "9730245214",
        amount: defaultAmount.toString(),
        description: recipientName ? `Payment to ${recipientName}` : "",
    });
    const [showQR, setShowQR] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setPaymentInfo((prev) => ({ ...prev, [name]: value }));
    };

    const handleShowQR = () => {
        if (!paymentInfo.upiId && !paymentInfo.mobileNumber) {
            toast.error("Please enter a UPI ID or Mobile Number to generate QR.");
            return;
        }
        if (!paymentInfo.amount || isNaN(parseFloat(paymentInfo.amount)) || parseFloat(paymentInfo.amount) <= 0) {
            toast.error("Please enter a valid amount.");
            return;
        }
        setShowQR(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            if (!paymentInfo.amount || isNaN(parseFloat(paymentInfo.amount))) {
                toast.error("Please enter a valid amount.");
                return;
            }

            toast.success("Payment processed successfully!");
            if (onPaymentComplete) {
                onPaymentComplete(parseFloat(paymentInfo.amount));
            }

            // Reset form
            setPaymentInfo({
                upiId: "",
                mobileNumber: "",
                amount: defaultAmount.toString(),
                description: recipientName ? `Payment to ${recipientName}` : "",
            });
            setShowQR(false);
        } catch (error) {
            console.error("Payment submission failed:", error);
            toast.error("Failed to process payment. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const qrValue = paymentInfo.upiId
        ? `upi://pay?pa=${paymentInfo.upiId}&am=${paymentInfo.amount
        }&pn=${encodeURIComponent(recipientName || "")}`
        : `upi://pay?pn=${paymentInfo.mobileNumber}&am=${paymentInfo.amount}`;

    return (
        <Card className="w-full max-w-md mx-auto mt-4">
            <CardHeader>
                <CardTitle>Make Payment</CardTitle>
                <CardDescription>Pay using UPI ID or mobile number</CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={(e) => { e.preventDefault(); if (showQR) handleSubmit(e); else handleShowQR(); }} className="space-y-4">
                    {!showQR ? (
                        <>
                            <div className="space-y-2">
                                <Label htmlFor="upiId">UPI ID</Label>
                                <Input
                                    id="upiId"
                                    name="upiId"
                                    value={paymentInfo.upiId}
                                    onChange={handleInputChange}
                                    placeholder="username@bank"
                                />
                            </div>

                            <div className="relative my-4">
                                <div className="absolute inset-0 flex items-center">
                                    <span className="w-full border-t" />
                                </div>
                                <div className="relative flex justify-center text-xs uppercase">
                                    <span className="bg-background px-2 text-muted-foreground">OR</span>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="mobileNumber">Mobile Number (UPI linked)</Label>
                                <Input
                                    id="mobileNumber"
                                    name="mobileNumber"
                                    value={paymentInfo.mobileNumber}
                                    onChange={handleInputChange}
                                    placeholder="Enter mobile number"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="amount">Amount (₹)</Label>
                                <Input
                                    id="amount"
                                    name="amount"
                                    type="number"
                                    value={paymentInfo.amount}
                                    onChange={handleInputChange}
                                    disabled={defaultAmount > 0}
                                />
                            </div>
                            <div className="flex gap-2 pt-2">
                                {onCancel && (
                                    <Button type="button" variant="outline" className="w-full" onClick={onCancel}>
                                        Cancel
                                    </Button>
                                )}
                                <Button type="button" className="w-full" onClick={handleShowQR}>
                                    <QrCode className="w-4 h-4 mr-2" /> Generate QR
                                </Button>
                            </div>
                        </>
                    ) : (
                        <div className="flex flex-col items-center justify-center p-4 border rounded-md bg-white">
                            <Suspense fallback={<Loader2 className="w-8 h-8 animate-spin" />}>
                                <QRCodeSVG value={qrValue} size={200} />
                            </Suspense>
                            <p className="text-sm mt-4 text-center text-muted-foreground">
                                Scan this QR code with any UPI app to pay ₹{paymentInfo.amount}
                            </p>

                            <div className="flex gap-2 w-full mt-6">
                                <Button type="button" variant="outline" className="w-full" onClick={() => setShowQR(false)}>
                                    Back
                                </Button>
                                <Button type="button" onClick={handleSubmit} disabled={loading} className="w-full bg-primary text-primary-foreground">
                                    {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
                                    Confirm Payment
                                </Button>
                            </div>
                        </div>
                    )}
                </form>
            </CardContent>
        </Card>
    );
}
