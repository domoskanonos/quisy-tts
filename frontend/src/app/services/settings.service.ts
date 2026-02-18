import { Injectable, signal, effect, PLATFORM_ID, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Injectable({
    providedIn: 'root'
})
export class SettingsService {
    private readonly platformId = inject(PLATFORM_ID);

    // Signals
    readonly defaultLanguage = signal<string>('German'); // Default to German

    constructor() {
        this.loadSettings();

        // Auto-save effect
        effect(() => {
            const lang = this.defaultLanguage();
            const model = this.defaultModel();
            const voiceId = this.defaultVoiceId();
            if (isPlatformBrowser(this.platformId)) {
                localStorage.setItem('settings_default_language', lang);
                localStorage.setItem('settings_default_model', model);
                if (voiceId) localStorage.setItem('settings_default_voice_id', voiceId);
            }
        });
    }

    private loadSettings(): void {
        if (isPlatformBrowser(this.platformId)) {
            const savedLang = localStorage.getItem('settings_default_language');
            if (savedLang) {
                this.defaultLanguage.set(savedLang);
            } else {
                // Auto-detect browser language
                const browserLang = navigator.language.toLowerCase();
                if (browserLang.startsWith('de')) {
                    this.defaultLanguage.set('German');
                } else {
                    this.defaultLanguage.set('English');
                }
            }

            const savedModel = localStorage.getItem('settings_default_model');
            if (savedModel) {
                this.defaultModel.set(savedModel);
            }

            const savedVoiceId = localStorage.getItem('settings_default_voice_id');
            if (savedVoiceId) {
                this.defaultVoiceId.set(savedVoiceId);
            }
        }
    }

    setDefaultLanguage(lang: string): void {
        this.defaultLanguage.set(lang);
    }

    // New: Model Settings
    readonly defaultModel = signal<string>('1.7b'); // Default to 1.7b

    setDefaultModel(model: string): void {
        this.defaultModel.set(model);
    }

    // New: Voice Settings
    readonly defaultVoiceId = signal<string | null>(null);

    setDefaultVoiceId(id: string): void {
        this.defaultVoiceId.set(id);
    }
}
