# -*- coding: utf-8 -*-
"""
トランスクライバー - faster-whisperによる音声認識

このモジュールは、faster-whisperを使用した高速な音声認識機能を提供します。
GPU（CUDA）が利用可能な場合はfloat16で高速処理、
CPUのみの場合はint8量子化で実用的な速度を確保します。

環境自動判定機能により、ユーザーが設定を変更することなく
ハードウェア性能を最大限に活用します。
"""

import numpy as np
from typing import Optional
from faster_whisper import WhisperModel


def detect_optimal_settings() -> tuple[str, str]:
    """
    利用可能なハードウェアを検出し、最適な設定を返す
    
    Returns:
        (device, compute_type) のタプル
        - GPU搭載機: ("cuda", "float16")
        - CPU専用機: ("cpu", "int8")
    """
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"[Transcriber] GPU検出: {gpu_name}")
            return ("cuda", "float16")
    except ImportError:
        pass
    
    print("[Transcriber] GPUが利用できません。CPUモードで動作します。")
    return ("cpu", "int8")


class AudioTranscriber:
    """
    音声認識クラス（環境自動適応型）
    
    faster-whisperを使用して音声データをテキストに変換します。
    起動時にGPU/CPUを自動判定し、最適な設定を選択します。
    
    - GPU搭載機: CUDA + float16 でリアルタイム認識
    - CPU専用機: int8量子化で実用的な速度を確保
    
    使用例:
        transcriber = AudioTranscriber()  # 自動設定
        text = transcriber.transcribe(audio_data)
        print(text)
    """
    
    # デフォルト設定
    DEFAULT_MODEL = "medium"  # バランスの良いmediumモデル
    
    def __init__(
        self,
        model_size: str = DEFAULT_MODEL,
        device: Optional[str] = None,
        compute_type: Optional[str] = None
    ):
        """
        トランスクライバーを初期化する
        
        Args:
            model_size: モデルサイズ (デフォルト: "medium")
            device: 実行デバイス (省略時は自動検出)
            compute_type: 計算精度 (省略時は自動選択)
        """
        self._model_size = model_size
        
        # デバイスと計算精度を自動検出（明示的に指定されていない場合）
        if device is None or compute_type is None:
            auto_device, auto_compute = detect_optimal_settings()
            self._device = device or auto_device
            self._compute_type = compute_type or auto_compute
        else:
            self._device = device
            self._compute_type = compute_type
            
        self._model: Optional[WhisperModel] = None
        
        # モデルを読み込む
        self._load_model()
        
    def _load_model(self) -> None:
        """Whisperモデルを読み込む"""
        print(f"[Transcriber] モデル読み込み中: {self._model_size}")
        print(f"[Transcriber] デバイス: {self._device.upper()}, 精度: {self._compute_type}")
        
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
