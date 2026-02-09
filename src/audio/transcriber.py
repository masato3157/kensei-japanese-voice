# -*- coding: utf-8 -*-
"""
トランスクライバー - 音声認識エンジン (Kotoba-Whisper / Faster Whisper)

このモジュールは、以下の音声認識エンジンを提供します。

1. Kotoba-Whisper (Main): Transformersベース。高精度な日本語認識、文体維持。
2. Faster Whisper (Fallback): CTranslate2ベース。軽量・高速、低スペック環境用。

環境設定または自動判定により、最適なエンジンを選択して初期化します。
"""

import numpy as np
import threading
from typing import Optional, Literal
from src.utils.config_manager import ConfigManager

# エンジンの種類
ENGINE_KOTOBA = "kotoba"
ENGINE_FASTER = "faster_whisper"


class AudioTranscriber:
    """
    音声認識クラス（マルチエンジン対応）
    
    設定に基づいて Kotoba-Whisper または Faster Whisper を初期化し、
    音声データをテキストに変換します。
    """
    
    def __init__(
        self,
        model_size: str = "medium",
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        engine: Optional[str] = None
    ):
        """
        トランスクライバーを初期化する
        
        Args:
            model_size: モデルサイズ (Faster Whisper用。Kotobaは固定)
            device:実行デバイス ("cuda" or "cpu"。省略時は自動検出)
            compute_type: 計算精度 (Faster Whisper用。省略時は自動選択)
            engine: エンジン指定 ("kotoba", "faster_whisper", "auto"。省略時はConfigManagerから取得)
        """
        self._config = ConfigManager.get_instance()
        
        # エンジンの決定
        self._target_engine = engine or self._config.settings.asr_engine
        if self._target_engine == "auto":
            import torch
            has_gpu = torch.cuda.is_available()
            # GPUがあるなら Kotoba (Main), なければ Faster (Fallback)
            self._target_engine = ENGINE_KOTOBA if has_gpu else ENGINE_FASTER
            
        print(f"[Transcriber] 選択されたエンジン: {self._target_engine}")

        # デバイスの決定
        if device is None:
            import torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self._device = device

        self._model_size = model_size
        self._compute_type = compute_type
        
        # モデルインスタンス
        self._pipe = None  # Kotoba-Whisper用 (pipeline)
        self._model = None # Faster Whisper用 (WhisperModel)
        self._lock = threading.Lock() # スレッドセーフ用
        
        # モデル読み込み
        self._load_model()
        
    def _load_model(self) -> None:
        """選択されたエンジンに基づいてモデルを読み込む"""
        try:
            if self._target_engine == ENGINE_KOTOBA:
                self._load_kotoba_whisper()
            else:
                self._load_faster_whisper()
        except Exception as e:
            print(f"[Transcriber] モデル読み込みエラー: {e}")
            # エラー時はFallbackとしてFaster Whisperを試みる（Kotoba失敗時など）
            if self._target_engine == ENGINE_KOTOBA:
                print("[Transcriber] Kotoba-Whisperの読み込みに失敗しました。Faster Whisperへの切り替えを試みます。")
                self._target_engine = ENGINE_FASTER
                self._load_faster_whisper()
            else:
                raise e

    def _load_kotoba_whisper(self) -> None:
        """Kotoba-Whisper v1.0 をロードする (Transformers)"""
        print("[Transcriber] Kotoba-Whisper v1.0 (Transformers) を読み込み中...")
        from transformers import pipeline
        import torch

        # モデルID (v1.0を使用)
        model_id = "kotoba-tech/kotoba-whisper-v1.0"
        
        torch_dtype = torch.float16 if self._device == "cuda" else torch.float32
        
        self._pipe = pipeline(
            "automatic-speech-recognition",
            model=model_id,
            torch_dtype=torch_dtype,
            device=self._device,
            chunk_length_s=30,
            batch_size=1, # リアルタイム用途なのでバッチサイズ1
            trust_remote_code=True
        )
        print(f"[Transcriber] Kotoba-Whisper 読み込み完了 (Device: {self._device})")

    def _load_faster_whisper(self) -> None:
        """Faster Whisper をロードする"""
        print(f"[Transcriber] Faster Whisper ({self._model_size}) を読み込み中...")
        from faster_whisper import WhisperModel
        
        # compute_typeの自動決定
        if self._compute_type is None:
            self._compute_type = "float16" if self._device == "cuda" else "int8"
            
        self._model = WhisperModel(
            self._model_size,
            device=self._device,
            compute_type=self._compute_type
        )
        print(f"[Transcriber] Faster Whisper 読み込み完了 (Device: {self._device}, Type: {self._compute_type})")

    def transcribe(self, audio_data: np.ndarray, language: str = "ja") -> str:
        """
        音声データをテキストに変換する
        
        Args:
            audio_data: 音声データ（float32 numpy配列、16kHz、-1.0〜1.0）
            language: 認識言語（デフォルト: 日本語）
            
        Returns:
            認識されたテキスト（生テキスト）
        """
        if audio_data is None or len(audio_data) == 0:
            return ""
            
        # 短すぎる音声はスキップ
        if len(audio_data) < 8000: # 0.5秒
            return ""

        with self._lock:
            if self._target_engine == ENGINE_KOTOBA:
                return self._transcribe_kotoba(audio_data, language)
            else:
                return self._transcribe_faster(audio_data, language)

    def _transcribe_kotoba(self, audio_data: np.ndarray, language: str) -> str:
        """Kotoba-Whisperによる推論"""
        if self._pipe is None:
            return ""
            
        try:
            # パイプラインは通常ファイルパスやbytesを期待するが、samping_rate指定でnumpy arrayも通せる場合が多い。
            # ただしtransformersのバージョンによる。安全のため辞書形式で渡す。
            # (raw audio, sampling_rate)
            
            # audio_data は float32, 16kHz であることが前提
            prediction = self._pipe(
                {"raw": audio_data, "sampling_rate": 16000},
                generate_kwargs={
                    "language": "japanese", # Kotobaは日本語特化だが念のため指定
                    "task": "transcribe",
                    "num_beams": 1, # 高速化と余計な探索抑制
                    "do_sample": False # 決定論的に
                },
                return_timestamps=False
            )
            
            text = prediction["text"].strip()
            return text
            
        except Exception as e:
            print(f"[Transcriber] Kotoba推論エラー: {e}")
            return ""

    def _transcribe_faster(self, audio_data: np.ndarray, language: str) -> str:
        """Faster Whisperによる推論"""
        if self._model is None:
            return ""
            
        try:
            segments, _ = self._model.transcribe(
                audio_data,
                language=language,
                beam_size=1,
                vad_filter=True, # Faster-WhisperのVADは優秀なので使う
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            text_parts = [segment.text.strip() for segment in segments]
            return " ".join(text_parts)
            
        except Exception as e:
            print(f"[Transcriber] Faster推論エラー: {e}")
            return ""

    def get_model_info(self) -> dict:
        """現在のモデル情報を返す"""
        return {
            "engine": self._target_engine,
            "device": self._device,
            "loaded": (self._pipe is not None) or (self._model is not None)
        }
    
    def dispose(self) -> None:
        """リソースを解放する"""
        with self._lock:
            self._pipe = None
            self._model = None
            import gc
            gc.collect()


# テスト用
if __name__ == "__main__":
    import time
    
    print("=== Transcriber Dual Engine Test ===")
    
    # テスト1: Faster Whisper (強制)
    print("\n--- Testing Faster Whisper ---")
    try:
        t_faster = AudioTranscriber(engine=ENGINE_FASTER)
        dummy_audio = np.zeros(16000 * 2, dtype=np.float32)
        start = time.time()
        res = t_faster.transcribe(dummy_audio)
        print(f"Result: '{res}' ({time.time() - start:.2f}s)")
        t_faster.dispose()
    except Exception as e:
        print(f"Faster Whisper Test Failed: {e}")

    # テスト2: Kotoba-Whisper (強制 - GPU推奨だがCPUでも動くか確認)
    print("\n--- Testing Kotoba-Whisper ---")
    try:
        # CPU環境で重すぎる場合は中断される可能性があることに注意
        t_kotoba = AudioTranscriber(engine=ENGINE_KOTOBA)
        start = time.time()
        res = t_kotoba.transcribe(dummy_audio)
        print(f"Result: '{res}' ({time.time() - start:.2f}s)")
        t_kotoba.dispose()
    except Exception as e:
        print(f"Kotoba-Whisper Test Failed: {e}")
        
    print("\nTest Finished")
