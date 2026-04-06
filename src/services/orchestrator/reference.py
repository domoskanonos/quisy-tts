import asyncio
from api.websocket_status_manager import status_ws_manager
from services.voice_audio_integrity import VoiceAudioIntegrityService


async def ensure_reference_audio(service, voice_id: str, force: bool = False) -> None:
    """Ensure reference audio is generated and persisted."""

    async def _generator_callback(text, lang, mode, model_size, instruct):
        return await service.generate_audio(
            text=text,
            language=lang,
            mode=mode,
            model_size=model_size,
            instruct=instruct,
            skip_integrity_check=True,
        )

    integrity_service = VoiceAudioIntegrityService(
        service.voice_service, service.audio_service, service.engine, service.cache
    )
    await integrity_service.ensure_audio(voice_id, _generator_callback, force=force)


async def run_ref_gen_task(service, voice_id: str, force: bool = False) -> None:
    """Internal coroutine to generate and persist audio."""
    service._ref_gen_status[voice_id] = {"status": "running", "message": "starting", "progress": 0}
    try:
        try:
            await status_ws_manager.broadcast_to_voice(
                voice_id,
                {"type": "ref-gen", "voice_id": voice_id, "status": "running", "progress": 0, "message": "starting"},
            )
        except Exception:
            pass
        await ensure_reference_audio(service, voice_id, force=force)
        service._ref_gen_status[voice_id] = {"status": "done", "message": "completed", "progress": 100}
        try:
            await status_ws_manager.broadcast_to_voice(
                voice_id,
                {"type": "ref-gen", "voice_id": voice_id, "status": "done", "progress": 100, "message": "completed"},
            )
        except Exception:
            pass
    except asyncio.CancelledError:
        service._ref_gen_status[voice_id] = {"status": "cancelled", "message": "cancelled"}
        raise
    except Exception as e:
        service._ref_gen_status[voice_id] = {"status": "failed", "message": str(e)}
        try:
            await status_ws_manager.broadcast_to_voice(
                voice_id, {"type": "ref-gen", "voice_id": voice_id, "status": "failed", "message": str(e)}
            )
        except Exception:
            pass
