# -*- coding: utf-8 -*-
"""
トランスクライバー - faster-whisperによる音声認識

このモジュールは、faster-whisperを使用した高速な音声認識機能を提供します。
CPU上でint8量子化を使用し、高速かつ低メモリで動作します。
"""

import numpy as np
from typing import Optional
from faster_whisper import WhisperModel


class AudioTranscriber:
    """
    音声認識クラス
    
    faster-whisperを使用して音声データをテキストに変換します。
    CPU最適化（int8量子化）により、高速に動作します。
    
    使用例:
        transcriber = AudioTranscriber()
        text = transcriber.transcribe(audio_data)
        print(text)
    """
    
    # デフォルト設定
    DEFAULT_MODEL = "base"       # 軽量モデル（約140MB）
    DEFAULT_DEVICE = "cpu"       # CPUで実行
    DEFAULT_COMPUTE_TYPE = "int8"  # int8量子化で高速化
    
    def __init__(
        self,
        model_size: str = DEFAULT_MODEL,
        device: str = DEFAULT_DEVICE,
        compute_type: str = DEFAULT_COMPUTE_TYPE
    ):
        """
        トランスクライバーを初期化する
        
        Args:
            model_size: モデルサイズ ("tiny", "base", "small", "medium", "large-v3")
            device: 実行デバイス ("cpu" または "cuda")
            compute_type: 計算精度 ("int8", "float16", "float32")
        """
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model: Optional[WhisperModel] = None
        
        # モデルを読み込む
        self._load_model()
        
    def _load_model(self) -> None:
        """Whisperモデルを読み込む"""
        print(f"[Transcriber] モデル読み込み中: {self._model_size} ({self._compute_type})...")
        
        self._model = WhisperModel(
            self._model_size,
            device=self._device,
            compute_type=self._compute_type
        )
        
        print(f"[Transcriber] モデル読み込み完了")
        
    def transcribe(
        self,
        audio_data: np.ndarray,
        language: str = "ja"
    ) -> str:
        """
        音声データをテキストに変換する
        
        Args:
            audio_data: 音声データ（float32 numpy配列、16kHz、-1.0〜1.0）
            language: 認識言語（デフォルト: 日本語）
            
        Returns:
            認識されたテキスト
        """
        if self._model is None:
            raise RuntimeError("モデルが読み込まれていません")
            
        if audio_data is None or len(audio_data) == 0:
            return ""
            
        # 音声が短すぎる場合（0.5秒未満）はスキップ
        if len(audio_data) < 8000:  # 16kHz * 0.5秒
            return ""
        
        # faster-whisperで文字起こし
        # beam_size=1 で高速化、vad_filter=True でノイズ除去
        segments, info = self._model.transcribe(
            audio_data,
            language=language,
            beam_size=1,           # 高速化のため1に設定
            vad_filter=True,       # Voice Activity Detectionでノイズ除去
            vad_parameters={
                "min_silence_duration_ms": 500,  # 500ms以上の無音で区切る
            }
        )
        
        # セグメントを結合してテキストを生成
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())
            
        result = " ".join(text_parts)
        
        return result
    
    def get_model_info(self) -> dict:
        """
        現在のモデル情報を返す
        
        Returns:
            モデル情報の辞書
        """
        return {
            "model_size": self._model_size,
            "device": self._device,
            "compute_type": self._compute_type,
            "loaded": self._model is not None
        }
    
    def dispose(self) -> None:
        """リソースを解放する"""
        self._model = None


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    import time
    
    print("=== Transcriber テスト ===")
    
    # モデル読み込み
    start_time = time.time()
    transcriber = AudioTranscriber()
    load_time = time.time() - start_time
    print(f"モデル読み込み時間: {load_time:.2f} 秒")
    
    # テスト用のダミー音声（無音）を生成
    dummy_audio = np.zeros(16000 * 2, dtype=np.float32)  # 2秒の無音
    
    print("\nダミー音声で認識テスト...")
    start_time = time.time()
    result = transcriber.transcribe(dummy_audio)
    transcribe_time = time.time() - start_time
    
    print(f"認識結果: '{result}'")
    print(f"認識時間: {transcribe_time:.2f} 秒")
    
    print("\nモデル情報:")
    print(transcriber.get_model_info())
    
    transcriber.dispose()
    print("\nテスト終了")
