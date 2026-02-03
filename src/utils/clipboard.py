# -*- coding: utf-8 -*-
"""
クリップボード - テキストのコピー・ペースト操作

このモジュールは、クリップボード経由でテキストを貼り付ける機能を提供します。
音声認識の結果をアクティブなアプリケーションに入力するために使用します。
"""

import pyperclip
import keyboard
import time
from typing import Optional


def copy_to_clipboard(text: str) -> bool:
    """
    テキストをクリップボードにコピーする
    
    Args:
        text: コピーするテキスト
        
    Returns:
        成功した場合True
    """
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        print(f"[Clipboard] コピー失敗: {e}")
        return False


def get_from_clipboard() -> Optional[str]:
    """
    クリップボードからテキストを取得する
    
    Returns:
        クリップボードのテキスト、取得失敗時はNone
    """
    try:
        return pyperclip.paste()
    except Exception as e:
        print(f"[Clipboard] 取得失敗: {e}")
        return None


def paste_text(text: str, delay: float = 0.1) -> bool:
    """
    テキストをクリップボードにコピーし、アクティブウィンドウに貼り付ける
    
    処理フロー:
    1. 元のクリップボード内容を保存
    2. 新しいテキストをクリップボードにコピー
    3. 少し待機（安定性のため）
    4. Ctrl+V を送信して貼り付け
    5. 元のクリップボード内容を復元
    
    Args:
        text: 貼り付けるテキスト
        delay: 貼り付け前の待機時間（秒）
        
    Returns:
        成功した場合True
    """
    if not text:
        return False
        
    try:
        # 元のクリップボード内容を保存
        original_clipboard = get_from_clipboard()
        
        # テキストをクリップボードにコピー
        if not copy_to_clipboard(text):
            return False
            
        # 少し待機（アプリケーションがフォーカスを得るため）
        time.sleep(delay)
        
        # Ctrl+V を送信して貼り付け
        keyboard.send("ctrl+v")
        
        # 貼り付け完了まで少し待機
        time.sleep(0.05)
        
        # 元のクリップボード内容を復元（任意）
        # 注意: 復元すると、ユーザーが直後にCtrl+Vしたときに
        #       古い内容が貼り付けられるため、復元しない方が自然かもしれない
        # if original_clipboard is not None:
        #     copy_to_clipboard(original_clipboard)
        
        return True
        
    except Exception as e:
        print(f"[Clipboard] 貼り付け失敗: {e}")
        return False


def type_text(text: str, interval: float = 0.01) -> bool:
    """
    テキストを直接タイプする（クリップボードを使わない方法）
    
    注意: 日本語は正しく入力できない場合があります。
    クリップボード経由の paste_text() を推奨します。
    
    Args:
        text: 入力するテキスト
        interval: キー入力間隔（秒）
        
    Returns:
        成功した場合True
    """
    try:
        keyboard.write(text, delay=interval)
        return True
    except Exception as e:
        print(f"[Clipboard] タイプ失敗: {e}")
        return False


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    print("=== Clipboard テスト ===")
    print()
    
    # コピーテスト
    test_text = "賢声テスト：これはテストメッセージです。"
    print(f"コピーするテキスト: {test_text}")
    
    if copy_to_clipboard(test_text):
        print("✔ クリップボードにコピー成功")
    else:
        print("✖ コピー失敗")
        
    # 取得テスト
    retrieved = get_from_clipboard()
    if retrieved == test_text:
        print("✔ クリップボードから正しく取得")
    else:
        print(f"✖ 取得結果が異なる: {retrieved}")
        
    print()
    print("--- 貼り付けテスト ---")
    print("3秒後に、現在アクティブなウィンドウにテキストを貼り付けます。")
    print("メモ帳などを開いて、カーソルを置いてください。")
    
    time.sleep(3)
    
    if paste_text("【賢声】貼り付けテスト成功！"):
        print("✔ 貼り付け完了")
    else:
        print("✖ 貼り付け失敗")
        
    print("\nテスト終了")
