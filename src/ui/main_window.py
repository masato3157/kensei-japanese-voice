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
        self.add_log("[初期化] AI整形エンジン...")
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
        
    def _toggle_recording(self) -> None:
        """右Ctrlキーでの録音トグル処理"""
        if self._is_processing:
            return
            
        if not self._is_toggle_recording:
            # 録音開始
            self._is_toggle_recording = True
            self._recorder.start()
            self.root.after(0, lambda: self.set_status("● 録音中...（右Ctrlで停止）", "red"))
            self.root.after(0, lambda: self.add_log("[録音] 開始（トグルモード）"))
        else:
            # 録音停止
            self._is_toggle_recording = False
            self._stop_and_process()
        
    def _on_recording_start(self) -> None:
        """録音開始時の処理（左Ctrlキー押下）"""
        if self._is_processing:
            return
            
        # トグル録音中の場合は無視
        if self._is_toggle_recording:
            return
            
        self._recorder.start()
        
        self.root.after(0, lambda: self.set_status("● 録音中...", "red"))
        self.root.after(0, lambda: self.add_log("[録音] 開始"))
        
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
        
        # 録音停止・データ取得
        audio_data = self._recorder.stop()
        
        if audio_data is None or len(audio_data) == 0:
            self._is_processing = False
            self.root.after(0, lambda: self.set_status("待機中...", "green"))
            self.root.after(0, lambda: self.add_log("[録音] データなし（キャンセル）"))
            return
            
        # UI更新
        duration = len(audio_data) / 16000
        
        # 最低録音時間チェック（0.5秒未満はノイズとして無視）
        if duration < 0.5:
            self._is_processing = False
            self.root.after(0, lambda: self.set_status("待機中...", "green"))
            self.root.after(0, lambda: self.add_log("[録音] 短すぎます（0.5秒未満）"))
            return
        self.root.after(0, lambda: self.set_status("🎤 変換中...", "orange"))
        self.root.after(0, lambda: self.add_log(f"[録音] 終了 ({duration:.1f}秒)"))
        
        # クリップボードの内容を取得（自動判定用）
        try:
            clipboard_content = pyperclip.paste()
        except Exception:
            clipboard_content = ""
        
        # 別スレッドで処理を実行
        threading.Thread(
            target=self._process_audio,
            args=(audio_data, clipboard_content),
            daemon=True
        ).start()
        
    def _process_audio(self, audio_data, clipboard_content: str) -> None:
        """
        音声処理パイプラインを実行する（別スレッドで実行）
        
        処理フロー:
        1. Whisperで文字起こし
        2. クリップボードと比較して自動判定
        3. 修正 → 学習 / 新規入力 → 整形
        4. クリップボード経由で貼り付け
        5. 学習完了時は性格パラメータを更新
        
        Args:
            audio_data: 音声データ（float32 numpy配列）
            clipboard_content: クリップボードの内容
        """
        try:
            # === ステップ1: 音声認識 (Whisper) ===
            self.root.after(0, lambda: self.set_status("🎤 変換中...", "orange"))
            
            raw_text = self._transcriber.transcribe(audio_data)
            
            if not raw_text or not raw_text.strip():
                self.root.after(0, lambda: self.add_log("[認識] テキストなし"))
                self.root.after(0, lambda: self.set_status("待機中...", "green"))
                return
                
            self.root.after(0, lambda: self.add_log(f"[認識] {raw_text.strip()}"))
            
            # === ミニウィンドウに認識結果を表示 ===
            recognized = raw_text.strip()
            self._display_window.root.after(
                0, lambda t=recognized: self._display_window.update_text(f"🎤 {t}")
            )
            
            # === 直前の音声認識結果を保存（手動修正用） ===
            self._last_voice_text = raw_text.strip()
            
            # === ステップ2: AI整形（Hybrid） ===
            if self._ai_enabled and self._corrector is not None:
                self.root.after(0, lambda: self.set_status("🧠 AI思考中...", "purple"))
                
                # 単純な整形処理（モードに応じてCloud/Localが自動選択される）
                final_text = self._corrector.correct(raw_text.strip())
                
                if final_text != raw_text.strip():
                    self.root.after(0, lambda: self.add_log(f"[整形] {final_text}"))
                
                # ミニウィンドウを整形結果で更新
                self._display_window.root.after(
                    0, lambda t=final_text: self._display_window.update_text(f"✔ {t}")
                )
            else:
                final_text = raw_text.strip()
            
            # === ステップ3: 貼り付け ===
            paste_text(final_text)
            
            self.root.after(0, lambda: self.set_status("✔ 貼り付け完了", "blue"))
                
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
