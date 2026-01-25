import inspect

from qwen_tts import Qwen3TTSModel


print("Inspecting Qwen3TTSModel...")
methods = inspect.getmembers(Qwen3TTSModel, predicate=inspect.isfunction)
for name, _ in methods:
    print(f"- {name}")
