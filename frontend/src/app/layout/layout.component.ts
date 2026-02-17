import { Component, signal } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-layout',
    standalone: true,
    imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
    templateUrl: './layout.component.html',
    styleUrl: './layout.component.scss',
})
export class LayoutComponent {
    sidebarCollapsed = signal(false);

    navItems = [
        { label: 'Speech Synthesis', icon: 'pi pi-microphone', route: '/synthesis' },
        { label: 'Voice Library', icon: 'pi pi-users', route: '/voices' },
        { label: 'API Status', icon: 'pi pi-server', route: '/status' },
    ];

    toggleSidebar(): void {
        this.sidebarCollapsed.update(v => !v);
    }
}
