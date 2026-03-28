from services.voice_service import VoiceService

vs = VoiceService()

target = "default_035"

# Search by ID
voice_by_id = vs.get_voice(target)
print(f"By ID '{target}': {voice_by_id}")

# Search by Name
voice_by_name = vs.get_voice_by_name(target)
print(f"By Name '{target}': {voice_by_name}")

print("\n--- Listing all voices to be sure ---")
for v in vs.list_voices():
    if v["id"] == target or v["name"] == target:
        print(f"FOUND: {v}")
