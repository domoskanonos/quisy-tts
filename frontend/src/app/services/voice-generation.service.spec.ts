import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { VoiceGenerationService } from './voice-generation.service';
import { TtsApiService } from './tts-api.service';
import { Voice } from '../models/tts.models';

describe('VoiceGenerationService', () => {
    let service: VoiceGenerationService;
    let httpMock: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            imports: [HttpClientTestingModule],
            providers: [VoiceGenerationService, TtsApiService]
        });

        service = TestBed.inject(VoiceGenerationService);
        httpMock = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should throw when voice has no instruct', (done) => {
        const v = { id: '1', name: 'x', example_text: 'hi', instruct: null, language: 'german', audio_filename: null, is_default: false, created_at: '', updated_at: '' } as Voice;
        service.ensureVoiceAudio(v).subscribe({
            next: () => fail('expected error'),
            error: () => done()
        });
    });
});
