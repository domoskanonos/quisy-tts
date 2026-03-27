"""Unit tests for VoiceService.set_audio behavior (generated vs user uploads).

These tests verify that auto-generated files matching the pattern
`voice_{id}_*.wav` are removed when `set_audio` persists a new audio file,
and that user-uploaded files named `voice_{id}.wav` are preserved.
"""

import os
import sys
from pathlib import Path


def _prepare_env(tmp_path: Path) -> None:
    # Set minimal env vars BEFORE importing project code so ProjectConfig picks them up
    os.environ.setdefault("MODELS_DIR", str(tmp_path / "models"))
    os.environ.setdefault("VOICES_DIR", str(tmp_path / "voices"))
    os.environ.setdefault("OUTPUT_DIR", str(tmp_path / "output"))
    os.environ.setdefault("APP_DIR", str(tmp_path / "app"))
    os.environ.setdefault("RESOURCES_DIR", str(tmp_path / "resources"))
    os.environ.setdefault(
        "DOWNLOAD_MODELS",
        "Qwen/Qwen3-TTS-12Hz-1.7B-Base,Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign,Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    )


def test_set_audio_removes_old_generated_files_but_preserves_user_upload(tmp_path: Path) -> None:
    _prepare_env(tmp_path)

    # Load voice_service module by file path to avoid importing the `services`
    # package which can trigger circular imports during test initialization.
    src_root = Path(__file__).resolve().parent.parent / "src"
    voice_service_path = src_root / "services" / "voice_service.py"
    default_voices_path = src_root / "services" / "default_voices.py"
    import importlib.util
    import types

    # Provide a lightweight 'services' package in sys.modules so that
    # `from services.default_voices import DEFAULT_VOICES` inside
    # voice_service.py does not import the real services package and trigger
    # circular imports. Load default_voices as services.default_voices.
    services_pkg = types.ModuleType("services")
    sys.modules["services"] = services_pkg

    spec_def = importlib.util.spec_from_file_location("services.default_voices", str(default_voices_path))
    assert spec_def is not None
    def_mod = importlib.util.module_from_spec(spec_def)
    assert spec_def.loader is not None
    spec_def.loader.exec_module(def_mod)
    sys.modules["services.default_voices"] = def_mod

    spec = importlib.util.spec_from_file_location("voice_service_mod", str(voice_service_path))
    assert spec is not None
    vs_mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(vs_mod)
    VoiceService = vs_mod.VoiceService

    vs = VoiceService(voices_dir=Path(os.environ["VOICES_DIR"]))

    # Create a voice
    v = vs.create_voice(name="tts-test-1", example_text="Hallo", instruct="A test")
    vid = v["id"]

    voices_dir = Path(os.environ["VOICES_DIR"])
    voices_dir.mkdir(parents=True, exist_ok=True)

    # Create some existing generated files and one user-uploaded file
    gen1 = voices_dir / f"voice_{vid}_aaa111bbb222.wav"
    gen2 = voices_dir / f"voice_{vid}_ccc333ddd444.wav"
    user = voices_dir / f"voice_{vid}.wav"

    gen1.write_bytes(b"gen1")
    gen2.write_bytes(b"gen2")
    user.write_bytes(b"user_upload")

    # Now call set_audio with an explicit generated filename (simulate auto-gen)
    final_name = f"voice_{vid}_fff999ggg000.wav"
    updated = vs.set_audio(vid, b"newgen", original_filename="gen.wav", audio_filename=final_name)

    # DB should point to the new generated filename
    assert updated["audio_filename"] == final_name

    # New file exists
    assert (voices_dir / final_name).exists()

    # Old generated files should be removed
    assert not gen1.exists()
    assert not gen2.exists()

    # User-uploaded file should remain untouched
    assert user.exists()


def test_upload_replaces_generated_files_and_writes_user_filename(tmp_path: Path) -> None:
    _prepare_env(tmp_path)
    src_root = Path(__file__).resolve().parent.parent / "src"
    voice_service_path = src_root / "services" / "voice_service.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("voice_service_mod", str(voice_service_path))
    assert spec is not None
    vs_mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(vs_mod)
    VoiceService = vs_mod.VoiceService

    vs = VoiceService(voices_dir=Path(os.environ["VOICES_DIR"]))

    v = vs.create_voice(name="tts-test-2", example_text="Hallo2", instruct="A test")
    vid = v["id"]

    voices_dir = Path(os.environ["VOICES_DIR"])
    voices_dir.mkdir(parents=True, exist_ok=True)

    # Create a generated file
    gen = voices_dir / f"voice_{vid}_oldkey.wav"
    gen.write_bytes(b"old")

    # Simulate user uploading a file (no audio_filename override)
    updated = vs.set_audio(vid, b"uploaded", original_filename="upload.wav")

    # Should save as voice_{id}.wav
    expected = f"voice_{vid}.wav"
    assert updated["audio_filename"] == expected
    assert (voices_dir / expected).exists()

    # Generated file should be removed
    assert not gen.exists()
