import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { TextareaModule } from 'primeng/textarea';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';
import { TtsApiService } from '../../services/tts-api.service';
import { Voice } from '../../models/tts.models';

@Component({
    selector: 'app-voices',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        DialogModule,
        InputTextModule,
        TextareaModule,
        ToastModule,
        ConfirmDialogModule,
    ],
    providers: [MessageService, ConfirmationService],
    templateUrl: './voices.component.html',
    styleUrl: './voices.component.scss',
})
export class VoicesComponent implements OnInit {
    private readonly ttsApi = inject(TtsApiService);
    private readonly router = inject(Router);
    private readonly messageService = inject(MessageService);
    private readonly confirmService = inject(ConfirmationService);

    voices = signal<Voice[]>([]);
    builtInSpeakers = signal<string[]>([]);
    isLoading = signal(true);

    // Dialog state
    showCreateDialog = signal(false);
    showEditDialog = signal(false);
    newVoiceName = '';
    newVoiceText = '';
    editVoice: Voice | null = null;
    editName = '';
    editText = '';
    selectedAudioFile: File | null = null;
    isUploading = signal(false);

    readonly speakerDescriptions: Record<string, string> = {
        Chelsie: 'Warm, freundliche weibliche Stimme',
        Aidan: 'Klare, professionelle männliche Stimme',
        Serena: 'Ruhige, elegante weibliche Stimme',
        Ethan: 'Dynamische, energische männliche Stimme',
        Vivian: 'Ausdrucksstarke, lebendige weibliche Stimme',
        Lucas: 'Tiefe, vertrauenswürdige männliche Stimme',
        Aria: 'Sanfte, melodische weibliche Stimme',
        Oliver: 'Natürliche, warme männliche Stimme',
        Isabel: 'Elegante, kultivierte weibliche Stimme',
        Caleb: 'Jugendliche, frische männliche Stimme',
        eric: 'Casual, entspannte männliche Stimme',
    };

    ngOnInit(): void {
        this.loadVoices();
        this.ttsApi.getSpeakers().subscribe({
            next: res => this.builtInSpeakers.set(res.speakers),
            error: () =>
                this.builtInSpeakers.set([
                    'Chelsie', 'Aidan', 'Serena', 'Ethan', 'Vivian',
                    'Lucas', 'Aria', 'Oliver', 'Isabel', 'Caleb', 'eric',
                ]),
        });
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
        this.selectedAudioFile = null;
        this.showEditDialog.set(true);
    }

    saveEdit(): void {
        if (!this.editVoice || !this.editName.trim() || !this.editText.trim()) return;

        this.ttsApi.updateVoice(this.editVoice.id, {
            name: this.editName,
            example_text: this.editText,
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

    // ─── Audio Preview ──────────────────────────────────────────

    playPreview(voice: Voice): void {
        if (!voice.audio_filename) return;
        const audio = new Audio(this.ttsApi.getVoiceAudioUrl(voice.id));
        audio.play();
    }

    // ─── Helpers ────────────────────────────────────────────────

    trySpeaker(speaker: string): void {
        this.router.navigate(['/synthesis'], { queryParams: { speaker } });
    }

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

    getDescription(name: string): string {
        return this.speakerDescriptions[name] || 'KI-generierte Stimme';
    }
}
