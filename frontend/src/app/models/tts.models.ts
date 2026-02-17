// ─── API Response Models ────────────────────────────────────────
export interface ApiStatus {
  message: string;
  version: string;
  architecture: string;
  backend: string;
  available_endpoints: string[];
}

export interface SpeakersResponse {
  speakers: string[];
}

export interface LanguagesResponse {
  languages: string[];
}

// ─── Request Models ─────────────────────────────────────────────
export interface BaseGenerateRequest {
  text: string;
  language: string;
  reference_audio?: string | null;
  ref_text?: string | null;
}

export interface VoiceDesignRequest {
  text: string;
  language: string;
  instruct: string;
}

export interface CustomVoiceRequest {
  text: string;
  language: string;
  speaker: string;
  instruct?: string | null;
}

// ─── UI Models ──────────────────────────────────────────────────
export type TtsMode = 'base' | 'voice_design' | 'custom_voice';
export type ModelSize = '0.6b' | '1.7b';

export interface GenerationHistoryItem {
  id: string;
  text: string;
  mode: TtsMode;
  modelSize: ModelSize;
  language: string;
  speaker?: string;
  audioUrl: string;
  timestamp: Date;
}

export interface VoiceSpeaker {
  name: string;
  avatarColor: string;
  initials: string;
}

// ─── Voice CRUD Models ──────────────────────────────────────────
export interface Voice {
  id: string;
  name: string;
  example_text: string;
  instruct: string | null;
  audio_filename: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface VoiceListResponse {
  voices: Voice[];
  total: number;
}

export interface VoiceCreateRequest {
  name: string;
  example_text: string;
  instruct?: string | null;
}

export interface VoiceUpdateRequest {
  name?: string;
  example_text?: string;
  instruct?: string | null;
}
