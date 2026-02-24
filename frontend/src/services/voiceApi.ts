/**
 * Voice API — OpenAI Whisper preferred, browser Web Speech API as fallback.
 *
 * Logic:
 *   1. Call /api/v1/voice/status (backend checks if user has an active OpenAI key).
 *   2. If backend says provider = 'openai'  → use Whisper + OpenAI TTS.
 *   3. If backend says available = false    → fall back to browser SpeechRecognition.
 *
 * Switching is automatic: call clearStatusCache() after the user adds/removes
 * an OpenAI key and the next voice action will re-check and switch providers.
 */

import { api } from './api';
import toast from 'react-hot-toast';
import { localVoice, LocalTranscriptionResult, LocalSynthesisOptions } from './localVoice';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface VoiceStatus {
    available: boolean;
    message: string;
    provider: 'openai' | 'local' | null;
    action_required?: 'add_openai_provider' | 'add_any_provider' | 'use_local';
}

export interface TranscriptionResponse {
    success: boolean;
    text: string;
    language: string;
    duration_seconds: number;
    audio_size_bytes?: number;
    transcribed_at: string;
    provider: 'openai' | 'local';
}

export interface SynthesisResponse {
    success: boolean;
    audio_url?: string;
    duration_estimate: number;
    voice: string;
    speed: number;
    generated_at: string;
    provider: 'openai' | 'local';
}

export interface VoiceLanguage {
    code: string;
    name: string;
}

export interface TTSVoice {
    id: string;
    name: string;
    description: string;
}

// ─── Module State ─────────────────────────────────────────────────────────────

const API_BASE = '/api/v1/voice';

let cachedStatus: VoiceStatus | null = null;
let statusCacheTime = 0;
const STATUS_CACHE_TTL = 60_000; // 1 minute

// These let stopLocalTranscription() resolve the promise created in transcribeWithLocal()
let _pendingLocalResolve: ((text: string) => void) | null = null;
let _pendingLocalReject: ((err: unknown) => void) | null = null;

// ─── Language Helper ──────────────────────────────────────────────────────────

const LANG_MAP: Record<string, string> = {
    en: 'en-US', es: 'es-ES', fr: 'fr-FR', de: 'de-DE', it: 'it-IT',
    pt: 'pt-BR', ru: 'ru-RU', zh: 'zh-CN', ja: 'ja-JP', ko: 'ko-KR',
    ar: 'ar-SA', hi: 'hi-IN', nl: 'nl-NL', pl: 'pl-PL', tr: 'tr-TR', vi: 'vi-VN',
};

function toBcp47(lang?: string): string {
    if (!lang) return 'en-US';
    if (lang.includes('-')) return lang; // already a full tag e.g. 'en-US'
    return LANG_MAP[lang] ?? 'en-US';
}

// ─── API ──────────────────────────────────────────────────────────────────────

export const voiceApi = {

    // ── Status / Provider Detection ──────────────────────────────────────────

    /**
     * Determine which provider to use.
     *
     * 1. Ask backend → does the user have an active OpenAI key?
     *    YES → provider = 'openai'
     *    NO  → check browser support → provider = 'local'
     *
     * Result is cached for 60 s. Call clearStatusCache() to force a re-check
     * immediately (e.g. right after the user saves a new API key in Settings).
     */
    checkStatus: async (forceRefresh = false): Promise<VoiceStatus> => {
        const now = Date.now();

        if (!forceRefresh && cachedStatus && (now - statusCacheTime) < STATUS_CACHE_TTL) {
            return cachedStatus;
        }

        // Step 1: Ask the backend — it knows if the user has an OpenAI key
        try {
            const response = await api.get<VoiceStatus>(`${API_BASE}/status`);
            if (response.data.available && response.data.provider === 'openai') {
                cachedStatus = { ...response.data, provider: 'openai' };
                statusCacheTime = now;
                return cachedStatus;
            }
            // Backend responded but no OpenAI key — fall through to local
        } catch {
            // Backend unreachable — fall through to local
        }

        // Step 2: Fall back to browser Web Speech API
        const localAvail = await localVoice.checkAvailability();
        if (localAvail.available) {
            cachedStatus = {
                available: true,
                message: 'No OpenAI key found — using browser voice instead',
                provider: 'local',
            };
            statusCacheTime = now;
            return cachedStatus;
        }

        // Step 3: Nothing works
        cachedStatus = {
            available: false,
            message: localAvail.message,
            provider: null,
            action_required: 'add_openai_provider',
        };
        statusCacheTime = now;
        return cachedStatus;
    },

    /**
     * Call this after the user adds or removes an OpenAI API key so the next
     * voice action immediately re-checks and switches providers.
     */
    clearStatusCache: (): void => {
        cachedStatus = null;
        statusCacheTime = 0;
    },

    getCurrentProvider: (): 'openai' | 'local' | null => cachedStatus?.provider ?? null,

    /** Returns true if voice is usable, shows a toast if not. */
    checkAvailability: async (): Promise<boolean> => {
        const status = await voiceApi.checkStatus();
        if (!status.available) {
            toast.error(status.message, { duration: 5000 });
            return false;
        }
        if (status.provider === 'local') {
            toast('Using browser voice (no OpenAI key configured)', { icon: '🎤', duration: 3000 });
        }
        return true;
    },

    // ── Transcription ────────────────────────────────────────────────────────

    /**
     * Smart transcription — picks the right provider automatically.
     *
     * OpenAI path : pass a recorded audioBlob (from startRecording/stopRecording).
     * Local path  : pass null for audioBlob; onProgress fires with real-time text.
     *               The promise resolves only when stopLocalTranscription() is called.
     *
     * Recommended: use startSmartRecording() instead — it handles all of this.
     */
    transcribe: async (
        audioBlob: Blob | null,
        language?: string,
        onProgress?: (text: string, isFinal: boolean) => void,
    ): Promise<TranscriptionResponse> => {
        const status = await voiceApi.checkStatus();

        if (status.provider === 'openai') {
            if (!audioBlob) throw new Error('audioBlob is required for OpenAI transcription');
            return voiceApi.transcribeWithOpenAI(audioBlob, language);
        }

        return voiceApi.transcribeWithLocal(language, onProgress);
    },

    /** Send a recorded audio blob to OpenAI Whisper. */
    transcribeWithOpenAI: async (audioBlob: Blob, language?: string): Promise<TranscriptionResponse> => {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        if (language) formData.append('language', language);

        const response = await api.post<TranscriptionResponse>(
            `${API_BASE}/transcribe`,
            formData,
            { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60_000 },
        );
        return { ...response.data, provider: 'openai' };
    },

    /**
     * Start browser SpeechRecognition.
     * The returned Promise stays pending until stopLocalTranscription() is called.
     * Use onProgress to receive interim/final text in real time as the user speaks.
     */
    transcribeWithLocal: (
        language?: string,
        onProgress?: (text: string, isFinal: boolean) => void,
    ): Promise<TranscriptionResponse> => {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();

            // Wire up real-time progress updates
            const handleResult = (result: LocalTranscriptionResult) => {
                onProgress?.(result.text, result.isFinal);
            };

            // Start the browser recogniser
            localVoice.transcribe(handleResult, reject, toBcp47(language));

            // Store resolve/reject so stopLocalTranscription() can close this promise
            _pendingLocalResolve = (text: string) => {
                resolve({
                    success: true,
                    text,
                    language: language ?? 'auto-detected',
                    duration_seconds: (Date.now() - startTime) / 1000,
                    transcribed_at: new Date().toISOString(),
                    provider: 'local',
                });
            };
            _pendingLocalReject = reject;
        });
    },

    /**
     * Stop browser recognition gracefully and resolve the pending promise.
     * Call this when the user releases the mic button.
     */
    stopLocalTranscription: async (): Promise<TranscriptionResponse> => {
        const text = await localVoice.stopTranscribe();
        _pendingLocalResolve?.(text ?? '');
        _pendingLocalResolve = null;
        _pendingLocalReject = null;

        return {
            success: true,
            text: text ?? '',
            language: 'auto-detected',
            duration_seconds: 0,
            transcribed_at: new Date().toISOString(),
            provider: 'local',
        };
    },

    /** Abort browser recognition immediately with no result. */
    abortLocalTranscription: (): void => {
        localVoice.abortTranscribe();
        _pendingLocalReject?.(new Error('Transcription aborted'));
        _pendingLocalResolve = null;
        _pendingLocalReject = null;
    },

    isLocalTranscribing: (): boolean => localVoice.isListening,

    // ── Smart Recording Helper ───────────────────────────────────────────────

    /**
     * ONE call to start recording regardless of provider.
     * Returns a `stop` function — call it when the user finishes speaking.
     *
     * Example:
     *   const stop = await voiceApi.startSmartRecording('en', setText);
     *   // user speaks...
     *   const result = await stop();   // TranscriptionResponse
     */
    startSmartRecording: async (
        language?: string,
        onProgress?: (text: string, isFinal: boolean) => void,
    ): Promise<() => Promise<TranscriptionResponse>> => {
        const status = await voiceApi.checkStatus();

        if (status.provider === 'openai') {
            // Record audio → send blob to Whisper on stop
            const { recorder, stream } = await voiceApi.startRecording();
            recorder.start();

            return async () => {
                const blob = await voiceApi.stopRecording(recorder, stream);
                return voiceApi.transcribeWithOpenAI(blob, language);
            };
        } else {
            // Start real-time browser recognition
            // (transcribeWithLocal promise is pending internally)
            voiceApi.transcribeWithLocal(language, onProgress);

            return async () => voiceApi.stopLocalTranscription();
        }
    },

    // ── Synthesis ────────────────────────────────────────────────────────────

    /**
     * Speak text.
     * Uses OpenAI TTS if the user has a key, browser speechSynthesis otherwise.
     * If OpenAI TTS fails at runtime it silently falls back to local.
     */
    synthesize: async (text: string, voice = 'alloy', speed = 1.0): Promise<SynthesisResponse> => {
        const status = await voiceApi.checkStatus();

        if (status.provider === 'openai') {
            try {
                return await voiceApi.synthesizeWithOpenAI(text, voice, speed);
            } catch (err) {
                console.warn('[voiceApi] OpenAI TTS failed, falling back to browser TTS', err);
            }
        }

        return voiceApi.synthesizeWithLocal(text, speed);
    },

    synthesizeWithOpenAI: async (text: string, voice = 'alloy', speed = 1.0): Promise<SynthesisResponse> => {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('voice', voice);
        formData.append('speed', speed.toString());

        const response = await api.post<SynthesisResponse>(
            `${API_BASE}/synthesize`,
            formData,
            { headers: { 'Content-Type': 'multipart/form-data' } },
        );
        return { ...response.data, provider: 'openai' };
    },

    synthesizeWithLocal: async (text: string, rate = 1.0): Promise<SynthesisResponse> => {
        // waitForVoices handles Chrome's async voice loading
        const voices = await localVoice.waitForVoices();

        const preferredVoice =
            voices.find(v => v.lang.startsWith('en') && v.name.includes('Google')) ??
            voices.find(v => v.lang.startsWith('en')) ??
            voices[0];

        const options: LocalSynthesisOptions = {
            rate,
            pitch: 1.0,
            volume: 1.0,
            voice: preferredVoice?.name,
        };

        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            localVoice.synthesize(
                text, options,
                undefined,
                () => resolve({
                    success: true,
                    duration_estimate: (Date.now() - startTime) / 1000,
                    voice: preferredVoice?.name ?? 'default',
                    speed: rate,
                    generated_at: new Date().toISOString(),
                    provider: 'local',
                }),
                (error) => reject(new Error(error)),
            );
        });
    },

    stopSynthesis: (): void => localVoice.stopSynthesis(),

    // ── Raw Recording (OpenAI path) ───────────────────────────────────────────

    startRecording: async (): Promise<{ recorder: MediaRecorder; stream: MediaStream }> => {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mimeType =
            MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' :
            MediaRecorder.isTypeSupported('audio/webm')             ? 'audio/webm' :
                                                                       'audio/mp4';
        return { recorder: new MediaRecorder(stream, { mimeType }), stream };
    },

    stopRecording: (recorder: MediaRecorder, stream: MediaStream): Promise<Blob> =>
        new Promise((resolve) => {
            const chunks: BlobPart[] = [];
            recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
            recorder.onstop = () => {
                stream.getTracks().forEach(t => t.stop());
                resolve(new Blob(chunks, { type: recorder.mimeType }));
            };
            recorder.stop();
        }),

    // ── Direct Local Recognition ──────────────────────────────────────────────

    startLocalRecognition: async (
        onResult: (text: string, isFinal: boolean) => void,
        onError: (error: string) => void,
        language?: string,
    ): Promise<void> => {
        const wrapped = (r: LocalTranscriptionResult) => onResult(r.text, r.isFinal);
        await localVoice.transcribe(wrapped, onError, toBcp47(language));
    },

    stopLocalRecognition: (): Promise<string> => localVoice.stopTranscribe(),

    // ── Playback ──────────────────────────────────────────────────────────────

    playAudio: async (urlOrText: string, isLocal = false): Promise<void> => {
        if (isLocal) {
            await voiceApi.synthesizeWithLocal(urlOrText);
        } else {
            await new Audio(urlOrText).play();
        }
    },

    getAudioUrl: (userId: string, filename: string): string =>
        `${API_BASE}/audio/${userId}/${filename}`,

    // ── Language / Voice Lists ────────────────────────────────────────────────

    getLanguages: async (): Promise<VoiceLanguage[]> =>
        localVoice.getSupportedLanguages().map(l => ({
            code: l.code.split('-')[0],
            name: l.name,
        })),

    getVoices: async (): Promise<TTSVoice[]> => {
        const status = await voiceApi.checkStatus();

        if (status.provider === 'openai') {
            try {
                const response = await api.get<{ voices: TTSVoice[]; default: string }>(`${API_BASE}/voices`);
                return response.data.voices;
            } catch { /* fall through */ }
        }

        const voices = await localVoice.waitForVoices();
        return voices.map(v => ({
            id: v.name,
            name: v.name,
            description: `${v.lang}${v.localService ? ' (local)' : ''}`,
        }));
    },
};

export default voiceApi;