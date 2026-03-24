import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { SynthesisComponent } from './synthesis.component';
import { TtsApiService } from '../../services/tts-api.service';
import { AudioPlayerService } from '../../services/audio-player.service';
import { MessageService } from 'primeng/api';
import { SettingsService } from '../../services/settings.service';
import { VoiceGenerationService } from '../../services/voice-generation.service';
import { Voice } from '../../models/tts.models';

describe('SynthesisComponent', () => {
    let component: SynthesisComponent;
    let ttsApiSpy: any;
    let audioPlayerSpy: any;
    let messageSpy: any;
    let settingsSpy: any;
    let voiceGenSpy: any;

    beforeEach(() => {
        ttsApiSpy = {
            getStatus: () => of({ message: 'ok' }),
            getVoices: () => of({ voices: [] }),
            generateBase: jasmine.createSpy('generateBase').and.returnValue(of(new Blob())),
        };

        audioPlayerSpy = { loadAudio: jasmine.createSpy('loadAudio') };
        messageSpy = { add: jasmine.createSpy('add') };
        settingsSpy = { defaultModel: () => '0.6b', defaultLanguage: () => 'german', defaultVoiceId: () => null, setDefaultVoiceId: () => {} };
        voiceGenSpy = { ensureVoiceAudio: jasmine.createSpy('ensureVoiceAudio').and.returnValue(of({ id: 'v1', audio_filename: 'file.wav' })) };

        TestBed.configureTestingModule({
            providers: [
                SynthesisComponent,
                { provide: TtsApiService, useValue: ttsApiSpy },
                { provide: AudioPlayerService, useValue: audioPlayerSpy },
                { provide: MessageService, useValue: messageSpy },
                { provide: SettingsService, useValue: settingsSpy },
                { provide: VoiceGenerationService, useValue: voiceGenSpy },
            ],
        });

        component = TestBed.inject(SynthesisComponent);
        component.text = 'Hallo Welt';
    });

    it('should generate directly when selectedVoice has audio', (done) => {
        component.selectedVoice = { id: 'a', name: 'A', example_text: 'ex', instruct: 'i', language: 'german', audio_filename: 'file.wav', is_default: false, created_at: '', updated_at: '' } as Voice;
        component.generate();
        expect(ttsApiSpy.generateBase).toHaveBeenCalled();
        setTimeout(() => {
            expect(audioPlayerSpy.loadAudio).toHaveBeenCalled();
            done();
        }, 0);
    });

    it('should generate reference audio first when missing and instruct present', (done) => {
        component.selectedVoice = { id: 'v1', name: 'V1', example_text: 'ex', instruct: 'i', language: 'german', audio_filename: null, is_default: false, created_at: '', updated_at: '' } as Voice;
        component.generate();
        expect(voiceGenSpy.ensureVoiceAudio).toHaveBeenCalledWith(component.selectedVoice);
        // After ensure, generateBase should be called
        setTimeout(() => {
            expect(ttsApiSpy.generateBase).toHaveBeenCalled();
            done();
        }, 0);
    });
});
