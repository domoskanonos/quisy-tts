import { TestBed, fakeAsync, tick } from '@angular/core/testing';
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

    it('should immediately return voice when audio exists', (done) => {
        const v = { id: '2', name: 'v2', example_text: 'hi', instruct: 'style', language: 'german', audio_filename: 'file.wav', is_default: false, created_at: '', updated_at: '' } as Voice;
        service.ensureVoiceAudio(v).subscribe({
            next: (res) => {
                expect(res).toBe(v);
                done();
            },
            error: () => fail('should not error')
        });
    });

    it('should generate via voice-design and upload the file', (done) => {
        const v = { id: '3', name: 'v3', example_text: 'hello', instruct: 'warm voice', language: 'german', audio_filename: null, is_default: false, created_at: '', updated_at: '' } as Voice;

        service.ensureVoiceAudio(v).subscribe({
            next: (updated) => {
                expect(updated.id).toBe('3');
                expect(updated.audio_filename).toBe('voice_3.wav');
                done();
            },
            error: (err) => fail(err)
        });

        // Expect POST to generateVoiceDesign
        const genReq = httpMock.expectOne('/api/generate/voice-design/1.7b');
        expect(genReq.request.method).toBe('POST');
        // Respond with a small Blob
        const blob = new Blob(['audio'], { type: 'audio/wav' });
        genReq.flush(blob);

        // Expect upload call
        const uploadReq = httpMock.expectOne('/api/voices/3/audio');
        expect(uploadReq.request.method).toBe('POST');
        // Return updated voice
        const updatedVoice: Voice = { ...v, audio_filename: 'voice_3.wav' };
        uploadReq.flush(updatedVoice);
    });

    it('should trigger ensure by id and poll until audio available', fakeAsync(() => {
        const voiceId = '5';
        let result: Voice | null = null;

        service.ensureVoiceAudioById(voiceId, 10, 1000).subscribe({
            next: (v) => result = v,
            error: (err) => fail(err)
        });

        // Expect the ensure POST
        const ensureReq = httpMock.expectOne(`/api/voices/${voiceId}/ensure-audio`);
        expect(ensureReq.request.method).toBe('POST');
        ensureReq.flush({ status: 'ok', message: 'started' });

        // First poll: return voice without audio
        tick(10);
        const firstGet = httpMock.expectOne(`/api/voices/${voiceId}`);
        expect(firstGet.request.method).toBe('GET');
        firstGet.flush({ id: voiceId, name: 'v5', example_text: '', instruct: '', language: 'german', audio_filename: null, is_default: false, created_at: '', updated_at: '' });

        // Second poll: now with audio
        tick(10);
        const secondGet = httpMock.expectOne(`/api/voices/${voiceId}`);
        expect(secondGet.request.method).toBe('GET');
        const readyVoice: Voice = { id: voiceId, name: 'v5', example_text: '', instruct: '', language: 'german', audio_filename: 'voice_5.wav', is_default: false, created_at: '', updated_at: '' };
        secondGet.flush(readyVoice);

        // Allow observable to emit
        tick(1);
        expect(result).not.toBeNull();
        expect(result!.audio_filename).toBe('voice_5.wav');
    }));
});
