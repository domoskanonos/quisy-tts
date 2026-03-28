from services.voice_service import VoiceService

vs = VoiceService()
voices = vs.list_voices()
print("Available voices in database:")
for v in voices:
    print(f"Name: {v['name']}, ID: {v['id']}")
