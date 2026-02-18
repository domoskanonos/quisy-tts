import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
    ApiStatus,
    BaseGenerateRequest,
    CustomVoiceRequest,
    LanguagesResponse,
    ModelSize,
    SpeakersResponse,
    Voice,
    VoiceCreateRequest,
    VoiceDesignRequest,
    VoiceListResponse,
    VoiceUpdateRequest,
} from '../models/tts.models';

@Injectable({ providedIn: 'root' })
export class TtsApiService {
    private readonly http = inject(HttpClient);
    private readonly baseUrl = '/api';

    // ─── Info Endpoints ─────────────────────────────────────────
    getStatus(): Observable<ApiStatus> {
        return this.http.get<ApiStatus>(this.baseUrl + '/');
    }

    getSpeakers(): Observable<SpeakersResponse> {
        return this.http.get<SpeakersResponse>(this.baseUrl + '/speakers');
    }

    getLanguages(): Observable<LanguagesResponse> {
        return this.http.get<LanguagesResponse>(this.baseUrl + '/languages');
    }

    // ─── Base Mode (Voice Cloning) ──────────────────────────────
    generateBase(request: BaseGenerateRequest, modelSize: ModelSize): Observable<Blob> {
        return this.http.post(
            `${this.baseUrl}/generate/base/${modelSize}`,
            request,
            { responseType: 'blob' }
        );
    }

    // ─── Voice Design Mode ──────────────────────────────────────
    generateVoiceDesign(request: VoiceDesignRequest): Observable<Blob> {
        return this.http.post(
            `${this.baseUrl}/generate/voice-design/1.7b`,
            request,
            { responseType: 'blob' }
        );
    }

    // ─── Custom Voice Mode ──────────────────────────────────────
    generateCustomVoice(request: CustomVoiceRequest, modelSize: ModelSize): Observable<Blob> {
        return this.http.post(
            `${this.baseUrl}/generate/custom-voice/${modelSize}`,
            request,
            { responseType: 'blob' }
        );
    }

    // ─── Voice CRUD ─────────────────────────────────────────────
    getVoices(): Observable<VoiceListResponse> {
        return this.http.get<VoiceListResponse>(this.baseUrl + '/voices/');
    }

    getVoice(voiceId: string): Observable<Voice> {
        return this.http.get<Voice>(`${this.baseUrl}/voices/${voiceId}`);
    }

    createVoice(data: VoiceCreateRequest): Observable<Voice> {
        return this.http.post<Voice>(this.baseUrl + '/voices/', data);
    }

    updateVoice(voiceId: string, data: VoiceUpdateRequest): Observable<Voice> {
        return this.http.put<Voice>(`${this.baseUrl}/voices/${voiceId}`, data);
    }

    deleteVoice(voiceId: string): Observable<void> {
        return this.http.delete<void>(`${this.baseUrl}/voices/${voiceId}`);
    }

    uploadVoiceAudio(voiceId: string, file: File): Observable<Voice> {
        const formData = new FormData();
        formData.append('file', file);
        return this.http.post<Voice>(`${this.baseUrl}/voices/${voiceId}/audio`, formData);
    }

    getVoiceAudioUrl(voiceId: string): string {
        return `${this.baseUrl}/voices/${voiceId}/audio`;
    }

    // ─── Background Generation ──────────────────────────────────
    ensureVoiceAudio(voiceId: string): Observable<{ status: string; message: string }> {
        return this.http.post<{ status: string; message: string }>(
            `${this.baseUrl}/voices/${voiceId}/ensure-audio`,
            {}
        );
    }
}
