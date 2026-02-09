# -*- coding: utf-8 -*-
"""
レコーダー - PyAudioによるマイク入力の制御

このモジュールは、マイクからの音声録音機能を提供します。
プッシュ・トゥ・トーク方式（キーを押している間だけ録音）に対応しています。
"""

import numpy as np
import pyaudio
import threading
from typing import Optional, List


class AudioRecorder:
    """
    音声録音クラス
    
    PyAudioを使用してマイクから音声を録音します。
    16kHz, モノラル, 16bitで録音し、numpy配列として返します。
    
    使用例:
        recorder = AudioRecorder()
        recorder.start()
        # ... 録音中 ...
        audio_data = recorder.stop()
    """
    
    # 録音パラメータ（Whisperに最適化）
    SAMPLE_RATE = 16000      # 16kHz (Whisperの推奨サンプルレート)
    CHANNELS = 1             # モノラル
    CHUNK_SIZE = 1024        # バッファサイズ
    FORMAT = pyaudio.paInt16 # 16bit整数
    
    def __init__(self):
        """レコーダーを初期化する"""
        self._audio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._frames: List[bytes] = []
        self._is_recording = False
        self._lock = threading.Lock()
        
    def _init_audio(self) -> None:
        """PyAudioインスタンスを初期化する"""
        if self._audio is None:
            self._audio = pyaudio.PyAudio()
            
    def get_default_input_device_name(self) -> str:
        """
        デフォルト入力デバイス（マイク）の名前を取得する
        
        Returns:
            デバイス名（取得失敗時は「不明」）
        """
        try:
            self._init_audio()
            default_index = self._audio.get_default_input_device_info()
            return default_index.get("name", "不明")
        except Exception as e:
            return f"取得失敗: {e}"
            
    def _cleanup_audio(self) -> None:
        """PyAudioリソースを解放する"""
        if self._audio is not None:
            self._audio.terminate()
            self._audio = None
            
    def start(self) -> None:
        """
        録音を開始する
        
        既に録音中の場合は何もしない。
        """
        with self._lock:
            if self._is_recording:
                return
                
            self._init_audio()
            self._frames = []
            
            # ストリームを開く
            self._stream = self._audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.SAMPLE_RATE,
                input=True,
                frames_per_buffer=self.CHUNK_SIZE,
                stream_callback=self._audio_callback
            )
            
            self._is_recording = True
            self._stream.start_stream()
            
    def _audio_callback(
        self,
        in_data: bytes,
        frame_count: int,
        time_info: dict,
        status: int
    ) -> tuple[None, int]:
        """
        音声データのコールバック関数
        
        PyAudioから呼び出され、音声データをバッファに蓄積する。
        
        Args:
            in_data: 録音された音声データ
            frame_count: フレーム数
            time_info: タイミング情報
            status: ステータスフラグ
            
        Returns:
            (None, paContinue) で録音を継続
        """
        if self._is_recording:
            self._frames.append(in_data)
        return (None, pyaudio.paContinue)
    
    def stop(self) -> Optional[np.ndarray]:
        """
        録音を停止し、録音データを返す
        
        Returns:
            録音された音声データ（float32 numpy配列、-1.0〜1.0に正規化）
            録音していなかった場合はNone
        """
        with self._lock:
            if not self._is_recording:
                return None
                
            self._is_recording = False
            
            # ストリームを停止・閉じる
            if self._stream is not None:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None
                
            # フレームが空の場合
            if not self._frames:
                return None
                
            # バイトデータをnumpy配列に変換
            audio_bytes = b''.join(self._frames)
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # float32に変換し、-1.0〜1.0に正規化（Whisperの入力形式）
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            
            self._frames = []
            return audio_float32
            
    def get_audio_chunk(self) -> Optional[np.ndarray]:
        """
        現在の録音バッファからデータを取得し、バッファをクリアする（逐次処理用）
        
        Returns:
            前回取得時以降の音声データ（float32）。データがない場合はNone
        """
        with self._lock:
            if not self._is_recording or not self._frames:
                return None
                
            # バイトデータをnumpy配列に変換
            audio_bytes = b''.join(self._frames)
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # float32に変換
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            
            # バッファをクリア（取得した分は削除）
            self._frames = []
            return audio_float32
    
    def is_recording(self) -> bool:
        """
        録音中かどうかを返す
        
        Returns:
            録音中ならTrue
        """
        return self._is_recording
    
    def get_duration(self) -> float:
        """
        現在の録音時間（秒）を返す
        
        Returns:
            録音時間（秒）
        """
        if not self._frames:
            return 0.0
        total_samples = len(self._frames) * self.CHUNK_SIZE
        return total_samples / self.SAMPLE_RATE
    
    def dispose(self) -> None:
        """リソースを解放する"""
        self.stop()
        self._cleanup_audio()


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    import time
    
    print("録音テスト開始...")
    recorder = AudioRecorder()
    
    print("3秒間録音します...")
    recorder.start()
    time.sleep(3)
    audio_data = recorder.stop()
    
    if audio_data is not None:
        print(f"録音完了: {len(audio_data)} サンプル")
        print(f"録音時間: {len(audio_data) / AudioRecorder.SAMPLE_RATE:.2f} 秒")
        print(f"最大振幅: {np.max(np.abs(audio_data)):.4f}")
    else:
        print("録音データがありません")
        
    recorder.dispose()
    print("テスト終了")
