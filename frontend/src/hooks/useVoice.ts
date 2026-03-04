import { useState, useRef, useCallback, useEffect } from "react";

declare global {
    interface Window {
        SpeechRecognition: any;
        webkitSpeechRecognition: any;
    }
}

export function useVoice() {
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState("");
    const [interimText, setInterimText] = useState("");
    const recognitionRef = useRef<any>(null);

    useEffect(() => {
        // Check browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("Speech Recognition not supported in this browser");
            return;
        }

        const recognition = new SpeechRecognition();

        recognition.lang = "en-US";
        recognition.interimResults = true; // shows live speech
        recognition.continuous = false;    // User requested simple non-continuous behavior

        recognition.onresult = (event: any) => {
            let finalTranscript = "";
            let currentInterim = "";

            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    currentInterim += event.results[i][0].transcript;
                }
            }

            if (finalTranscript) {
                setTranscript(finalTranscript);
                setInterimText("");
            } else {
                setInterimText(currentInterim);
            }
        };

        recognition.onerror = (event: any) => {
            console.error("Error:", event.error);
            setIsRecording(false);
        };

        recognition.onend = () => {
            setIsRecording(false);
        };

        recognitionRef.current = recognition;
    }, []);

    const startRecording = useCallback(() => {
        if (!recognitionRef.current) {
            alert("Speech recognition is not supported in this browser. Please use Google Chrome.");
            return;
        }
        try {
            setTranscript("");
            setInterimText("");
            setIsRecording(true);
            recognitionRef.current.start();
        } catch (e) {
            // Already started or error
            console.error("Start error:", e);
            setIsRecording(false);
        }
    }, []);

    const stopRecording = useCallback(() => {
        setIsRecording(false);
        try {
            recognitionRef.current?.stop();
        } catch (e) { /* ignore */ }
    }, []);

    const speak = useCallback((text: string) => {
        if (!("speechSynthesis" in window)) return;

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95;
        utterance.pitch = 1.05;
        utterance.volume = 1;
        utterance.lang = "en-US";

        const voices = window.speechSynthesis.getVoices();
        const preferred =
            voices.find(v => v.name.includes("Google") && v.lang.startsWith("en")) ||
            voices.find(v => v.name.includes("Samantha")) ||
            voices.find(v => v.lang.startsWith("en") && !v.localService) ||
            voices.find(v => v.lang.startsWith("en"));
        if (preferred) utterance.voice = preferred;

        window.speechSynthesis.speak(utterance);
    }, []);

    return {
        isRecording,
        transcript,
        interimText,
        startRecording,
        stopRecording,
        speak,
        isSupported: !!(window.SpeechRecognition || window.webkitSpeechRecognition),
    };
}
