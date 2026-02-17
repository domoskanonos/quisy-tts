import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class AudioPlayerService {
    private audioElement: HTMLAudioElement | null = null;
    private audioContext: AudioContext | null = null;
    private analyser: AnalyserNode | null = null;
    private sourceNode: MediaElementAudioSourceNode | null = null;

    readonly isPlaying = signal(false);
    readonly currentTime = signal(0);
    readonly duration = signal(0);
    readonly audioUrl = signal<string | null>(null);
    readonly waveformData = signal<number[]>([]);

    loadAudio(blob: Blob): void {
        this.stop();

        const url = URL.createObjectURL(blob);
        this.audioUrl.set(url);

        this.audioElement = new Audio(url);
        this.audioElement.addEventListener('loadedmetadata', () => {
            this.duration.set(this.audioElement!.duration);
        });
        this.audioElement.addEventListener('timeupdate', () => {
            this.currentTime.set(this.audioElement!.currentTime);
        });
        this.audioElement.addEventListener('ended', () => {
            this.isPlaying.set(false);
        });

        // Set up Web Audio API for waveform
        this.setupAnalyser();

        // Extract waveform data from blob
        this.extractWaveform(blob);
    }

    private setupAnalyser(): void {
        if (!this.audioElement) return;

        this.audioContext = new AudioContext();
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;

        this.sourceNode = this.audioContext.createMediaElementSource(this.audioElement);
        this.sourceNode.connect(this.analyser);
        this.analyser.connect(this.audioContext.destination);
    }

    private async extractWaveform(blob: Blob): Promise<void> {
        try {
            const ctx = new AudioContext();
            const arrayBuffer = await blob.arrayBuffer();
            const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
            const channelData = audioBuffer.getChannelData(0);

            // Downsample to ~100 bars
            const bars = 100;
            const blockSize = Math.floor(channelData.length / bars);
            const waveform: number[] = [];

            for (let i = 0; i < bars; i++) {
                let sum = 0;
                for (let j = 0; j < blockSize; j++) {
                    sum += Math.abs(channelData[i * blockSize + j]);
                }
                waveform.push(sum / blockSize);
            }

            // Normalize
            const max = Math.max(...waveform);
            this.waveformData.set(waveform.map(v => v / (max || 1)));
            await ctx.close();
        } catch {
            this.waveformData.set([]);
        }
    }

    play(): void {
        if (this.audioElement) {
            this.audioContext?.resume();
            this.audioElement.play();
            this.isPlaying.set(true);
        }
    }

    pause(): void {
        if (this.audioElement) {
            this.audioElement.pause();
            this.isPlaying.set(false);
        }
    }

    stop(): void {
        if (this.audioElement) {
            this.audioElement.pause();
            this.audioElement.currentTime = 0;
            this.isPlaying.set(false);
        }
        if (this.audioUrl()) {
            URL.revokeObjectURL(this.audioUrl()!);
            this.audioUrl.set(null);
        }
        this.waveformData.set([]);
        this.currentTime.set(0);
        this.duration.set(0);
    }

    seek(time: number): void {
        if (this.audioElement) {
            this.audioElement.currentTime = time;
        }
    }

    seekPercent(percent: number): void {
        if (this.audioElement && this.duration()) {
            this.audioElement.currentTime = (percent / 100) * this.duration();
        }
    }

    download(filename = 'quisy-tts-output.wav'): void {
        const url = this.audioUrl();
        if (!url) return;

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
    }

    formatTime(seconds: number): string {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}
