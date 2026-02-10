# -*- coding: utf-8 -*-
import time
import sys
from pathlib import Path
# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.audio.recorder import AudioRecorder
from src.audio.transcriber import AudioTranscriber

def main():
    print("【開始】初期化中...")
    print("※初回はAIモデルのダウンロードが行われます（数分かかる場合があります）。")
    
    # 1. AIの準備
    try:
        transcriber = AudioTranscriber(model_size="base", device="cpu", compute_type="int8")
        print("✔ AIモデルの準備OK")
    except Exception as e:
        print(f"✖ AIモデルのエラー: {e}")
        return

    # 2. マイクの準備
    recorder = AudioRecorder()
    
    print("\n=== マイクテスト ===")
    print("5秒間、マイクに向かって何か話してください...")
    print("3...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1... スタート！")
    
    # 録音開始
    recorder.start()
    time.sleep(5)
    # 録音停止
    audio_data = recorder.stop()
    
    print("録音終了。文字に変換しています...")
    
    # 3. 文字起こし
    if audio_data is not None:
        text = transcriber.transcribe(audio_data)
        print("\n=== 結果 ===")
        print(f"認識された文字: 「{text}」")
    else:
        print("音声データが空でした。マイク設定を確認してください。")
    
    recorder.dispose()
    transcriber.dispose()

if __name__ == "__main__":
    main()