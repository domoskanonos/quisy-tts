import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { DialogModule } from 'primeng/dialog';
import { SelectModule } from 'primeng/select';
import { InputTextModule } from 'primeng/inputtext';
import { TextareaModule } from 'primeng/textarea';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';
import { TtsApiService } from '../../services/tts-api.service';
import { VoiceGenerationService } from '../../services/voice-generation.service';
import { Voice } from '../../models/tts.models';

@Component({
    selector: 'app-voices',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        FormsModule,
        DialogModule,
        SelectModule,
        InputTextModule,
        TextareaModule,
        ButtonModule,
        ToastModule,
        ConfirmDialogModule,
    ],
    providers: [ConfirmationService],
    templateUrl: './voices.component.html',
    styleUrl: './voices.component.scss',
})
export class VoicesComponent implements OnInit {
    public readonly ttsApi = inject(TtsApiService);
    private readonly voiceGen = inject(VoiceGenerationService);
    private readonly router = inject(Router);
    private readonly messageService = inject(MessageService);
    private readonly confirmService = inject(ConfirmationService);

    voices = signal<Voice[]>([]);
    isLoading = signal(true);

    // Dialog state
    showCreateDialog = signal(false);
    showEditDialog = signal(false);
    newVoiceName = '';
    newVoiceText = '';
    newVoiceInstruct = '';
    // system_prompt removed
    newVoiceLanguage = 'german';
    editVoice: Voice | null = null;
    editName = '';
    editText = '';
    editInstruct = '';
    // system_prompt removed
    editLanguage = 'german';
    selectedAudioFile: File | null = null;
    isUploading = signal(false);
    generatingVoiceId = signal<string | null>(null);

    readonly languageOptions = [
        { value: 'german', label: 'Deutsch', flag: '🇩🇪' },
        { value: 'english', label: 'English', flag: '🇬🇧' },
        { value: 'french', label: 'Français', flag: '🇫🇷' },
        { value: 'spanish', label: 'Español', flag: '🇪🇸' },
        { value: 'italian', label: 'Italiano', flag: '🇮🇹' },
        { value: 'portuguese', label: 'Português', flag: '🇵🇹' },
        { value: 'russian', label: 'Русский', flag: '🇷🇺' },
        { value: 'japanese', label: '日本語', flag: '🇯🇵' },
        { value: 'korean', label: '한국어', flag: '🇰🇷' },
        { value: 'chinese', label: '中文', flag: '🇨🇳' },
    ];



    ngOnInit(): void {
        this.loadVoices();
    }

    loadVoices(): void {
        this.isLoading.set(true);
        this.ttsApi.getVoices().subscribe({
            next: res => {
                this.voices.set(res.voices);
                this.isLoading.set(false);
            },
            error: () => {
                this.voices.set([]);
                this.isLoading.set(false);
            },
        });
    }

    // ─── Create ─────────────────────────────────────────────────

    openCreateDialog(): void {
        this.newVoiceName = '';
        this.newVoiceText = '';
        this.newVoiceInstruct = '';
        // system_prompt removed
        this.newVoiceLanguage = 'german';
        this.selectedAudioFile = null;
        this.showCreateDialog.set(true);
    }

    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            this.selectedAudioFile = input.files[0];
        }
    }

    createVoice(): void {
        if (!this.newVoiceName.trim() || !this.newVoiceText.trim()) return;

        this.ttsApi.createVoice({
            name: this.newVoiceName,
            example_text: this.newVoiceText,
            instruct: this.newVoiceInstruct.trim() || null,
            language: this.newVoiceLanguage,
        }).subscribe({
            next: voice => {
                if (this.selectedAudioFile) {
                    this.isUploading.set(true);
                    this.ttsApi.uploadVoiceAudio(voice.id, this.selectedAudioFile).subscribe({
                        next: () => {
                            this.isUploading.set(false);
                            this.showCreateDialog.set(false);
                            this.loadVoices();
                            this.messageService.add({
                                severity: 'success',
                                summary: 'Stimme erstellt',
                                detail: `"${voice.name}" wurde mit Audio erstellt.`,
                            });
                        },
                        error: () => {
                            this.isUploading.set(false);
                            this.showCreateDialog.set(false);
                            this.loadVoices();
                            this.messageService.add({
                                severity: 'warn',
                                summary: 'Stimme erstellt',
                                detail: 'Stimme erstellt, aber Audio-Upload fehlgeschlagen.',
                            });
                        },
                    });
                } else {
                    this.showCreateDialog.set(false);
                    this.loadVoices();
                    this.messageService.add({
                        severity: 'success',
                        summary: 'Stimme erstellt',
                        detail: `"${voice.name}" wurde erfolgreich erstellt.`,
                    });
                }
            },
            error: () => {
                this.messageService.add({
                    severity: 'error',
                    summary: 'Fehler',
                    detail: 'Stimme konnte nicht erstellt werden.',
                });
            },
        });
    }

    // ─── Edit ───────────────────────────────────────────────────

    openEditDialog(voice: Voice): void {
        this.editVoice = voice;
        this.editName = voice.name;
        this.editText = voice.example_text;
        this.editInstruct = voice.instruct || '';
        // system_prompt removed
        this.editLanguage = voice.language || 'german';
        this.selectedAudioFile = null;
        this.showEditDialog.set(true);
    }

    closeEditPanel(): void {
        this.showEditDialog.set(false);
        this.selectedAudioFile = null;
    }

    generatePreview(): void {
        if (!this.editVoice) return;
        const voice = this.editVoice;
        if (this.generatingVoiceId()) return;
        if (!voice.instruct) {
            this.messageService.add({ severity: 'warn', summary: 'Instruct fehlt', detail: 'Diese Stimme hat keinen Instruct-Text. Bitte bearbeite die Stimme zuerst.' });
            return;
        }

        this.generatingVoiceId.set(voice.id);
        this.messageService.add({ severity: 'info', summary: 'Generierung', detail: 'Erzeuge Beispiel-Audio...' });

        // Force regeneration when user explicitly requests preview generation
        this.voiceGen.ensureVoiceAudio(voice, true).subscribe({
            next: (updated: Voice) => {
                this.generatingVoiceId.set(null);
                const audio = new Audio(this.ttsApi.getVoiceAudioUrl(updated.id));
                audio.play().catch(err => console.warn('Playback failed for uploaded audio, but generation succeeded', err));
                this.loadVoices();
                this.messageService.add({ severity: 'success', summary: 'Audio erstellt', detail: `Referenz-Audio für "${voice.name}" wurde generiert und gespeichert.` });
            },
            error: () => {
                this.generatingVoiceId.set(null);
                this.messageService.add({ severity: 'error', summary: 'Fehler', detail: 'Audio konnte nicht generiert werden. Ist das Backend erreichbar?' });
            }
        });
    }

    saveEdit(): void {
        if (!this.editVoice || !this.editName.trim() || !this.editText.trim()) return;

        this.ttsApi.updateVoice(this.editVoice.id, {
            name: this.editName,
            example_text: this.editText,
            instruct: this.editInstruct.trim() || null,
            language: this.editLanguage,
        }).subscribe({
            next: () => {
                if (this.selectedAudioFile) {
                    this.isUploading.set(true);
                    this.ttsApi.uploadVoiceAudio(this.editVoice!.id, this.selectedAudioFile!).subscribe({
                        next: () => {
                            this.isUploading.set(false);
                            this.showEditDialog.set(false);
                            this.loadVoices();
                            this.messageService.add({ severity: 'success', summary: 'Aktualisiert', detail: 'Stimme und Audio aktualisiert.' });
                        },
                        error: () => {
                            this.isUploading.set(false);
                            this.showEditDialog.set(false);
                            this.loadVoices();
                            this.messageService.add({ severity: 'warn', summary: 'Teilweise', detail: 'Stimme aktualisiert, Audio-Upload fehlgeschlagen.' });
                        },
                    });
                } else {
                    this.showEditDialog.set(false);
                    this.loadVoices();
                    this.messageService.add({ severity: 'success', summary: 'Aktualisiert', detail: 'Stimme wurde aktualisiert.' });
                }
            },
            error: () => {
                this.messageService.add({ severity: 'error', summary: 'Fehler', detail: 'Aktualisierung fehlgeschlagen.' });
            },
        });
    }

    // ─── Delete ─────────────────────────────────────────────────

    confirmDelete(voice: Voice): void {
        this.confirmService.confirm({
            message: `Möchtest du die Stimme "${voice.name}" wirklich löschen?`,
            header: 'Stimme löschen',
            icon: 'pi pi-exclamation-triangle',
            acceptLabel: 'Löschen',
            rejectLabel: 'Abbrechen',
            accept: () => this.deleteVoice(voice),
        });
    }

    deleteVoice(voice: Voice): void {
        this.ttsApi.deleteVoice(voice.id).subscribe({
            next: () => {
                this.loadVoices();
                this.messageService.add({
                    severity: 'success',
                    summary: 'Gelöscht',
                    detail: `"${voice.name}" wurde gelöscht.`,
                });
            },
            error: () => {
                this.messageService.add({ severity: 'error', summary: 'Fehler', detail: 'Löschen fehlgeschlagen.' });
            },
        });
    }

    // ─── Audio Preview & Generate ───────────────────────────────

    playOrGenerate(voice: Voice): void {
        if (voice.audio_filename) {
            // Audio exists → offer to regenerate if user holds modifier (Shift) or always play
            const audio = new Audio(this.ttsApi.getVoiceAudioUrl(voice.id));
            audio.play();
        } else {
            // No audio → generate, play, and save (reuse generation helper)
            this.generateAndPlay(voice);
        }
    }

    private generateAndPlay(voice: Voice, force: boolean = false): void {
        if (this.generatingVoiceId()) return; // already generating
        if (!voice.instruct) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Instruct fehlt',
                detail: 'Diese Stimme hat keinen Instruct-Text. Bitte bearbeite die Stimme zuerst.',
            });
            return;
        }

        this.generatingVoiceId.set(voice.id);

        this.messageService.add({ severity: 'info', summary: 'Generierung', detail: 'Erzeuge Beispiel-Audio...' });

        // Use unified generation service which handles generation + upload
        this.voiceGen.ensureVoiceAudio(voice, force).subscribe({
            next: (updated: Voice) => {
                this.generatingVoiceId.set(null);
                // Play the newly uploaded audio; if cross-origin or auth prevents playing the direct URL,
                // fetch blob via generateVoiceDesign endpoint would be alternative, but we assume public endpoint here.
                const audio = new Audio(this.ttsApi.getVoiceAudioUrl(updated.id));
                audio.play().catch(err => console.warn('Playback failed for uploaded audio, but generation succeeded', err));
                this.loadVoices();
                this.messageService.add({
                    severity: 'success',
                    summary: 'Audio erstellt',
                    detail: `Referenz-Audio für "${voice.name}" wurde generiert und gespeichert.`,
                });
            },
            error: () => {
                this.generatingVoiceId.set(null);
                this.messageService.add({
                    severity: 'error',
                    summary: 'Fehler',
                    detail: 'Audio konnte nicht generiert werden. Ist das Backend erreichbar?',
                });
            }
        });
    }

    // ─── Helpers ────────────────────────────────────────────────



    getInitials(name: string): string {
        return name.charAt(0).toUpperCase();
    }

    getColor(name: string): string {
        const colors = [
            '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b',
            '#ef4444', '#ec4899', '#6366f1', '#14b8a6',
            '#f97316', '#84cc16', '#a855f7',
        ];
        let hash = 0;
        for (const char of name) hash = char.charCodeAt(0) + ((hash << 5) - hash);
        return colors[Math.abs(hash) % colors.length];
    }



    getLanguageFlag(lang: string): string {
        const found = this.languageOptions.find(l => l.value === lang);
        return found ? found.flag : '🌐';
    }

    getLanguageLabel(lang: string): string {
        const found = this.languageOptions.find(l => l.value === lang);
        return found ? found.label : lang;
    }
}
