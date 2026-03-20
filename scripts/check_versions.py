import subprocess

result = subprocess.run(
    ["grep", "-rl", "qwen3_tts", "/mnt/c/_dev/repositories/quisy-tts/.venv/lib/"], capture_output=True, text=True
)
print("Files matching 'qwen3_tts':")
print(result.stdout if result.stdout else "NONE FOUND")
print(result.stderr[:200] if result.stderr else "")
