# -*- coding: utf-8 -*-
"""
キーボードハンドラー - グローバルホットキーの監視

このモジュールは、グローバルなキーボードイベントを監視し、
プッシュ・トゥ・トーク方式の操作を実現します。
"""

import keyboard
import threading
from typing import Callable, Optional


class KeyboardHandler:
    """
    キーボードイベントハンドラー
    
    左Ctrlキーの押し下げ・離上を検知し、コールバック関数を呼び出します。
    重複イベント防止のフラグ管理を内蔵しています。
    
    使用例:
        handler = KeyboardHandler()
        handler.on_key_down = lambda: print("押された")
        handler.on_key_up = lambda: print("離された")
        handler.start()
    """
    
    # 監視するキー
    TRIGGER_KEY = "ctrl"  # 左Ctrl
    
    def __init__(self):
        """ハンドラーを初期化する"""
        self._is_key_pressed = False       # キーが押されているか
        self._is_running = False           # 監視中か
        self._lock = threading.Lock()      # 競合防止用ロック
        
        # コールバック関数（外部から設定）
        self.on_key_down: Optional[Callable[[], None]] = None
        self.on_key_up: Optional[Callable[[], None]] = None
        
    def _handle_key_event(self, event: keyboard.KeyboardEvent) -> None:
        """
        キーイベントを処理する
        
        重複イベントを防止し、状態変化時のみコールバックを呼び出す。
        
        Args:
            event: キーボードイベント
        """
        with self._lock:
            # 左Ctrlキーのみを処理（scan_code 29 = 左Ctrl, 285 = 右Ctrl）
            # event.name == "ctrl" は左右どちらでも一致するため、scan_codeで判定
            if event.name != "ctrl" or event.scan_code != 29:
                return
                
            if event.event_type == keyboard.KEY_DOWN:
                # 既に押されている場合は無視（重複防止）
                if self._is_key_pressed:
                    return
                    
                self._is_key_pressed = True
                
                # コールバックを呼び出し
                if self.on_key_down is not None:
                    # 別スレッドで実行（ブロッキング防止）
                    threading.Thread(
                        target=self.on_key_down,
                        daemon=True
                    ).start()
                    
            elif event.event_type == keyboard.KEY_UP:
                # 押されていない場合は無視
                if not self._is_key_pressed:
                    return
                    
                self._is_key_pressed = False
                
                # コールバックを呼び出し
                if self.on_key_up is not None:
                    threading.Thread(
                        target=self.on_key_up,
                        daemon=True
                    ).start()
                    
    def start(self) -> None:
        """
        キーボード監視を開始する
        
        既に開始している場合は何もしない。
        """
        if self._is_running:
            return
            
        self._is_running = True
        
        # グローバルフックを登録
        keyboard.hook(self._handle_key_event)
        
        print("[KeyboardHandler] 監視開始 (左Ctrlキー)")
        
    def stop(self) -> None:
        """
        キーボード監視を停止する
        """
        if not self._is_running:
            return
            
        self._is_running = False
        
        # 自分のフックのみを解除（他モジュールのフックに影響しない）
        keyboard.unhook(self._handle_key_event)
        
        # 状態をリセット
        self._is_key_pressed = False
        
        print("[KeyboardHandler] 監視停止")
        
    def is_key_pressed(self) -> bool:
        """
        現在キーが押されているかを返す
        
        Returns:
            キーが押されていればTrue
        """
        return self._is_key_pressed
    
    def is_running(self) -> bool:
        """
        監視中かどうかを返す
        
        Returns:
            監視中ならTrue
        """
        return self._is_running


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    import time
    
    print("=== KeyboardHandler テスト ===")
    print("左Ctrlキーを押して離してみてください。")
    print("5秒後に自動終了します。")
    print()
    
    handler = KeyboardHandler()
    
    # コールバックを設定
    handler.on_key_down = lambda: print("→ キー押下検知！")
    handler.on_key_up = lambda: print("→ キー離上検知！")
    
    # 監視開始
    handler.start()
    
    # 5秒待機
    time.sleep(5)
    
    # 監視停止
    handler.stop()
    
    print("\nテスト終了")
