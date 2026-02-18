import { Component, inject, OnInit, signal, effect, computed } from '@angular/core';
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
import { SettingsService } from '../../services/settings.service';
import { ModelSize, TtsMode, GenerationHistoryItem, Voice } from '../../models/tts.models';

@Component({
    selector: 'app-synthesis',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        TabsModule,
        SelectModule,
        TextareaModule,
        InputTextModule,
        ToastModule,
    ],
    providers: [MessageService],
    templateUrl: './synthesis.component.html',
    styleUrl: './synthesis.component.scss',
})
export class SynthesisComponent implements OnInit {
    private readonly ttsApi = inject(TtsApiService);
    readonly audioPlayer = inject(AudioPlayerService);
    private readonly messageService = inject(MessageService);
    private readonly settingsService = inject(SettingsService);

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
    selectedModel: ModelSize = '1.7b';

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
                // Select default voice if available
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

        this.isGenerating.set(true);

        if (!this.selectedVoice.audio_filename) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Kein Audio',
                detail: 'Diese Stimme hat keine Audiodatei für Cloning (Base Mode).'
            });
            return;
        }

        this.isGenerating.set(true);

        this.ttsApi.generateBase(
            {
                text: this.text,
                language: this.selectedVoice.language || 'german',
                reference_audio: this.selectedVoice.audio_filename,
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
                this.messageService.add({ severity: 'error', summary: 'Fehler', detail: 'Generierung fehlgeschlagen.' });
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
                this.generateExampleAudio(voice);
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

        // Otherwise generate it
        this.generateExampleAudio(voice);
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
}
