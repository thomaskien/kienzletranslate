"""One complete checkpoint; no alternative ASR, LID or TTS model."""
import gc
import time
from .audio import decode_wav, encode_wav


class Model:
    def __init__(self, path):
        self.path = path
        self.model = None
        self.processor = None
        self.state = "unloaded"
        self.error = None

    def load(self):
        if self.model is not None:
            return
        self.state, self.error = "loading", None
        try:
            import torch
            from transformers import AutoProcessor, SeamlessM4Tv2Model
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA is unavailable")
            self.processor = AutoProcessor.from_pretrained(self.path, local_files_only=True)
            self.model = SeamlessM4Tv2Model.from_pretrained(
                self.path, local_files_only=True, use_safetensors=True,
                torch_dtype=torch.float16, low_cpu_mem_usage=True,
            ).to("cuda").eval()
            self.state = "ready"
        except Exception:
            self.unload()
            self.state, self.error = "error", "Modell konnte nicht geladen werden. Modellpfad, CUDA und freien GPU-Speicher prüfen."
            raise

    def unload(self):
        self.state = "unloading"
        self.model = None
        self.processor = None
        gc.collect()
        import torch
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        self.state, self.error = "unloaded", None

    def translate(self, data, source, target, tts):
        import torch
        self.load()
        audio, seconds = decode_wav(data)
        started = time.monotonic()
        torch.cuda.reset_peak_memory_stats()
        features = self.processor(audios=audio, sampling_rate=16000, return_tensors="pt")
        inputs = {k: v.to(device="cuda", dtype=torch.float16 if v.is_floating_point() else v.dtype)
                  for k, v in features.items()}
        with torch.inference_mode():
            original = self.model.generate(**inputs, tgt_lang=source, generate_speech=False,
                                           max_new_tokens=256, num_beams=1)
            original_ids = original.sequences if hasattr(original, "sequences") else original
            original_text = self.processor.batch_decode(original_ids, skip_special_tokens=True)[0]
            asr_done = time.monotonic()
            speech_codes = set(self.model.generation_config.t2u_lang_code_to_id) & set(self.model.generation_config.vocoder_lang_code_to_id)
            make_speech = bool(tts and target in speech_codes)
            translated = self.model.generate(
                **inputs, tgt_lang=target, generate_speech=make_speech,
                return_intermediate_token_ids=make_speech, max_new_tokens=256, num_beams=1,
            )
            ids = translated.sequences if hasattr(translated, "sequences") else translated
            translated_text = self.processor.batch_decode(ids, skip_special_tokens=True)[0]
            output_audio = None
            if make_speech:
                length = int(translated.waveform_lengths.reshape(-1)[0].item())
                waveform = translated.waveform.reshape(-1)[:length].float().cpu().numpy()
                output_audio = encode_wav(waveform, self.model.config.sampling_rate)
            finished = time.monotonic()
            result = {
                "original_text": original_text, "translated_text": translated_text,
                "source_lang": source, "target_lang": target,
                "audio_available": output_audio is not None,
                "text_only_reason": "Für diese Zielsprache ist nur Textausgabe verfügbar." if tts and not make_speech else None,
                "metrics": {"audio_seconds": round(seconds, 3), "asr_seconds": round(asr_done-started, 3),
                            "translation_seconds": round(finished-asr_done, 3),
                            "peak_vram_mib": round(torch.cuda.max_memory_allocated()/1024**2)},
            }
        return result, output_audio
