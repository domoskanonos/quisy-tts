import sys

sys.path.append("C:/_dev/repositories/quisy-tts/src")

from audio.processor import SoxAudioProcessor
from pathlib import Path


# List of files in generation order (oldest to newest)
file_list = [
    "data/audio/cache_b5b6ff15ed9639ef0e3401664e11166237d5724da75702dfe5a785e66a4bae81.wav",
    "data/audio/cache_cf740c937275b4d2e432ff757ad01d21a49c90e2e402df28131a3086c665fe12.wav",
    "data/audio/cache_3656e2a7f80335865f61111cbbd493b5e8728b2d8c9d90aaedf463c367ffecfe.wav",
    "data/audio/cache_fee823d8bd394d3f04f8cb0104eff5c36159c0f5407e7da8b6d812e12f56d11e.wav",
    "data/audio/cache_6487df20241c56eaadcf8df310e7679ab23ae7258568af5f19366c7ae1a4eac0.wav",
    "data/audio/cache_e27e377f1e8156727256cf7d2ea11945a7f0354334148eaedb8ab3f6a82ea9c3.wav",
    "data/audio/cache_b970226bef2c1131d0017994d516bc70adb0184fa3b21febf17bfe82fb0b756e.wav",
    "data/audio/cache_6af12011adbeb2289f3defde44a503889af51b0dea31c995400006d6b1f4b85f.wav",
    "data/audio/cache_c08991918706ace45e959f7912d8b6c2ecd2f2f519c3bbc9fe3a6bbaff61d86f.wav",
    "data/audio/cache_bdecc34339b49e0b5cb6d4ab1d18edaf3cafde71aa3b0c75139b8527d0fed3b8.wav",
    "data/audio/cache_a344adf20cb5ad78f8bf61bfba77d723f1f73db283fb24395a4b2dfe3b7450d1.wav",
    "data/audio/cache_d7c4362ca9f72935100a36544d32ab539e4b60bfbd19a1f1a0c88f50c810078c.wav",
    "data/audio/cache_62120b4b28999880153755d8a952fb1b101de21885492b183915e9c008b15795.wav",
]

output_path = "data/audio/concatenated_result.wav"

if SoxAudioProcessor.concatenate_audio(file_list, output_path):
    print(f"Successfully concatenated to {output_path}")
else:
    print("Concatenation failed")
