import { Component, signal, Inject, PLATFORM_ID, OnInit, effect, ChangeDetectionStrategy } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule, DOCUMENT, isPlatformBrowser } from '@angular/common';

@Component({
    selector: 'app-layout',
    standalone: true,
    changeDetection: ChangeDetectionStrategy.OnPush,
    imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
    templateUrl: './layout.component.html',
    styleUrl: './layout.component.scss',
})
export class LayoutComponent implements OnInit {
    sidebarCollapsed = signal(false);
    isDarkMode = signal(false);

    navItems = [
        { label: 'Speech Synthesis', icon: 'pi pi-microphone', route: '/synthesis' },
        { label: 'Voice Library', icon: 'pi pi-users', route: '/voices' },
        { label: 'Status', icon: 'pi pi-server', route: '/status' },
        { label: 'Einstellungen', icon: 'pi pi-cog', route: '/settings' },
    ];

    constructor(
        @Inject(DOCUMENT) private document: Document,
        @Inject(PLATFORM_ID) private platformId: Object
    ) {
        // Effect to apply theme class
        effect(() => {
            if (this.isDarkMode()) {
                this.document.documentElement.classList.add('dark-mode');
            } else {
                this.document.documentElement.classList.remove('dark-mode');
            }
        });
    }

    ngOnInit(): void {
        if (isPlatformBrowser(this.platformId)) {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {
                this.isDarkMode.set(savedTheme === 'dark');
            } else {
                // Default to dark if no preference (or check system preference)
                this.isDarkMode.set(true);
            }
        } else {
            this.isDarkMode.set(true);
        }
    }

    toggleSidebar(): void {
        this.sidebarCollapsed.update(v => !v);
    }

    toggleTheme(): void {
        this.isDarkMode.update(v => !v);
        if (isPlatformBrowser(this.platformId)) {
            localStorage.setItem('theme', this.isDarkMode() ? 'dark' : 'light');
        }
    }
}
