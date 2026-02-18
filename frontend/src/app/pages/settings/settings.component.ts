import { Component, inject, OnInit, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SelectModule } from 'primeng/select';
import { CardModule } from 'primeng/card';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { SettingsService } from '../../services/settings.service';
import { TtsApiService } from '../../services/tts-api.service';

@Component({
    selector: 'app-settings',
    standalone: true,
    imports: [CommonModule, FormsModule, SelectModule, CardModule, ToastModule],
    providers: [MessageService],
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

    saveSettings(): void {
        // The signal is linked in the service, but since we use `selectedLanguage = this.settingsService.defaultLanguage`, it's a readonly signal reference or computed? 
        // Actually `selectedLanguage` should be a WritableSignal if valid, OR we just bind to a local signal and update service on change.

        // Let's make `selectedLanguage` a writeable signal initialized with service value, 
        // or just bind directly if `settingsService.defaultLanguage` is writable.
        // `settingsService.defaultLanguage` is a WritableSignal.

        // However, `selectedLanguage = this.settingsService.defaultLanguage` assigns the REFERENCE. 
        // `[(ngModel)]="selectedLanguage"` won't work directly on a signal in Angular < 17.2 without `model()` input or explicit handling.
        // But PrimeNG `p-select` expects a value. 

        // Better approach:
        // local `lang` signal or property.
    }

    // Actually, let's use a simple property for ngModel and update signal on change.
    currentLang: string = '';

    constructor() {
        // Initialize after injection
        effect(() => {
            this.currentLang = this.settingsService.defaultLanguage();
        });
    }

    onLangChange(newValue: string): void {
        this.settingsService.defaultLanguage.set(newValue);
        this.messageService.add({ severity: 'success', summary: 'Gespeichert', detail: 'Einstellungen wurden aktualisiert.' });
    }
}
