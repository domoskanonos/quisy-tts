import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TtsApiService } from '../../services/tts-api.service';
import { ApiStatus } from '../../models/tts.models';

@Component({
    selector: 'app-status',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './status.component.html',
    styleUrl: './status.component.scss',
})
export class StatusComponent implements OnInit {
    private readonly ttsApi = inject(TtsApiService);

    status = signal<ApiStatus | null>(null);
    error = signal<string | null>(null);
    isLoading = signal(true);

    ngOnInit(): void {
        this.loadStatus();
    }

    loadStatus(): void {
        this.isLoading.set(true);
        this.error.set(null);

        this.ttsApi.getStatus().subscribe({
            next: data => {
                this.status.set(data);
                this.isLoading.set(false);
            },
            error: () => {
                this.error.set('Backend nicht erreichbar. Stelle sicher, dass der Server läuft.');
                this.isLoading.set(false);
            },
        });
    }
}
