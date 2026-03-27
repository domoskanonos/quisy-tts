import { Component, inject, OnInit, signal, effect, computed, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TabsModule } from 'primeng/tabs';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { InputTextModule } from 'primeng/inputtext';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { TtsApiService } from '../../services/tts-api.service';
import { AudioPlayerService } from '../../services/audio-player.service';
import { AudioPlayerComponent } from '../../components/audio-player/audio-player.component';
import { SettingsService } from '../../services/settings.service';
import { ModelSize, TtsMode, GenerationHistoryItem, Voice } from '../../models/tts.models';
import { StatusService } from '../../services/status.service';
import { VoiceGenerationService } from '../../services/voice-generation.service';

@Component({
    selector: 'app-synthesis',
    standalone: true,
    changeDetection: ChangeDetectionStrategy.OnPush,
    imports: [
        CommonModule,
        FormsModule,
        TabsModule,
        SelectModule,
        TextareaModule,
        InputTextModule,
        ToastModule,
        AudioPlayerComponent,
    ],
    templateUrl: './synthesis.component.html',
    styleUrl: './synthesis.component.scss',
})
export class SynthesisComponent implements OnInit {
    private readonly ttsApi = inject(TtsApiService);
    readonly audioPlayer = inject(AudioPlayerService);
    private readonly messageService = inject(MessageService);
    private readonly settingsService = inject(SettingsService);
    private readonly voiceGen = inject(VoiceGenerationService);
    private readonly statusService = inject(StatusService);

    // Form state
    text = '';

    // Settings (Sidebar)
    voices = signal<Voice[]>([]);

    // Computed sorted voices based on default language
    sortedVoices = computed(() => {
        const allVoices = this.voices();
        const defaultLang = this.settingsService.defaultLanguage();

        if (!defaultLang) return allVoices;

        return [...allVoices].sort((a, b) => {
            const aIsDefault = a.language === defaultLang;
            const bIsDefault = b.language === defaultLang;

            if (aIsDefault && !bIsDefault) return -1;
            if (!aIsDefault && bIsDefault) return 1;

            // Secondary sort by name
            return a.name.localeCompare(b.name);
        });
    });

    selectedVoice: Voice | null = null;
    selectedModel: ModelSize = this.settingsService.defaultModel() as ModelSize;

    // Model Options
    modelOptions = [
        { label: 'Standard (0.6B)', value: '0.6b' },
        { label: 'High Quality (1.7B)', value: '1.7b' },
    ];


    // State
    isGenerating = signal(false);
    isPlayingExample = signal(false);
    backendOnline = signal<boolean | null>(null);
    history = signal<GenerationHistoryItem[]>([]);
    // Reference-generation progress
    refGenProgress = signal(0);
    refGenMessage = signal('');

    ngOnInit(): void {
        this.checkBackend();
    }

    private checkBackend(): void {
        this.ttsApi.getStatus().subscribe({
            next: () => {
                this.backendOnline.set(true);
                this.loadVoices();
            },
            error: () => {
                this.backendOnline.set(false);
            },
        });
    }

    private loadVoices(): void {
        this.ttsApi.getVoices().subscribe({
            next: res => {
                this.voices.set(res.voices);

                // Select default voice logic
                const savedVoiceId = this.settingsService.defaultVoiceId();
                if (savedVoiceId) {
                    const savedVoice = res.voices.find(v => v.id === savedVoiceId);
                    if (savedVoice) {
                        this.selectedVoice = savedVoice;
                        return;
                    }
                }

                // Fallback
                const defaultVoice = res.voices.find(v => v.is_default) || res.voices[0];
                if (defaultVoice) {
                    this.selectedVoice = defaultVoice;
                }
            },
            error: () => {
                this.messageService.add({ severity: 'error', summary: 'Fehler', detail: 'Stimmen konnten nicht geladen werden.' });
            },
        });
    }

    retryConnection(): void {
        this.backendOnline.set(null);
        this.checkBackend();
    }

    generate(): void {
        if (!this.text.trim()) {
            this.messageService.add({ severity: 'warn', summary: 'Text fehlt', detail: 'Bitte gib einen Text ein.' });
            return;
        }

        if (!this.selectedVoice) {
            this.messageService.add({ severity: 'warn', summary: 'Stimme fehlt', detail: 'Bitte wähle eine Stimme aus.' });
            return;
        }

        // If voice has no audio yet, attempt to generate and persist it first (unified behavior with Voices page)
        if (!this.selectedVoice.audio_filename) {
            // If there's no instruct available, we cannot generate via Voice Design
            if (!this.selectedVoice.instruct) {
                this.messageService.add({
                    severity: 'warn',
                    summary: 'Kein Audio',
                    detail: 'Diese Stimme hat keine Audiodatei für Cloning (Base Mode) und keinen Instruct-Text zum Generieren. Bitte bearbeite die Stimme in der Voice Library.'
                });
                return;
            }

            this.isGenerating.set(true);
            // Generate reference audio first, then continue with base generation
        // Subscribe to WS status for the selected voice to show progress
            try {
            const statusSvc = this.statusService;
            const statusSub = statusSvc.subscribeVoice(this.selectedVoice.id).subscribe((ev: any) => {
                // Update UI based on event
                if (ev.status === 'running' || ev.status === 'queued' || ev.status === 'progress') {
                    // Show a progress toast or update in-place: replace the info toast
                    const percent = ev.progress ?? 0;
                    this.refGenProgress.set(percent);
                    this.refGenMessage.set(ev.message || ev.status || 'running');
                    this.messageService.clear();
                    this.messageService.add({ severity: 'info', summary: 'Generierung', detail: `Referenz-Audio: ${this.refGenMessage()} (${percent}%)` });
                }
                if (ev.status === 'done') {
                    this.refGenProgress.set(100);
                    this.refGenMessage.set('completed');
                    this.messageService.clear();
                    this.messageService.add({ severity: 'success', summary: 'Generierung', detail: 'Referenz-Audio erfolgreich erstellt.' });
                    // Refresh voice and proceed
                    this.ttsApi.getVoice(this.selectedVoice!.id).subscribe(v => {
                        this.voices.update(vs => vs.map(x => x.id === v.id ? v : x));
                        this.selectedVoice = v;
                        this.callGenerateBase();
                        this.isGenerating.set(false);
                    });
                    statusSub.unsubscribe();
                }
                if (ev.status === 'failed') {
                    this.refGenProgress.set(0);
                    this.refGenMessage.set('failed');
                    this.messageService.clear();
                    this.messageService.add({ severity: 'error', summary: 'Fehler', detail: 'Referenz-Audio konnte nicht generiert werden.' });
                    this.isGenerating.set(false);
                    statusSub.unsubscribe();
                }
            });

            // Trigger the backend generation (fire-and-forget)
            this.voiceGen.ensureVoiceAudio(this.selectedVoice, false).subscribe({ next: () => {}, error: () => {} });
        } catch (e) {
            // Fallback to previous polling approach
            this.voiceGen.ensureVoiceAudio(this.selectedVoice).subscribe({
                next: (updated: Voice) => {
                    // Update voices and selectedVoice with persisted audio
                    this.voices.update(vs => vs.map(v => v.id === updated.id ? updated : v));
                    this.selectedVoice = updated;
                    // clear the info toast and now call base generation (reference will be voice ID)
                    this.messageService.clear();
                    this.messageService.add({ severity: 'success', summary: 'Generierung', detail: 'Referenz-Audio erfolgreich erstellt.' });
                    this.callGenerateBase();
                },
                error: () => {
                    this.isGenerating.set(false);
                    this.messageService.clear();
                    this.messageService.add({ severity: 'error', summary: 'Fehler', detail: 'Referenz-Audio konnte nicht generiert werden.' });
                }
            });
        }

        // Remove the info toast after generation completes (success path cleans up implicitly when UI updates)

        // Show a user-facing loading toast while the backend generates the reference audio
        this.messageService.add({ severity: 'info', summary: 'Generierung', detail: 'Referenz-Audio wird erzeugt, bitte warten...' });

            return;
        }

        // If we already have reference audio, generate directly
        this.isGenerating.set(true);
        this.callGenerateBase();
    }

    private callGenerateBase(): void {
        if (!this.selectedVoice) return;

        this.ttsApi.generateBase(
            {
                text: this.text,
                language: this.selectedVoice.language || 'german',
                // API now expects a voice ID (not a filename)
                reference_audio: this.selectedVoice.id,
                ref_text: this.selectedVoice.example_text || null,
            },
            this.selectedModel
        ).subscribe({
            next: (blob: Blob) => {
                this.audioPlayer.loadAudio(blob);
                this.isGenerating.set(false);
                this.addToHistory();
            },
            error: (err: unknown) => {
                this.isGenerating.set(false);
                // Try to surface backend detail if available
                const detail = (err as any)?.error?.detail || 'Generierung fehlgeschlagen.';
                this.messageService.add({ severity: 'error', summary: 'Fehler', detail });
            },
        });
    }

    playExample(): void {
        const voice = this.selectedVoice;
        if (!voice) return;

        // If voice has audio, try to play it
        if (voice.audio_filename) {
            const url = this.ttsApi.getVoiceAudioUrl(voice.id);
            const audio = new Audio(url);

            this.isPlayingExample.set(true);

            // Handle errors (e.g. 404 Not Found) by falling back to generation
            const errorHandler = () => {
                console.warn(`Audio file for ${voice.name} not found or failed to load. Generating new example...`);
                // Remove listeners to avoid double triggers if possible, though new Audio instance is mostly safe
                audio.onended = null;
                audio.onerror = null;
                // Use unified generation service when available
                if (this.voiceGen && this.voiceGen.ensureVoiceAudio) {
                    this.voiceGen.ensureVoiceAudio(voice).subscribe({
                        next: (updated: any) => {
                            this.voices.update(current => current.map(v => v.id === updated.id ? updated : v));
                            this.selectedVoice = updated;
                            // play uploaded audio
                            const url = this.ttsApi.getVoiceAudioUrl(updated.id);
                            const a = new Audio(url);
                            a.play();
                            a.onended = () => this.isPlayingExample.set(false);
                        },
                        error: () => {
                            // fallback to previous method
                            this.generateExampleAudio(voice);
                        }
                    });
                } else {
                    this.generateExampleAudio(voice);
                }
            };

            audio.onerror = errorHandler;

            const playPromise = audio.play();
            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        // Playback started successfully
                    })
                    .catch(error => {
                        console.warn("Audio playback prevented or failed:", error);
                        errorHandler();
                    });
            }

            audio.onended = () => this.isPlayingExample.set(false);
            return;
        }

        // Otherwise generate it using unified generation service if present
        if (this.voiceGen && this.voiceGen.ensureVoiceAudio) {
            this.isPlayingExample.set(true);
            this.voiceGen.ensureVoiceAudio(voice).subscribe({
                next: (updated: any) => {
                    this.voices.update(current => current.map(v => v.id === updated.id ? updated : v));
                    this.selectedVoice = updated;
                    const url = this.ttsApi.getVoiceAudioUrl(updated.id);
                    const a = new Audio(url);
                    a.play();
                    a.onended = () => this.isPlayingExample.set(false);
                },
                error: () => {
                    this.isPlayingExample.set(false);
                    this.messageService.add({ severity: 'error', summary: 'Fehler', detail: 'Beispiel konnte nicht generiert werden.' });
                }
            });
        } else {
            this.generateExampleAudio(voice);
        }
    }

    private generateExampleAudio(voice: Voice): void {
        this.isPlayingExample.set(true);

        // Use VoiceDesign generation (prompt-based) as requested
        this.ttsApi.generateVoiceDesign({
            text: voice.example_text || 'Dies ist eine Hörprobe meiner Stimme.',
            language: voice.language || 'german',
            instruct: voice.instruct || '',
        }).subscribe({
            next: (blob) => {
                // 1. Play locally
                const url = URL.createObjectURL(blob);
                const audio = new Audio(url);
                audio.play();
                audio.onended = () => {
                    this.isPlayingExample.set(false);
                    URL.revokeObjectURL(url);
                };

                // 2. Upload and Persist
                const file = new File([blob], `voice_${voice.id}.wav`, { type: 'audio/wav' });
                this.ttsApi.uploadVoiceAudio(voice.id, file).subscribe({
                    next: (updatedVoice) => {
                        // Update local state so next time we play the file
                        this.voices.update(currentVoices =>
                            currentVoices.map(v => v.id === updatedVoice.id ? updatedVoice : v)
                        );

                        // Also update selectedVoice if it matches
                        if (this.selectedVoice?.id === updatedVoice.id) {
                            this.selectedVoice = updatedVoice;
                        }

                        this.messageService.add({ severity: 'success', summary: 'Gespeichert', detail: 'Hörprobe wurde gespeichert.' });
                    },
                    error: () => {
                        console.warn('Failed to upload generated example audio.');
                    }
                });
            },
            error: () => {
                this.isPlayingExample.set(false);
                this.messageService.add({ severity: 'error', summary: 'Fehler', detail: 'Beispiel konnte nicht generiert werden.' });
            }
        });
    }

    // History helper
    private addToHistory(): void {
        const item: GenerationHistoryItem = {
            id: crypto.randomUUID(),
            text: this.text.substring(0, 80),
            mode: 'custom_voice',
            modelSize: this.selectedModel,
            language: this.selectedVoice?.language || '?',
            speaker: this.selectedVoice?.name,
            audioUrl: this.audioPlayer.audioUrl() || '',
            timestamp: new Date(),
        };
        this.history.update(h => [item, ...h].slice(0, 20));
    }

    // Player helpers
    getProgressPercent(): number {
        const dur = this.audioPlayer.duration();
        if (!dur) return 0;
        return (this.audioPlayer.currentTime() / dur) * 100;
    }

    onWaveformClick(event: MouseEvent, container: HTMLElement): void {
        const rect = container.getBoundingClientRect();
        const percent = ((event.clientX - rect.left) / rect.width) * 100;
        this.audioPlayer.seekPercent(percent);
    }

    onVoiceChange(voice: Voice): void {
        this.selectedVoice = voice;
        this.settingsService.setDefaultVoiceId(voice.id);

        // Background generation if needed
        if (!voice.audio_filename) {
            // Trigger background generation; prefer client-side service when available
            this.messageService.add({ severity: 'info', summary: 'Generierung', detail: 'Hintergrund-Generierung wird gestartet.' });
            if (this.voiceGen && this.voiceGen.ensureVoiceAudio) {
                this.voiceGen.ensureVoiceAudio(voice).subscribe({
                    next: (updated: any) => {
                        this.voices.update(vs => vs.map(v => v.id === updated.id ? updated : v));
                        this.messageService.add({ severity: 'success', summary: 'Generierung', detail: 'Hörprobe wurde generiert und gespeichert.' });
                    },
                    error: (err: unknown) => {
                        console.warn('Failed to trigger background generation', err);
                        this.messageService.add({ severity: 'warn', summary: 'Generierung fehlgeschlagen', detail: 'Hintergrund-Generierung konnte nicht gestartet werden.' });
                    }
                });
            } else {
                // Fallback: call backend ensure and then poll for audio availability
                this.voiceGen.ensureVoiceAudioById(voice.id).subscribe({
                    next: (updated: Voice) => {
                        this.voices.update(vs => vs.map(v => v.id === updated.id ? updated : v));
                        this.messageService.add({ severity: 'success', summary: 'Generierung', detail: 'Hörprobe wurde generiert und gespeichert.' });
                    },
                    error: (err: unknown) => {
                        console.warn('Failed to poll for generated audio', err);
                        this.messageService.add({ severity: 'warn', summary: 'Fehler', detail: 'Hintergrund-Generierung konnte nicht abgeschlossen werden.' });
                    }
                });
            }
        }
    }
}
