# -*- coding: utf-8 -*-
"""
メインウィンドウ - 賢声のメインUI（最終完成版）

このモジュールは、賢声アプリケーションのメインウィンドウを提供します。
すべてのコンポーネント（録音、認識、AI整形、キーボード、クリップボード）を統合し、
プッシュ・トゥ・トーク方式の高精度音声入力を実現します。

処理フロー:
1. 左Ctrlキー押下 → 録音開始
2. 左Ctrlキー離上 → 録音停止 → Whisperで文字起こし → LlamaでAI整形 → 貼り付け
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from datetime import datetime
from typing import Optional

# 内部モジュール
from src.audio.recorder import AudioRecorder
from src.audio.transcriber import AudioTranscriber
from src.ai.corrector import TextCorrector
from src.utils.keyboard_handler import KeyboardHandler
from src.utils.clipboard import paste_text
from src.utils import config


class MainWindow:
    """
    賢声のメインウィンドウクラス（最終完成版）
    
    責務:
    - アプリケーションのメインUIを表示
    - 左Ctrlキーでプッシュ・トゥ・トーク録音
    - Whisperで音声認識 → LlamaでAI整形
    - 認識結果をクリップボード経由で貼り付け
    """
    
    # ウィンドウサイズの定数
    WINDOW_WIDTH = 420
    WINDOW_HEIGHT = 350
    
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
        
        # 準備完了メッセージ
        self.add_log("[システム] すべての準備が整いました")
        self.add_log("[ヒント] 左Ctrlキーを押している間、録音します")
        self.set_status("待機中... (左Ctrlキーで録音)", "green")
        
    def _init_components(self) -> None:
        """音声処理・AIコンポーネントを初期化する"""
        
        # 録音コンポーネント
        self.add_log("[初期化] 録音モジュール...")
        self._recorder = AudioRecorder()
        
        # 認識コンポーネント（初回はモデル読み込みに時間がかかる）
        self.add_log("[初期化] 音声認識モデル (Whisper)...")
        self.set_status("Whisperモデル読み込み中...", "orange")
        self.root.update()  # UIを更新
        self._transcriber = AudioTranscriber()
        
        # AI整形コンポーネント（LLMモデル読み込み）
        self.add_log("[初期化] AI整形モデル (Llama)...")
        self.set_status("LLMモデル読み込み中...", "orange")
        self.root.update()  # UIを更新
        
        # モデルの存在確認
        if config.model_exists():
            self._corrector = TextCorrector()
            self._ai_enabled = True
            self.add_log("[初期化] AI整形: 有効")
        else:
            self._corrector = None
            self._ai_enabled = False
            self.add_log("[初期化] AI整形: 無効 (モデルなし)")
            self.add_log(f"[ヒント] models/ に GGUF ファイルを配置してください")
        
        # キーボードハンドラー
        self._keyboard_handler = KeyboardHandler()
        
        # 変換中フラグ（二重実行防止）
        self._is_processing = False
        
    def _setup_keyboard_handler(self) -> None:
        """キーボードハンドラーを設定する"""
        self._keyboard_handler.on_key_down = self._on_recording_start
        self._keyboard_handler.on_key_up = self._on_recording_stop
        self._keyboard_handler.start()
        
    def _on_recording_start(self) -> None:
        """録音開始時の処理（左Ctrlキー押下）"""
        # 変換中は無視
        if self._is_processing:
            return
            
        # 録音開始
        self._recorder.start()
        
        # UI更新（メインスレッドで実行）
        self.root.after(0, lambda: self.set_status("● 録音中...", "red"))
        self.root.after(0, lambda: self.add_log(f"[録音] 開始"))
        
    def _on_recording_stop(self) -> None:
        """録音停止時の処理（左Ctrlキー離上）"""
        # 録音していない場合は無視
        if not self._recorder.is_recording():
            return
            
        # 変換中は無視
        if self._is_processing:
            return
            
        self._is_processing = True
        
        # 録音停止・データ取得
        audio_data = self._recorder.stop()
        
        if audio_data is None or len(audio_data) == 0:
            self._is_processing = False
            self.root.after(0, lambda: self.set_status("待機中... (左Ctrlキーで録音)", "green"))
            self.root.after(0, lambda: self.add_log("[録音] データなし（キャンセル）"))
            return
            
        # UI更新
        duration = len(audio_data) / 16000
        self.root.after(0, lambda: self.set_status("🎤 変換中...", "orange"))
        self.root.after(0, lambda: self.add_log(f"[録音] 終了 ({duration:.1f}秒)"))
        
        # 別スレッドで処理を実行（UIがフリーズしないように）
        threading.Thread(
            target=self._process_audio,
            args=(audio_data,),
            daemon=True
        ).start()
        
    def _process_audio(self, audio_data) -> None:
        """
        音声処理パイプラインを実行する（別スレッドで実行）
        
        処理フロー:
        1. Whisperで文字起こし
        2. Llamaで文章整形（AI有効時のみ）
        3. クリップボード経由で貼り付け
        
        Args:
            audio_data: 音声データ（float32 numpy配列）
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
            
            # === ステップ2: AI整形 (Llama) ===
            if self._ai_enabled and self._corrector is not None:
                self.root.after(0, lambda: self.set_status("🧠 AI思考中...", "purple"))
                
                corrected_text = self._corrector.correct(raw_text.strip())
                
                if corrected_text and corrected_text.strip():
                    final_text = corrected_text.strip()
                    self.root.after(0, lambda: self.add_log(f"[整形] {final_text}"))
                else:
                    final_text = raw_text.strip()
            else:
                # AI無効時は認識結果をそのまま使用
                final_text = raw_text.strip()
            
            # === ステップ3: 貼り付け ===
            paste_text(final_text)
            
            self.root.after(0, lambda: self.set_status("✔ 貼り付け完了", "blue"))
                
        except Exception as e:
            self.root.after(0, lambda: self.add_log(f"[エラー] {str(e)}"))
            self.root.after(0, lambda: self.set_status("エラー発生", "red"))
            
        finally:
            self._is_processing = False
            # 少し待ってから待機状態に戻す
            self.root.after(2000, lambda: self.set_status("待機中... (左Ctrlキーで録音)", "green"))
        
    def _setup_window(self) -> None:
        """ウィンドウの基本設定を行う"""
        self.root.title("賢声 - 賢い日本語音声入力")
        
        # ウィンドウサイズと位置を設定
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.root.minsize(350, 250)
        
        # ウィンドウを画面中央に配置
        self._center_window()
        
        # 閉じるボタンの動作を設定
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
        # メインフレーム（パディング付き）
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === ヘッダー部分 ===
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # タイトルラベル
        title_label = ttk.Label(
            header_frame,
            text="賢声",
            font=("Yu Gothic UI", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # バージョン表示
        version_label = ttk.Label(
            header_frame,
            text="v0.2",
            font=("Yu Gothic UI", 9),
            foreground="gray"
        )
        version_label.pack(side=tk.LEFT, padx=(5, 0), pady=(8, 0))
        
        # 設定ボタン
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
            height=12,
            wrap=tk.WORD,
            font=("Yu Gothic UI", 9),
            state=tk.DISABLED  # 読み取り専用
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
    def _open_settings(self) -> None:
        """設定画面を開く（未実装）"""
        self.add_log("[システム] 設定画面は準備中です...")
        
    def _on_closing(self) -> None:
        """ウィンドウを閉じる際の処理"""
        self.add_log("[システム] 終了処理中...")
        
        # キーボード監視を停止
        self._keyboard_handler.stop()
        
        # 録音を停止
        self._recorder.dispose()
        
        # 認識コンポーネントを解放
        self._transcriber.dispose()
        
        # AI整形コンポーネントを解放
        if self._corrector is not None:
            self._corrector.dispose()
        
        # ウィンドウを閉じる
        self.root.destroy()
        
    def add_log(self, message: str) -> None:
        """
        ログエリアにメッセージを追加する
        
        Args:
            message: 表示するメッセージ
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, formatted_message + "\n")
        self.log_area.see(tk.END)  # 最新行にスクロール
        self.log_area.config(state=tk.DISABLED)
        
    def set_status(self, status: str, color: str = "gray") -> None:
        """
        ステータス表示を更新する
        
        Args:
            status: 表示するステータス文字列
            color: テキストの色
        """
        self.status_label.config(text=status, foreground=color)
        
    def run(self) -> None:
        """メインループを開始する"""
        self.root.mainloop()


def create_main_window() -> MainWindow:
    """
    メインウィンドウを作成するファクトリ関数
    
    Returns:
        MainWindow: 初期化されたメインウィンドウ
    """
    root = tk.Tk()
    return MainWindow(root)


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    window = create_main_window()
    window.run()
