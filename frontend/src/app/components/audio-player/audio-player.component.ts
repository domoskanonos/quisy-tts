import { Component, inject, computed, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AudioPlayerService } from '../../services/audio-player.service';

@Component({
    selector: 'app-audio-player',
    standalone: true,
    changeDetection: ChangeDetectionStrategy.OnPush,
    imports: [CommonModule],
    templateUrl: './audio-player.component.html',
    styleUrls: ['./audio-player.component.scss']
})
export class AudioPlayerComponent {
    audioPlayer = inject(AudioPlayerService);

    // Expose signals for template
    isPlaying = this.audioPlayer.isPlaying;
    currentTime = this.audioPlayer.currentTime;
    duration = this.audioPlayer.duration;
    audioUrl = this.audioPlayer.audioUrl;
    waveformData = this.audioPlayer.waveformData;

    formatTime(seconds: number): string {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    togglePlay(): void {
        this.audioPlayer.togglePlay();
    }

    stop(): void {
        this.audioPlayer.stop();
    }

    download(): void {
        this.audioPlayer.download();
    }
}
