import { Injectable, inject } from '@angular/core';
import { Observable, of, throwError, interval } from 'rxjs';
import { switchMap, take, timeout as rxTimeout, map, filter } from 'rxjs/operators';
import { TtsApiService } from './tts-api.service';
import { Voice } from '../models/tts.models';

@Injectable({ providedIn: 'root' })
export class VoiceGenerationService {
    private readonly ttsApi = inject(TtsApiService);

    /**
     * Ensure that a voice has a persisted audio file. If it's already present the voice is returned as-is.
     * Otherwise the method will generate an example audio via Voice Design and upload it, returning the
     * updated Voice from the backend.
     */
    ensureVoiceAudio(voice: Voice): Observable<Voice> {
        if (voice.audio_filename) return of(voice);

        if (!voice.instruct) {
            return throwError(() => new Error('Voice has no instruct text to generate audio.'));
        }

        return this.ttsApi.generateVoiceDesign({
            text: voice.example_text || 'Dies ist eine Hörprobe meiner Stimme.',
            language: voice.language || 'german',
            instruct: voice.instruct || '',
        }).pipe(
            switchMap((blob: Blob) => {
                const file = new File([blob], `voice_${voice.id}.wav`, { type: 'audio/wav' });
                return this.ttsApi.uploadVoiceAudio(voice.id, file);
            })
        );
    }

    /**
     * Ask the backend to ensure audio exists for a voiceId and poll until it's available.
     * Useful when only an id is known and the backend may generate audio asynchronously.
     */
    ensureVoiceAudioById(voiceId: string, pollIntervalMs = 2000, timeoutMs = 60000): Observable<Voice> {
        // Trigger backend ensure endpoint (fire-and-forget) then poll GET /voices/:id
        this.ttsApi.ensureVoiceAudio(voiceId).subscribe({ next: () => { }, error: () => { } });

        return interval(pollIntervalMs).pipe(
            switchMap(() => this.ttsApi.getVoice(voiceId)),
            filter((v: Voice) => !!v.audio_filename),
            take(1),
            rxTimeout(timeoutMs),
            map(v => v as Voice)
        );
    }
}
