import { TestBed } from '@angular/core/testing';
import { VoicesComponent } from './voices.component';
import { TtsApiService } from '../../services/tts-api.service';
import { MessageService, ConfirmationService } from 'primeng/api';
import { VoiceGenerationService } from '../../services/voice-generation.service';
import { of } from 'rxjs';

describe('VoicesComponent', () => {
    let comp: VoicesComponent;
    let ttsApiSpy: any;
    let messageSpy: any;
    let voiceGenSpy: any;

    beforeEach(() => {
        ttsApiSpy = { getVoices: () => of({ voices: [] }) };
        messageSpy = { add: jasmine.createSpy('add') };
        voiceGenSpy = { ensureVoiceAudio: jasmine.createSpy('ensureVoiceAudio').and.returnValue(of({ id: '1', audio_filename: 'a.wav' })) };

        TestBed.configureTestingModule({
            providers: [
                VoicesComponent,
                { provide: TtsApiService, useValue: ttsApiSpy },
                { provide: MessageService, useValue: messageSpy },
                { provide: ConfirmationService, useValue: {} },
                { provide: VoiceGenerationService, useValue: voiceGenSpy }
            ]
        });

        comp = TestBed.inject(VoicesComponent);
    });

    it('should call ensureVoiceAudio when generating audio', () => {
        const v: any = { id: '1', name: 't', example_text: '', instruct: 'x', language: 'german', audio_filename: null };
        comp.generateAndPlay(v);
        expect(voiceGenSpy.ensureVoiceAudio).toHaveBeenCalledWith(v);
    });
});
