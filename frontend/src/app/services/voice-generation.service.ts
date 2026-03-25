import { Injectable, inject } from '@angular/core';
import { Observable, of, throwError, interval } from 'rxjs';
import { switchMap, take, timeout as rxTimeout, map, filter } from 'rxjs/operators';
import { TtsApiService } from './tts-api.service';
import { Voice } from '../models/tts.models';
import { StatusService } from './status.service';

@Injectable({ providedIn: 'root' })
export class VoiceGenerationService {
    private readonly ttsApi = inject(TtsApiService);
    private readonly statusSvc = inject(StatusService);

    /**
     * Ensure that a voice has a persisted audio file. If it's already present the voice is returned as-is.
     * Otherwise the method will generate an example audio via Voice Design and upload it, returning the
     * updated Voice from the backend.
     */
    ensureVoiceAudio(voice: Voice, force: boolean = false): Observable<Voice> {
        // Centralize generation on the backend: trigger server-side generation and poll status
        if (voice.audio_filename) return of(voice);

        if (!voice.instruct) {
            return throwError(() => new Error('Voice has no instruct text to generate audio.'));
        }

        // Trigger backend generation and poll until done
        this.ttsApi.ensureVoiceAudio(voice.id, force).subscribe({ next: () => {}, error: () => {} });
        return this.ensureVoiceAudioById(voice.id);
    }

    /**
     * Ask the backend to ensure audio exists for a voiceId and poll until it's available.
     * Useful when only an id is known and the backend may generate audio asynchronously.
     */
    ensureVoiceAudioById(
        voiceId: string,
        pollIntervalMs = 2000,
        timeoutMs = 60000,
        statusCallback?: (status: any) => void,
    ): Observable<Voice> {
        // Trigger backend ensure endpoint (fire-and-forget) then poll GET /voices/:id
        this.ttsApi.ensureVoiceAudio(voiceId).subscribe({ next: () => { }, error: () => { } });

        // Prefer WebSocket real-time updates when available; otherwise fall back to polling
        // Use StatusService (Angular DI) when available for real-time updates, and keep polling as reliable fallback.
        // Use StatusService (DI) for real-time events, and keep polling as fallback
            const statusSvc = this.statusSvc;

            const ws$ = new Observable<Voice>(subscriber => {
                const wsSub = statusSvc.subscribeVoice(voiceId).subscribe((ev: any) => {
                    try { statusCallback && statusCallback(ev); } catch (_e) {}
                    if (ev && ev.status === 'done') {
                        // fetch latest voice and emit
                        this.ttsApi.getVoice(voiceId).subscribe({ next: v => { subscriber.next(v as Voice); subscriber.complete(); }, error: e => subscriber.error(e) });
                    }
                    if (ev && ev.status === 'failed') {
                        subscriber.error(new Error(ev.message || 'Generation failed'));
                    }
                });

                // Trigger backend generation (fire-and-forget)
                this.ttsApi.ensureVoiceAudio(voiceId).subscribe({ next: () => {}, error: () => {} });

                return () => wsSub.unsubscribe();
            });

            // Polling fallback: resolves if WS doesn't deliver final event
            const polling$ = interval(pollIntervalMs).pipe(
                switchMap(() => this.ttsApi.getEnsureAudioStatus(voiceId)),
                switchMap((s: any) => {
                    try { statusCallback && statusCallback(s); } catch (_e) {}
                    return of(s);
                }),
                filter((s: any) => s && s.status === 'done'),
                take(1),
                rxTimeout(timeoutMs),
                switchMap(() => this.ttsApi.getVoice(voiceId)),
                map(v => v as Voice),
            );

            // Merge behavior: prefer WS, but if polling resolves first emit that
            return new Observable<Voice>(subscriber => {
                const wsSub = ws$.subscribe({ next: v => { subscriber.next(v); subscriber.complete(); }, error: e => subscriber.error(e) });
                const pollSub = polling$.subscribe({ next: v => { subscriber.next(v); subscriber.complete(); }, error: e => subscriber.error(e) });
                return () => { wsSub.unsubscribe(); pollSub.unsubscribe(); };
            });
}
}
