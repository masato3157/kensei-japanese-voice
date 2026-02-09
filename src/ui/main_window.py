# -*- coding: utf-8 -*-
"""
メインウィンドウ - 賢声のメインUI

このモジュールは、賢声アプリケーションのメインウィンドウを提供します。
すべてのコンポーネント（録音、認識、AI整形）を統合し、
コンテキスト主導の高精度音声入力を実現します。

機能:
- 左Ctrl: プッシュ・トゥ・トーク録音
- 右Ctrl: 録音トグル
- ContextManagerによる文脈参照で同音異義語を判定
- LearningEngineによる文体学習
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from datetime import datetime
from typing import Optional
import time
import keyboard
import pyperclip

# 内部モジュール
from src import __version__
from src.audio.recorder import AudioRecorder
from src.audio.transcriber import AudioTranscriber
from src.ai.hybrid_corrector import HybridCorrector
from src.utils.keyboard_handler import KeyboardHandler
from src.utils.clipboard import paste_text
from src.ui.settings_dialog import SettingsDialog
from src.ui.display_window import DisplayWindow
from src.utils.config_manager import ConfigManager


class MainWindow:
    """
    賢声のメインウィンドウクラス（v0.4.7 シンプル版）
    
    責務:
    - アプリケーションのメインUIを表示
    - 左Ctrlキーでプッシュ・トゥ・トーク録音
    - 右Ctrlキーで録音トグル
    - Whisperで音声認識 → GroqでAI整形
    - ContextManagerによる文脈参照
    """
    
    # ウィンドウサイズの定数
    WINDOW_WIDTH = 450
    WINDOW_HEIGHT = 420
    
    def __init__(self, root: tk.Tk):
        """
        メインウィンドウを初期化する
        
        Args:
            root: TkinterのルートウィンドウまたはToplevel
        """
        self.root = root
        
        # === UIの先行構築（ログ出力を可能にする） ===
        self._setup_window()
        self._create_widgets()
        
        # === コンポーネントの初期化 ===
        self._init_components()
        
        # === キーボード監視の開始 ===
        self._setup_keyboard_handler()
        
        # === 右Ctrlキーのホットキー設定 ===
        self._setup_toggle_hotkey()
        
        # === 性格パラメータの初期表示 ===
        self.update_stats_display()
        
        # === ユーザー表示用ミニウィンドウ ===
        self._display_window = DisplayWindow(self.root)
        self._display_window.update_text("賢声を起動しました。音声入力を待機中...")
        
        # 準備完了メッセージ
        self.add_log("[システム] すべての準備が整いました")
        self.add_log("[ヒント] 左Ctrl: 押している間録音（プッシュ・トゥ・トーク）")
        self.add_log("[ヒント] 右Ctrl: 録音開始/停止（トグルモード）")
        self.set_status("待機中...", "green")
        
    def _init_components(self) -> None:
        """音声処理・AIコンポーネントを初期化する"""
        
        # 録音コンポーネント
        self.add_log("[初期化] 録音モジュール...")
        self._recorder = AudioRecorder()
        
        # マイク情報を表示
        mic_name = self._recorder.get_default_input_device_name()
        self.add_log(f"[マイク] {mic_name}")
        
        # 認識コンポーネント（初回はモデル読み込みに時間がかかる）
        self.add_log("[初期化] 音声認識モデル (Whisper)...")
        self.set_status("Whisperモデル読み込み中...", "orange")
        self.root.update()
        self._transcriber = AudioTranscriber()
        
        # AI整形コンポーネント（Groq API + 学習機能）
        # === AI整形コンポーネント（ハイブリッド）===
        self.add_log("[初期化] AI校正エンジン...")
        try:
            self._corrector = HybridCorrector()
            self._ai_enabled = True
        except Exception as e:
            self._corrector = None
            self._ai_enabled = False
            self.add_log(f"[エラー] AIエンジン初期化失敗: {e}")
        
        # キーボードハンドラー
        self._keyboard_handler = KeyboardHandler()
        
        # 変換中フラグ（二重実行防止）
        self._is_processing = False
        
        # トグル録音状態
        self._is_toggle_recording = False
        
        # デバウンス用（キーリピート防止）
        self._last_toggle_time = 0.0
        
        # 直前の音声認識結果（手動修正用）
        self._last_voice_text: Optional[str] = None
        
        # 逐次認識用のバッファ（v0.6.9）
        # 各チャンクの認識結果をリストとして保持
        self._current_text_buffer: list[str] = []
        # 逐次処理ループの制御フラグ
        self._is_streaming = False
        
    def _setup_keyboard_handler(self) -> None:
        """キーボードハンドラーを設定する（左Ctrl用）"""
        self._keyboard_handler.on_key_down = self._on_recording_start
        self._keyboard_handler.on_key_up = self._on_recording_stop
        self._keyboard_handler.start()
        
    def _setup_toggle_hotkey(self) -> None:
        """右Ctrlキーのホットキーを設定する"""
        # キーリピート対策: 押下フラグを使用
        self._right_ctrl_pressed = False
        
        # 右Ctrlのscan_code = 285
        keyboard.hook(self._handle_hotkey_event)
        print("[MainWindow] 右Ctrl: 録音トグル")
        
    def _handle_hotkey_event(self, event: keyboard.KeyboardEvent) -> None:
        """ホットキーイベントを処理する"""
        # 右Ctrl (scan_code=285) のみ処理
        if event.scan_code != 285:
            return
            
        if event.event_type == keyboard.KEY_DOWN:
            self._on_right_ctrl_press()
        elif event.event_type == keyboard.KEY_UP:
            self._on_right_ctrl_release()
        
    def _on_right_ctrl_press(self) -> None:
        """右Ctrlキー押下時（録音トグルのみ）"""
        # 既に押下済みなら無視（キーリピート対策）
        if self._right_ctrl_pressed:
            return
        self._right_ctrl_pressed = True
        
        if self._is_processing:
            return
            
        self._toggle_recording()
        
    def _on_right_ctrl_release(self) -> None:
        """右Ctrlキー離上時"""
        self._right_ctrl_pressed = False
        
    def _on_recording_start(self) -> None:
        """録音開始時の処理（左Ctrlキー押下）"""
        if self._is_processing:
            return
            
        # トグル録音中の場合は無視
        if self._is_toggle_recording:
            return
            
        # 録音開始
        self._start_recording_session()
        
    def _toggle_recording(self) -> None:
        """右Ctrlキーでの録音トグル処理"""
        if self._is_processing:
            return
            
        if not self._is_toggle_recording:
            # 録音開始
            self._is_toggle_recording = True
            self._start_recording_session()
            self.root.after(0, lambda: self.add_log("[録音] 開始（トグルモード）"))
        else:
            # 録音停止
            self._is_toggle_recording = False
            self._stop_and_process()

    def _start_recording_session(self) -> None:
        """録音セッションを開始する（共通処理）"""
        self._recorder.start()
        self._current_text_buffer = [] # バッファリセット
        self._is_streaming = True
        
        self.root.after(0, lambda: self.set_status("● 録音中...", "red"))
        
        # 逐次処理ループを別スレッドで開始
        threading.Thread(
            target=self._process_stream_loop,
            daemon=True
        ).start()

    def _process_stream_loop(self) -> None:
        """
        逐次認識ループ（録音中に並列実行）
        約1秒ごとに音声チャンクを取得し、ASRにかける
        """
        import time
        import re
        CHUNK_INTERVAL = 1.0 # 1秒ごとに認識
        
        while self._is_streaming and self._recorder.is_recording():
            time.sleep(CHUNK_INTERVAL)
            
            if not self._is_streaming: # sleep中に停止された場合
                break
                
            # 音声チャンクを取得
            chunk_data = self._recorder.get_audio_chunk()
            if chunk_data is None or len(chunk_data) == 0:
                continue
                
            # ASR実行（チャンク認識）
            try:
                partial_text = self._transcriber.transcribe(chunk_data)
                
                if partial_text and partial_text.strip():
                    # バッファに追加
                    self._current_text_buffer.append(partial_text.strip())
                    
                    # 現在の全テキストを結合（日本語なのでスペースなしで結合）
                    current_full_text = "".join(self._current_text_buffer)
                    
                    # 文末記号で分割 (。, ？, ！)
                    # 肯定先読み (?<=...) を使って区切り文字を含めて分割する手もあるが、
                    # シンプルに re.split で分割し、区切り文字をキャプチャする
                    parts = re.split(r'([。？！])', current_full_text)
                    
                    confirmed_text = ""
                    remaining_text = ""
                    
                    if len(parts) >= 3:
                        # 少なくとも1つの文末記号が含まれている
                        # 例: ["こんにちは", "。", "元気ですか", "？", "まだ続き"]
                        
                        # 確定部分の構築（最後の要素以外）
                        # 最後の要素が空文字列でないなら、それは未確定部分
                        # 最後の要素が空文字列なら、ちょうど文末で終わっている
                        
                        # 配列の末尾が未確定部分になる可能性があるため、
                        # 後ろから見て区切り文字でないものを除去する
                        
                        last_part = parts[-1]
                        confirmed_parts = parts[:-1]
                        
                        remaining_text = last_part
                        confirmed_text = "".join(confirmed_parts)
                        
                        # バッファをリセットし、未確定部分のみ再セット
                        self._current_text_buffer = [remaining_text] if remaining_text else []
                        
                        # === 確定文の即時処理 ===
                        if confirmed_text:
                            self.root.after(0, lambda t=confirmed_text: self.add_log(f"[文確定] {t}"))
                            
                            # 校正・貼り付け（別スレッドで実行した方がUIがスムーズだが、
                            # _process_stream_loop自体が別スレッドなのでここで実行してよい）
                            self._process_confirmed_text(confirmed_text)
                    
                    else:
                        # 文末記号がない -> 全て未確定
                        remaining_text = current_full_text

                    # UI更新（未確定部分のみ表示）
                    if remaining_text:
                        self.root.after(0, lambda t=remaining_text: self._display_window.update_text(f"🎤 {t} ..."))
                        # ログにはチャンクごとの追加分を出すと煩雑になるので、文確定時のみログ出力に変更しても良いが、
                        # 動作確認のため一旦チャンクも出す（ただし頻度が高いので抑制気味に）
                        # self.root.after(0, lambda t=partial_text: self.add_log(f"[認識(仮)] {t}"))
                    
            except Exception as e:
                print(f"[StreamLoop] Error: {e}")

    def _process_confirmed_text(self, text: str) -> None:
        """確定した文を校正して貼り付ける"""
        final_text = text
        
        # 校正
        if self._ai_enabled and self._corrector is not None:
             self.root.after(0, lambda: self.set_status("🧠 AI校正中...", "purple"))
             # 一文単位なので高速に終わるはず
             final_text = self._corrector.correct(text)
             
             if final_text != text:
                 self.root.after(0, lambda t=final_text: self.add_log(f"[校正] {t}"))
        
        # 貼り付け
        if final_text:
            paste_text(final_text)
            # 校正完了したらステータスを戻すわけにはいかない（録音中なので）、
            # UI更新は録音中のものに戻す
            self.root.after(0, lambda: self.set_status("● 録音中...", "red"))

    def _on_recording_stop(self) -> None:
        """録音停止時の処理（左Ctrlキー離上）"""
        # トグル録音中の場合は左Ctrl離上を無視
        if self._is_toggle_recording:
            return
            
        if not self._recorder.is_recording():
            return
            
        if self._is_processing:
            return
            
        self._stop_and_process()
        
    def _stop_and_process(self) -> None:
        """録音を停止して処理を開始する"""
        self._is_processing = True
        self._is_streaming = False # ストリーミングループ停止
        
        # 録音停止・残りのデータ取得
        remaining_data = self._recorder.stop()
        
        self.root.after(0, lambda: self.set_status("🎤 処理中...", "orange"))
        
        # クリップボードの内容を取得（自動判定用）
        try:
            clipboard_content = pyperclip.paste()
        except Exception:
            clipboard_content = ""
            
        # 最終処理を別スレッドで実行
        threading.Thread(
            target=self._process_audio_final,
            args=(remaining_data, clipboard_content),
            daemon=True
        ).start()
        
    def _process_audio_final(self, audio_data, clipboard_content: str) -> None:
        """最終的な音声処理と校正（処理完了後）"""
        try:
            # 残りの音声を認識
            if audio_data is not None and len(audio_data) > 0:
                last_text = self._transcriber.transcribe(audio_data)
                if last_text and last_text.strip():
                    self._current_text_buffer.append(last_text.strip())
                    self.root.after(0, lambda t=last_text: self.add_log(f"[認識(残)] {t}"))

            # 未確定バッファに残っているテキストを処理
            full_text = "".join(self._current_text_buffer).strip()
            
            if not full_text:
                self.root.after(0, lambda: self.add_log("[認識] テキストなし"))
                self.root.after(0, lambda: self.set_status("待機中...", "green"))
                self._is_processing = False
                return

            self.root.after(0, lambda: self.add_log(f"[認識(確定)] {full_text}"))
            
            # === 校正フェーズ (残余分) ===
            final_text = full_text
            
            if self._ai_enabled and self._corrector is not None:
                self.root.after(0, lambda: self.set_status("🧠 AI校正中...", "purple"))
                
                final_text = self._corrector.correct(full_text)
                
                if final_text != full_text:
                    self.root.after(0, lambda: self.add_log(f"[校正] {final_text}"))
                
                # ミニウィンドウ更新
                self._display_window.root.after(
                    0, lambda t=final_text: self._display_window.update_text(f"✔ {t}")
                )
            
            # 貼り付け
            paste_text(final_text)
            self.root.after(0, lambda: self.set_status("✔ 完了", "blue"))

        except Exception as e:
            self.root.after(0, lambda: self.add_log(f"[エラー] {str(e)}"))
            self.root.after(0, lambda: self.set_status("エラー発生", "red"))
            
        finally:
            self._is_processing = False
            self.root.after(2000, lambda: self.set_status("待機中...", "green"))
            
    def update_stats_display(self) -> None:
        """性格パラメータの表示を更新する"""
        try:
            if self._corrector is None or not self._ai_enabled:
                if hasattr(self, '_stats_label'):
                    self._stats_label.config(text="AI機能が無効です")
                return
            
            # HybridCorrectorの場合
            if isinstance(self._corrector, HybridCorrector):
                try:
                    config = ConfigManager.get_instance()
                    mode = config.settings.inference_mode.upper()
                    if hasattr(self, '_stats_label'):
                        self._stats_label.config(text=f"AI Mode: {mode}")
                except:
                    pass
                return
                
            # TextCorrectorの場合（互換性）
            if hasattr(self._corrector, 'user_profile'):
                data = self._corrector.user_profile.data
                stats_text = (
                    f"硬さ: {data.formality:.1f}  "
                    f"情緒: {data.emotionality:.1f}  "
                    f"断定: {data.assertiveness:.1f}  "
                    f"密度: {data.density:.1f}  "
                    f"語彙: {data.vocabulary:.1f}"
                )
                if hasattr(self, '_stats_label'):
                    self._stats_label.config(text=stats_text)
            
        except Exception as e:
            print(f"[MainWindow] パラメータ表示エラー: {e}")
            if hasattr(self, '_stats_label'):
                self._stats_label.config(text="データ取得エラー")
        
    def _setup_window(self) -> None:
        """ウィンドウの基本設定を行う"""
        self.root.title(f"賢声 - 賢い日本語音声入力 (v{__version__})")
        
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.root.minsize(400, 350)
        
        self._center_window()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _center_window(self) -> None:
        """ウィンドウを画面中央に配置する"""
        self.root.update_idletasks()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - self.WINDOW_WIDTH) // 2
        y = (screen_height - self.WINDOW_HEIGHT) // 2
        
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x}+{y}")
        
    def _create_widgets(self) -> None:
        """UIコンポーネントを作成する"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === ヘッダー部分 ===
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(
            header_frame,
            text="賢声",
            font=("Yu Gothic UI", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        version_label = ttk.Label(
            header_frame,
            text=f"v{__version__}",
            font=("Yu Gothic UI", 9),
            foreground="gray"
        )
        version_label.pack(side=tk.LEFT, padx=(5, 0), pady=(8, 0))
        
        self.settings_button = ttk.Button(
            header_frame,
            text="⚙ 設定",
            command=self._open_settings
        )
        self.settings_button.pack(side=tk.RIGHT)
        
        # === ステータス表示 ===
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(
            status_frame,
            text="初期化中...",
            font=("Yu Gothic UI", 11),
            foreground="gray"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # === ログ表示エリア ===
        log_label = ttk.Label(main_frame, text="処理ログ:")
        log_label.pack(anchor=tk.W)
        
        self.log_area = scrolledtext.ScrolledText(
            main_frame,
            height=10,
            wrap=tk.WORD,
            font=("Yu Gothic UI", 9),
            state=tk.DISABLED
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # === 性格パラメータ表示エリア ===
        stats_frame = ttk.LabelFrame(main_frame, text="現在の性格パラメータ", padding="5")
        stats_frame.pack(fill=tk.X, pady=(0, 0))
        
        self._stats_label = ttk.Label(
            stats_frame,
            text="読み込み中...",
            font=("Yu Gothic UI", 9),
            foreground="navy"
        )
        self._stats_label.pack(anchor=tk.W)
        
    def _open_settings(self) -> None:
        """設定ダイアログを開く"""
        from src.ui.settings_dialog import SettingsDialog
        SettingsDialog(self.root, on_save=self._on_settings_saved)
    
    def _on_settings_saved(self) -> None:
        """設定保存後のコールバック"""
        # 必要であればコレクターのリロードなどを行う
        if self._corrector and isinstance(self._corrector, HybridCorrector):
            self._corrector._reload_engine()
        
        self.add_log("[設定] 設定が保存されました")
        self.update_stats_display()
        
    def _on_closing(self) -> None:
        """ウィンドウを閉じる際の処理"""
        self.add_log("[システム] 終了処理中...")
        
        # ホットキーを解除
        keyboard.unhook_all_hotkeys()
        
        self._keyboard_handler.stop()
        self._recorder.dispose()
        self._transcriber.dispose()
        
        if self._corrector is not None:
            self._corrector.dispose()
        
        # ミニウィンドウを閉じる
        if hasattr(self, '_display_window'):
            self._display_window.close()
        
        self.root.destroy()
        
    def add_log(self, message: str) -> None:
        """ログエリアにメッセージを追加する"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, formatted_message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        
    def set_status(self, status: str, color: str = "gray") -> None:
        """ステータス表示を更新する"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=status, foreground=color)

    def run(self) -> None:
        """メインループを開始する"""
        self.root.mainloop()


def create_main_window() -> MainWindow:
    """メインウィンドウを作成するファクトリ関数"""
    root = tk.Tk()
    return MainWindow(root)


if __name__ == "__main__":
    window = create_main_window()
    window.run()
