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
            if (isPlatformBrowser(this.platformId)) {
                localStorage.setItem('settings_default_language', lang);
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
        }
    }

    setDefaultLanguage(lang: string): void {
        this.defaultLanguage.set(lang);
    }
}
