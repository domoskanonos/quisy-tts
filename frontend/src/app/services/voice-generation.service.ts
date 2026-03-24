import { Injectable, inject } from '@angular/core';
import { Observable, of, throwError } from 'rxjs';
import { switchMap } from 'rxjs/operators';
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
}
