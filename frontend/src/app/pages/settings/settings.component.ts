import { Component, inject, OnInit, signal, effect, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SelectModule } from 'primeng/select';
import { CardModule } from 'primeng/card';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { SettingsService } from '../../services/settings.service';
import { TtsApiService } from '../../services/tts-api.service';
import { Voice } from '../../models/tts.models';

@Component({
    selector: 'app-settings',
    standalone: true,
    imports: [CommonModule, FormsModule, SelectModule, CardModule, ToastModule],
    templateUrl: './settings.component.html',
    styleUrl: './settings.component.scss'
})
export class SettingsComponent implements OnInit {
    private readonly settingsService = inject(SettingsService);
    private readonly ttsApi = inject(TtsApiService);
    private readonly messageService = inject(MessageService);

    languages = signal<string[]>([]);
    selectedLanguage = this.settingsService.defaultLanguage;

    ngOnInit(): void {
        this.loadLanguages();
        this.loadVoices();
    }

    private loadLanguages(): void {
        this.ttsApi.getLanguages().subscribe({
            next: (res) => {
                this.languages.set(res.languages);
            },
            error: () => {
                this.messageService.add({ severity: 'error', summary: 'Fehler', detail: 'Sprachen konnten nicht geladen werden.' });
            }
        });
    }

    private loadVoices(): void {
        this.ttsApi.getVoices().subscribe({
            next: (res) => {
                this.voices.set(res.voices);
            },
            error: () => {
                this.messageService.add({ severity: 'error', summary: 'Fehler', detail: 'Stimmen konnten nicht geladen werden.' });
            }
        });
    }



    // Actually, let's use a simple property for ngModel and update signal on change.
    currentLang: string = '';

    // Model Settings
    modelOptions = [
        { label: 'Standard (0.6B)', value: '0.6b' },
        { label: 'High Quality (1.7B)', value: '1.7b' },
    ];
    currentModel: string = '1.7b';

    // Voice Settings
    voices = signal<Voice[]>([]);
    currentVoiceId: string | null = null;
    sortedVoices = computed(() => {
        const allVoices = this.voices();
        const defaultLang = this.currentLang; // Trigger on lang change if needed, but currentLang is not a signal here. 
        // Actually, let's just sort by name for now, or use the same logic as synthesis if we want.
        // For settings, maybe just alphabetical is fine.
        return [...allVoices].sort((a, b) => a.name.localeCompare(b.name));
    });

    constructor() {
        // Initialize after injection
        effect(() => {
            this.currentLang = this.settingsService.defaultLanguage();
            this.currentModel = this.settingsService.defaultModel();
            this.currentVoiceId = this.settingsService.defaultVoiceId();
        });
    }

    onLangChange(newValue: string): void {
        this.settingsService.defaultLanguage.set(newValue);
        this.messageService.add({ severity: 'success', summary: 'Gespeichert', detail: 'Spracheinstellungen wurden aktualisiert.' });
    }

    onModelChange(newValue: string): void {
        this.settingsService.defaultModel.set(newValue);
        this.messageService.add({ severity: 'success', summary: 'Gespeichert', detail: 'Modelleinstellungen wurden aktualisiert.' });
    }

    onVoiceChange(newValue: string): void {
        this.settingsService.defaultVoiceId.set(newValue);
        this.messageService.add({ severity: 'success', summary: 'Gespeichert', detail: 'Standardstimme wurde aktualisiert.' });

        // Trigger background generation if needed
        // We need to find the voice object to check if audio exists? 
        // Or just fire-and-forget call to ensure-audio (backend checks existence).
        // Since we only have ID here, let's just call it. The backend handles the "if exists" check efficiently.
        this.ttsApi.ensureVoiceAudio(newValue).subscribe({
            next: () => {
                // Success (triggered or already exists)
            },
            error: (err) => {
                console.warn('Failed to ensure voice audio:', err);
            }
        });
    }
}
