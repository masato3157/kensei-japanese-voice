# -*- coding: utf-8 -*-
"""
AI補正機能のテストスクリプト

TextCorrectorの動作確認用です。
"""

import time
from src.ai.corrector import TextCorrector


def main():
    print("=" * 50)
    print("AI補正機能テスト")
    print("=" * 50)
    print()
    
    # モデル読み込み
    print("【1】モデル読み込み中...")
    start_time = time.time()
    
    corrector = TextCorrector()
    
    load_time = time.time() - start_time
    print(f"✔ 読み込み完了 ({load_time:.2f}秒)")
    print()
    
    # テスト入力
    test_input = "こんにちは私は検性です"
    
    print("【2】補正テスト")
    print(f"入力: 「{test_input}」")
    print()
    
    # 補正実行
    print("処理中...")
    start_time = time.time()
    
    result = corrector.correct(test_input)
    
    process_time = time.time() - start_time
    print()
    print(f"出力: 「{result}」")
    print(f"処理時間: {process_time:.2f}秒")
    print()
    
    # リソース解放
    corrector.dispose()
    
    print("=" * 50)
    print("テスト完了")
    print("=" * 50)


if __name__ == "__main__":
    main()
