/**
 * Local Voice Service - Browser-native speech recognition and synthesis
 * Falls back automatically when OpenAI Whisper/TTS is unavailable
 * Uses Web Speech API (SpeechRecognition + speechSynthesis)
 */

// Type declarations for Web Speech API (must be before class definition)
interface SpeechRecognitionEvent extends Event {
    readonly resultIndex: number;
    readonly results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
    readonly error: string;
    readonly message: string;
}

interface SpeechRecognitionResultList {
    readonly length: number;
    item(index: number): SpeechRecognitionResult;
    [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
    readonly isFinal: boolean;
    readonly length: number;
    item(index: number): SpeechRecognitionAlternative;
    [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
    readonly transcript: string;
    readonly confidence: number;
}

interface SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    maxAlternatives: number;
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null;
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null;
    onend: ((this: SpeechRecognition, ev: Event) => void) | null;
    onstart: ((this: SpeechRecognition, ev: Event) => void) | null;
    start(): void;
    stop(): void;
    abort(): void;
}

interface SpeechRecognitionConstructor {
    new (): SpeechRecognition;
}

export interface LocalTranscriptionResult {
    text: string;
    confidence: number;
    isFinal: boolean;
    duration_seconds: number;
}

export interface LocalSynthesisOptions {
    voice?: string;
    rate?: number;
    pitch?: number;
    volume?: number;
}

export interface LocalVoiceState {
    isSupported: boolean;
    isListening: boolean;
    isSpeaking: boolean;
    transcript: string;
    interimTranscript: string;
    error: string | null;
}

export interface LocalAvailability {
    available: boolean;
    message: string;
    recognitionSupported: boolean;
    synthesisSupported: boolean;
}

class LocalVoiceService {
    private recognition: SpeechRecognition | null = null;
    private synthesis: SpeechSynthesis | null = null;
    private currentUtterance: SpeechSynthesisUtterance | null = null;
    private _isListening: boolean = false;
    private _isSpeaking: boolean = false;
    private recordingStartTime: number = 0;
    private accumulatedFinalText: string = '';

    constructor() {
        // Safely initialize synthesis
        if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
            this.synthesis = window.speechSynthesis;
        }
    }

    // ─── Feature Detection ───────────────────────────────────────────────────

    get isRecognitionSupported(): boolean {
        return typeof window !== 'undefined' &&
            ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);
    }

    get isSynthesisSupported(): boolean {
        return typeof window !== 'undefined' && 'speechSynthesis' in window;
    }

    get isListening(): boolean {
        return this._isListening;
    }

    get isSpeaking(): boolean {
        return this._isSpeaking;
    }

    // ─── Voice Enumeration ───────────────────────────────────────────────────

    getVoices(): SpeechSynthesisVoice[] {
        if (!this.isSynthesisSupported || !this.synthesis) return [];
        return this.synthesis.getVoices();
    }

    getVoicesByLang(lang: string): SpeechSynthesisVoice[] {
        return this.getVoices().filter(v => v.lang.startsWith(lang));
    }

    /**
     * Wait for voices to load (Chrome loads them asynchronously)
     */
    waitForVoices(timeout = 3000): Promise<SpeechSynthesisVoice[]> {
        return new Promise((resolve) => {
            if (!this.isSynthesisSupported || !this.synthesis) {
                resolve([]);
                return;
            }

            const voices = this.synthesis.getVoices();
            if (voices.length > 0) {
                resolve(voices);
                return;
            }

            const timer = setTimeout(() => resolve(this.synthesis?.getVoices() ?? []), timeout);

            window.speechSynthesis.onvoiceschanged = () => {
                clearTimeout(timer);
                resolve(this.synthesis?.getVoices() ?? []);
            };
        });
    }

    // ─── Speech Recognition ──────────────────────────────────────────────────

    /**
     * Start real-time transcription using the browser's SpeechRecognition API.
     * Continuously fires onResult callbacks with interim and final results.
     */
    async transcribe(
        onResult: (result: LocalTranscriptionResult) => void,
        onError: (error: string) => void,
        language: string = 'en-US'
    ): Promise<void> {
        if (!this.isRecognitionSupported) {
            onError('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
            return;
        }

        // Stop any existing session first
        this.abortTranscribe();

        // Request microphone permission
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
        } catch {
            onError('Microphone permission denied. Please allow microphone access and try again.');
            return;
        }

        const SpeechRecognitionCtor: SpeechRecognitionConstructor =
            (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;

        const recognition = new SpeechRecognitionCtor();
        this.recognition = recognition;

        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = language;
        recognition.maxAlternatives = 1;

        this.recordingStartTime = Date.now();
        this.accumulatedFinalText = '';
        this._isListening = true;

        recognition.onstart = () => {
            this._isListening = true;
        };

        recognition.onresult = (event: SpeechRecognitionEvent) => {
            let interimTranscript = '';
            let newFinalText = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i];
                const transcript = result[0].transcript;

                if (result.isFinal) {
                    newFinalText += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }

            if (newFinalText) {
                this.accumulatedFinalText += newFinalText;
            }

            const duration = (Date.now() - this.recordingStartTime) / 1000;
            const isFinal = newFinalText.length > 0;
            const text = isFinal
                ? this.accumulatedFinalText
                : this.accumulatedFinalText + interimTranscript;

            const confidence = event.results[event.resultIndex]?.[0]?.confidence ?? 0;

            onResult({ text, confidence, isFinal, duration_seconds: duration });
        };

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
            this._isListening = false;
            onError(this.mapRecognitionError(event.error));
        };

        recognition.onend = () => {
            this._isListening = false;
        };

        recognition.start();
    }

    /**
     * Stop transcription gracefully and return accumulated final text.
     */
    stopTranscribe(): Promise<string> {
        return new Promise((resolve) => {
            if (!this.recognition) {
                this._isListening = false;
                resolve(this.accumulatedFinalText);
                return;
            }

            const rec = this.recognition;
            this.recognition = null;

            // Capture any remaining final text on end
            rec.onend = () => {
                this._isListening = false;
                resolve(this.accumulatedFinalText);
            };

            // Catch any last results before stop
            rec.onresult = (event: SpeechRecognitionEvent) => {
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    if (event.results[i].isFinal) {
                        this.accumulatedFinalText += event.results[i][0].transcript;
                    }
                }
            };

            rec.stop();
        });
    }

    /**
     * Abort transcription immediately without waiting for results.
     */
    abortTranscribe(): void {
        if (this.recognition) {
            this.recognition.onresult = null;
            this.recognition.onerror = null;
            this.recognition.onend = null;
            this.recognition.abort();
            this.recognition = null;
        }
        this._isListening = false;
        this.accumulatedFinalText = '';
    }

    // ─── Speech Synthesis ────────────────────────────────────────────────────

    /**
     * Speak text using the browser's speechSynthesis API.
     * Resolves when speech finishes, rejects on error.
     */
    synthesize(
        text: string,
        options: LocalSynthesisOptions = {},
        onStart?: () => void,
        onEnd?: () => void,
        onError?: (error: string) => void
    ): void {
        if (!this.isSynthesisSupported || !this.synthesis) {
            onError?.('Text-to-speech is not supported in this browser.');
            return;
        }

        // Cancel any ongoing speech
        this.stopSynthesis();

        const utterance = new SpeechSynthesisUtterance(text);
        this.currentUtterance = utterance;

        // Apply options with sensible defaults
        utterance.rate   = options.rate   ?? 1.0;
        utterance.pitch  = options.pitch  ?? 1.0;
        utterance.volume = options.volume ?? 1.0;

        // Select voice
        if (options.voice) {
            const voices = this.getVoices();
            const match = voices.find(v => v.name === options.voice);
            if (match) utterance.voice = match;
        }

        utterance.onstart = () => {
            this._isSpeaking = true;
            onStart?.();
        };

        utterance.onend = () => {
            this._isSpeaking = false;
            this.currentUtterance = null;
            onEnd?.();
        };

        utterance.onerror = (event) => {
            this._isSpeaking = false;
            this.currentUtterance = null;
            // 'interrupted' is not really an error — it means we cancelled it
            if (event.error !== 'interrupted') {
                onError?.(`Speech synthesis error: ${event.error}`);
            }
        };

        this.synthesis.speak(utterance);
    }

    /**
     * Synthesize and return a Promise that resolves when speech ends.
     */
    synthesizeAsync(text: string, options: LocalSynthesisOptions = {}): Promise<void> {
        return new Promise((resolve, reject) => {
            this.synthesize(text, options, undefined, resolve, reject);
        });
    }

    stopSynthesis(): void {
        if (this.synthesis) {
            this.synthesis.cancel();
        }
        this._isSpeaking = false;
        this.currentUtterance = null;
    }

    pauseSynthesis(): void {
        this.synthesis?.pause();
    }

    resumeSynthesis(): void {
        this.synthesis?.resume();
    }

    // ─── Availability ────────────────────────────────────────────────────────

    async checkAvailability(): Promise<LocalAvailability> {
        const recognitionSupported = this.isRecognitionSupported;
        const synthesisSupported = this.isSynthesisSupported;

        if (recognitionSupported && synthesisSupported) {
            return {
                available: true,
                message: 'Local voice ready (browser-native Web Speech API)',
                recognitionSupported: true,
                synthesisSupported: true,
            };
        }

        const missing: string[] = [];
        if (!recognitionSupported) missing.push('speech recognition');
        if (!synthesisSupported) missing.push('text-to-speech');

        return {
            available: false,
            message: `Your browser does not support ${missing.join(' or ')}. Use Chrome or Edge for full voice support.`,
            recognitionSupported,
            synthesisSupported,
        };
    }

    // ─── Language Support ────────────────────────────────────────────────────

    getSupportedLanguages(): { code: string; name: string }[] {
        return [
            { code: 'en-US', name: 'English (US)' },
            { code: 'en-GB', name: 'English (UK)' },
            { code: 'es-ES', name: 'Spanish (Spain)' },
            { code: 'es-MX', name: 'Spanish (Mexico)' },
            { code: 'fr-FR', name: 'French' },
            { code: 'de-DE', name: 'German' },
            { code: 'it-IT', name: 'Italian' },
            { code: 'pt-BR', name: 'Portuguese (Brazil)' },
            { code: 'pt-PT', name: 'Portuguese (Portugal)' },
            { code: 'ru-RU', name: 'Russian' },
            { code: 'zh-CN', name: 'Chinese (Simplified)' },
            { code: 'zh-TW', name: 'Chinese (Traditional)' },
            { code: 'ja-JP', name: 'Japanese' },
            { code: 'ko-KR', name: 'Korean' },
            { code: 'ar-SA', name: 'Arabic' },
            { code: 'hi-IN', name: 'Hindi' },
            { code: 'nl-NL', name: 'Dutch' },
            { code: 'pl-PL', name: 'Polish' },
            { code: 'tr-TR', name: 'Turkish' },
            { code: 'vi-VN', name: 'Vietnamese' },
            { code: 'sv-SE', name: 'Swedish' },
            { code: 'da-DK', name: 'Danish' },
            { code: 'fi-FI', name: 'Finnish' },
            { code: 'nb-NO', name: 'Norwegian' },
        ];
    }

    // ─── Private Helpers ─────────────────────────────────────────────────────

    private mapRecognitionError(error: string): string {
        const map: Record<string, string> = {
            'no-speech':      'No speech detected. Please speak and try again.',
            'audio-capture':  'No microphone found or microphone is not working.',
            'not-allowed':    'Microphone permission denied. Please allow access in your browser settings.',
            'network':        'A network error occurred during recognition. Check your connection.',
            'aborted':        'Speech recognition was cancelled.',
            'bad-grammar':    'Speech recognition grammar error.',
            'language-not-supported': 'The selected language is not supported by your browser.',
        };
        return map[error] ?? `Speech recognition error: ${error}`;
    }
}

// ─── Singleton ───────────────────────────────────────────────────────────────

export const localVoice = new LocalVoiceService();

// ─── Global Type Extensions ───────────────────────────────────────────────────

declare global {
    interface Window {
        SpeechRecognition: SpeechRecognitionConstructor;
        webkitSpeechRecognition: SpeechRecognitionConstructor;
    }

    interface SpeechSynthesisVoice {
        local?: boolean;
    }
}