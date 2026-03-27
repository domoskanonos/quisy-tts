import { Injectable, OnDestroy } from '@angular/core';
import { Subject, Observable, BehaviorSubject, timer } from 'rxjs';
import { filter, takeUntil } from 'rxjs/operators';

export interface RefGenEvent {
    type: string;
    voice_id: string;
    status: 'queued' | 'running' | 'progress' | 'done' | 'failed';
    progress?: number;
    message?: string;
}

/**
 * StatusService establishes a single WebSocket connection to the server and
 * multiplexes reference-generation events to per-voice Observables.
 *
 * - Uses exponential backoff reconnect.
 * - Queues outgoing subscribe/unsubscribe commands until socket is open.
 * - Exposes `subscribeVoice(voiceId)` which returns an Observable of events
 *   scoped to that voice. The service sends subscribe/unsubscribe commands
 *   automatically when the first subscriber appears and when the last
 *   unsubscribes.
 */
@Injectable({ providedIn: 'root' })
export class StatusService implements OnDestroy {
    private ws: WebSocket | null = null;
    private incoming$ = new Subject<RefGenEvent>();
    private destroy$ = new Subject<void>();
    private connected$ = new BehaviorSubject<boolean>(false);

    // Map voice_id -> { subject, refCount }
    private voiceMap: Map<string, { subj: Subject<RefGenEvent>; ref: number }> = new Map();

    // Outgoing command queue while socket not open
    private pendingCmds: string[] = [];

    // Reconnect control
    private reconnectAttempts = 0;

    constructor() {
        this.connect();
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
        this.closeSocket();
    }

    private getWsUrl(): string {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        return `${protocol}://${window.location.host}/api/ws/status`;
    }

    private connect(): void {
        try {
            this.ws = new WebSocket(this.getWsUrl());
            this.ws.onopen = () => {
                this.reconnectAttempts = 0;
                this.connected$.next(true);
                // flush pending commands
                while (this.pendingCmds.length) {
                    const cmd = this.pendingCmds.shift()!;
                    this.safeSend(cmd);
                }
                // resubscribe active voices
                for (const vid of this.voiceMap.keys()) {
                    this.enqueueCommand(JSON.stringify({ action: 'subscribe', voice_id: vid }));
                }
            };
            this.ws.onmessage = (ev: MessageEvent) => {
                try {
                    const data = JSON.parse(ev.data) as RefGenEvent;
                    this.incoming$.next(data);
                    // route to voice subject if exists
                    const entry = this.voiceMap.get(data.voice_id);
                    if (entry) entry.subj.next(data);
                } catch (e) {
                    // ignore invalid payloads
                }
            };
            this.ws.onclose = () => {
                this.connected$.next(false);
                this.ws = null;
                this.scheduleReconnect();
            };
            this.ws.onerror = () => {
                // Error triggers onclose in many browsers; ensure we try reconnect flow
                if (this.ws) try { this.ws.close(); } catch (_) {}
            };
        } catch (e) {
            this.scheduleReconnect();
        }
    }

    private scheduleReconnect(): void {
        this.reconnectAttempts++;
        const delay = Math.min(30000, 500 * 2 ** (this.reconnectAttempts - 1)); // exponential backoff up to 30s
        timer(delay).pipe(takeUntil(this.destroy$)).subscribe(() => this.connect());
    }

    private closeSocket(): void {
        if (this.ws) {
            try { this.ws.close(); } catch (_) {}
            this.ws = null;
        }
        this.connected$.next(false);
    }

    private safeSend(payload: string): void {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        try {
            this.ws.send(payload);
        } catch (_) {
            // ignore
        }
    }

    private enqueueCommand(payload: string): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.safeSend(payload);
        } else {
            this.pendingCmds.push(payload);
        }
    }

    /**
     * Subscribe to events for a specific voiceId. When the first consumer subscribes
     * the service will send a subscribe command to the server. When the last consumer
     * unsubscribes, it will send an unsubscribe command.
     */
    subscribeVoice(voiceId: string): Observable<RefGenEvent> {
        let entry = this.voiceMap.get(voiceId);
        if (!entry) {
            entry = { subj: new Subject<RefGenEvent>(), ref: 0 };
            this.voiceMap.set(voiceId, entry);
        }
        entry.ref += 1;

        // Send subscribe command
        this.enqueueCommand(JSON.stringify({ action: 'subscribe', voice_id: voiceId }));

        const observable = new Observable<RefGenEvent>(subscriber => {
            const sub = entry!.subj.subscribe(subscriber);
            return () => {
                sub.unsubscribe();
                const current = this.voiceMap.get(voiceId);
                if (current) {
                    current.ref -= 1;
                    if (current.ref <= 0) {
                        // send unsubscribe and cleanup
                        this.enqueueCommand(JSON.stringify({ action: 'unsubscribe', voice_id: voiceId }));
                        current.subj.complete();
                        this.voiceMap.delete(voiceId);
                    }
                }
            };
        });

        return observable.pipe(takeUntil(this.destroy$));
    }

}
