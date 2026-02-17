import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TabsModule } from 'primeng/tabs';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { InputTextModule } from 'primeng/inputtext';
import { SelectButtonModule } from 'primeng/selectbutton';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { TtsApiService } from '../../services/tts-api.service';
import { AudioPlayerService } from '../../services/audio-player.service';
import { ModelSize, TtsMode, GenerationHistoryItem } from '../../models/tts.models';

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
        SelectButtonModule,
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

    // Form state
    text = '';
    language = 'German';
    modelSize: ModelSize = '1.7b';
    currentMode: TtsMode = 'custom_voice';

    // Base mode
    referenceAudio = 'chatbot_male.wav';
    refText = '';

    // Custom voice
    selectedSpeaker = 'Chelsie';
    customInstruct = '';

    // Voice design
    voiceDescription = '';

    // Dropdowns
    languages = signal<string[]>([]);
    speakers = signal<string[]>([]);
    referenceAudios = ['chatbot_male.wav', 'book_reader_male.wav', 'podcast_male.wav'];

    modelSizeOptions = [
        { label: '0.6B – Fast', value: '0.6b' },
        { label: '1.7B – Quality', value: '1.7b' },
    ];

    // State
    isGenerating = signal(false);
    history = signal<GenerationHistoryItem[]>([]);

    ngOnInit(): void {
        this.ttsApi.getLanguages().subscribe({
            next: res => this.languages.set(res.languages),
            error: () => this.languages.set(['German', 'English', 'French', 'Spanish']),
        });
        this.ttsApi.getSpeakers().subscribe({
            next: res => this.speakers.set(res.speakers),
            error: () =>
                this.speakers.set([
                    'Chelsie', 'Aidan', 'Serena', 'Ethan', 'Vivian',
                    'Lucas', 'Aria', 'Oliver', 'Isabel', 'Caleb', 'eric',
                ]),
        });
    }

    onTabChange(index: number): void {
        const modes: TtsMode[] = ['custom_voice', 'base', 'voice_design'];
        this.currentMode = modes[index] || 'custom_voice';

        // Voice design only supports 1.7B
        if (this.currentMode === 'voice_design') {
            this.modelSize = '1.7b';
        }
    }

    selectSpeaker(speaker: string): void {
        this.selectedSpeaker = speaker;
    }

    getSpeakerInitials(name: string): string {
        return name.charAt(0).toUpperCase();
    }

    getSpeakerColor(name: string): string {
        const colors = [
            '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b',
            '#ef4444', '#ec4899', '#6366f1', '#14b8a6',
            '#f97316', '#84cc16', '#a855f7',
        ];
        let hash = 0;
        for (const char of name) hash = char.charCodeAt(0) + ((hash << 5) - hash);
        return colors[Math.abs(hash) % colors.length];
    }

    generate(): void {
        if (!this.text.trim()) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Text fehlt',
                detail: 'Bitte gib einen Text zum Vorlesen ein.',
            });
            return;
        }

        this.isGenerating.set(true);

        let request$;

        switch (this.currentMode) {
            case 'base':
                request$ = this.ttsApi.generateBase(
                    {
                        text: this.text,
                        language: this.language,
                        reference_audio: this.referenceAudio,
                        ref_text: this.refText || null,
                    },
                    this.modelSize
                );
                break;

            case 'voice_design':
                if (!this.voiceDescription.trim()) {
                    this.messageService.add({
                        severity: 'warn',
                        summary: 'Beschreibung fehlt',
                        detail: 'Bitte beschreibe die gewünschte Stimme.',
                    });
                    this.isGenerating.set(false);
                    return;
                }
                request$ = this.ttsApi.generateVoiceDesign({
                    text: this.text,
                    language: this.language,
                    instruct: this.voiceDescription,
                });
                break;

            case 'custom_voice':
                request$ = this.ttsApi.generateCustomVoice(
                    {
                        text: this.text,
                        language: this.language,
                        speaker: this.selectedSpeaker,
                        instruct: this.customInstruct || null,
                    },
                    this.modelSize
                );
                break;
        }

        request$.subscribe({
            next: (blob: Blob) => {
                this.audioPlayer.loadAudio(blob);
                this.isGenerating.set(false);

                // Add to history
                const item: GenerationHistoryItem = {
                    id: crypto.randomUUID(),
                    text: this.text.substring(0, 80),
                    mode: this.currentMode,
                    modelSize: this.modelSize,
                    language: this.language,
                    speaker: this.currentMode === 'custom_voice' ? this.selectedSpeaker : undefined,
                    audioUrl: this.audioPlayer.audioUrl() || '',
                    timestamp: new Date(),
                };
                this.history.update(h => [item, ...h].slice(0, 20));

                this.messageService.add({
                    severity: 'success',
                    summary: 'Audio generiert',
                    detail: 'Die Sprachausgabe wurde erfolgreich erstellt.',
                });
            },
            error: (err: unknown) => {
                this.isGenerating.set(false);
                const errorDetail = err instanceof Error ? err.message : 'Verbindung zum Backend fehlgeschlagen.';
                this.messageService.add({
                    severity: 'error',
                    summary: 'Fehler',
                    detail: errorDetail,
                });
            },
        });
    }

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
