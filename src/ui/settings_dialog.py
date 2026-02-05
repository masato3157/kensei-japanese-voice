# -*- coding: utf-8 -*-
"""
設定ダイアログ - アプリケーション設定UI

このモジュールは、設定を変更するためのダイアログウィンドウを提供します。
推論モード（Cloud/Local）の切り替えや、APIキー、モデルパスの設定が可能です。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Optional

from src.utils.config_manager import ConfigManager


class SettingsDialog:
    """
    設定ダイアログクラス
    
    アプリケーションの設定を変更するためのモーダルダイアログ。
    設定の変更は「保存」ボタンで確定され、JSONファイルに永続化されます。
    
    使用例:
        dialog = SettingsDialog(root, on_save=lambda: print("Saved!"))
    """
    
    # ダイアログサイズ
    DIALOG_WIDTH = 450
    DIALOG_HEIGHT = 480  # 高さを増やしてすべての要素を表示
    
    def __init__(
        self,
        parent: tk.Tk,
        on_save: Optional[Callable[[], None]] = None
    ):
        """
        設定ダイアログを初期化・表示する
        
        Args:
            parent: 親ウィンドウ
            on_save: 保存完了時に呼び出されるコールバック
        """
        self._parent = parent
        self._on_save = on_save
        self._config = ConfigManager.get_instance()
        
        # ダイアログウィンドウを作成
        self._dialog = tk.Toplevel(parent)
        self._setup_dialog()
        self._create_widgets()
        self._load_current_settings()
        
        # モーダル化（親ウィンドウを操作不可に）
        self._dialog.transient(parent)
        self._dialog.grab_set()
        
    def _setup_dialog(self) -> None:
        """ダイアログウィンドウを設定する"""
        self._dialog.title("設定")
        self._dialog.geometry(f"{self.DIALOG_WIDTH}x{self.DIALOG_HEIGHT}")
        self._dialog.resizable(False, False)
        
        # 中央に配置
        self._center_dialog()
        
        # 閉じるボタン（X）の処理
        self._dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
    def _center_dialog(self) -> None:
        """ダイアログを親ウィンドウの中央に配置する"""
        self._dialog.update_idletasks()
        
        # 親ウィンドウの位置とサイズを取得
        parent_x = self._parent.winfo_x()
        parent_y = self._parent.winfo_y()
        parent_width = self._parent.winfo_width()
        parent_height = self._parent.winfo_height()
        
        # 中央位置を計算
        x = parent_x + (parent_width - self.DIALOG_WIDTH) // 2
        y = parent_y + (parent_height - self.DIALOG_HEIGHT) // 2
        
        self._dialog.geometry(f"{self.DIALOG_WIDTH}x{self.DIALOG_HEIGHT}+{x}+{y}")
        
    def _create_widgets(self) -> None:
        """UIコンポーネントを作成する"""
        main_frame = ttk.Frame(self._dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === 推論モード選択 ===
        mode_frame = ttk.LabelFrame(main_frame, text="推論モード", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self._mode_var = tk.StringVar(value="cloud")
        
        cloud_radio = ttk.Radiobutton(
            mode_frame,
            text="Cloud (Groq API) - 高精度・要ネット接続",
            variable=self._mode_var,
            value="cloud",
            command=self._on_mode_change
        )
        cloud_radio.pack(anchor=tk.W)
        
        local_radio = ttk.Radiobutton(
            mode_frame,
            text="Local (LFM) - オフライン・省リソース",
            variable=self._mode_var,
            value="local",
            command=self._on_mode_change
        )
        local_radio.pack(anchor=tk.W)
        
        # === Cloud設定 ===
        self._cloud_frame = ttk.LabelFrame(main_frame, text="Cloud設定 (Groq)", padding="10")
        self._cloud_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Groq API Key
        api_key_label = ttk.Label(self._cloud_frame, text="Groq API Key:")
        api_key_label.pack(anchor=tk.W)
        
        self._api_key_var = tk.StringVar()
        self._api_key_entry = ttk.Entry(
            self._cloud_frame,
            textvariable=self._api_key_var,
            show="*",  # パスワード形式
            width=50
        )
        self._api_key_entry.pack(fill=tk.X, pady=(2, 5))
        
        # 表示/非表示トグル
        self._show_key_var = tk.BooleanVar(value=False)
        show_key_check = ttk.Checkbutton(
            self._cloud_frame,
            text="APIキーを表示",
            variable=self._show_key_var,
            command=self._toggle_key_visibility
        )
        show_key_check.pack(anchor=tk.W)
        
        # === Local設定 ===
        self._local_frame = ttk.LabelFrame(main_frame, text="Local設定 (LFM)", padding="10")
        self._local_frame.pack(fill=tk.X, pady=(0, 10))
        
        model_path_label = ttk.Label(self._local_frame, text="モデルファイル (.gguf):")
        model_path_label.pack(anchor=tk.W)
        
        path_frame = ttk.Frame(self._local_frame)
        path_frame.pack(fill=tk.X, pady=(2, 0))
        
        self._model_path_var = tk.StringVar()
        self._model_path_entry = ttk.Entry(
            path_frame,
            textvariable=self._model_path_var,
            width=35
        )
        self._model_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(
            path_frame,
            text="参照...",
            command=self._browse_model_file
        )
        browse_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # === Whisper設定 ===
        whisper_frame = ttk.LabelFrame(main_frame, text="音声認識 (Whisper)", padding="10")
        whisper_frame.pack(fill=tk.X, pady=(0, 10))
        
        whisper_label = ttk.Label(whisper_frame, text="モデルサイズ:")
        whisper_label.pack(side=tk.LEFT)
        
        self._whisper_var = tk.StringVar(value="medium")
        whisper_combo = ttk.Combobox(
            whisper_frame,
            textvariable=self._whisper_var,
            values=["tiny", "base", "small", "medium", "large-v3"],
            state="readonly",
            width=15
        )
        whisper_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # === ボタン ===
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        cancel_button = ttk.Button(
            button_frame,
            text="キャンセル",
            command=self._on_cancel
        )
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        save_button = ttk.Button(
            button_frame,
            text="保存",
            command=self._on_save_click
        )
        save_button.pack(side=tk.RIGHT)
        
        # 初期状態でモードに応じたフレームの有効/無効を設定
        self._on_mode_change()
        
    def _load_current_settings(self) -> None:
        """現在の設定をUIに反映する"""
        settings = self._config.settings
        
        self._mode_var.set(settings.inference_mode)
        self._api_key_var.set(settings.groq_api_key)
        self._model_path_var.set(settings.local_model_path)
        self._whisper_var.set(settings.whisper_model_size)
        
        # モード変更のUI更新
        self._on_mode_change()
        
    def _on_mode_change(self) -> None:
        """推論モード変更時のUI更新"""
        mode = self._mode_var.get()
        
        # Cloud設定フレームの有効/無効
        cloud_state = "normal" if mode == "cloud" else "disabled"
        for child in self._cloud_frame.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Checkbutton)):
                child.configure(state=cloud_state)
                
        # Local設定フレームの有効/無効
        local_state = "normal" if mode == "local" else "disabled"
        
        # モデルパス入力欄と参照ボタンを直接制御
        self._model_path_entry.configure(state=local_state)
        # 参照ボタンはローカル変数ではなくインスタンス変数にする必要があるが、
        # ここではウィジェットの階層から特定するか、すべてのボタンを対象にする
        for child in self._local_frame.winfo_children():
            if isinstance(child, ttk.Frame):
                # path_frame内のボタンとエントリ
                for grandchild in child.winfo_children():
                    try:
                        grandchild.configure(state=local_state)
                    except:
                        pass
    
    def _toggle_key_visibility(self) -> None:
        """APIキーの表示/非表示を切り替える"""
        if self._show_key_var.get():
            self._api_key_entry.configure(show="")
        else:
            self._api_key_entry.configure(show="*")
            
    def _browse_model_file(self) -> None:
        """モデルファイル選択ダイアログを開く"""
        file_path = filedialog.askopenfilename(
            title="GGUFモデルファイルを選択",
            filetypes=[
                ("GGUFファイル", "*.gguf"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            self._model_path_var.set(file_path)
            
    def _on_save_click(self) -> None:
        """保存ボタンクリック時の処理"""
        # 設定を更新
        settings = self._config.settings
        settings.inference_mode = self._mode_var.get()
        settings.groq_api_key = self._api_key_var.get()
        settings.local_model_path = self._model_path_var.get()
        settings.whisper_model_size = self._whisper_var.get()
        
        # 保存
        if self._config.save():
            messagebox.showinfo("設定", "設定を保存しました。\n一部の設定は再起動後に反映されます。")
            
            # コールバックを呼び出し
            if self._on_save:
                self._on_save()
                
            self._dialog.destroy()
        else:
            messagebox.showerror("エラー", "設定の保存に失敗しました。")
            
    def _on_cancel(self) -> None:
        """キャンセル時の処理"""
        self._dialog.destroy()


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    root = tk.Tk()
    root.title("テスト")
    root.geometry("200x100")
    
    def open_settings():
        SettingsDialog(root, on_save=lambda: print("Saved!"))
    
    ttk.Button(root, text="設定を開く", command=open_settings).pack(pady=20)
    
    root.mainloop()
