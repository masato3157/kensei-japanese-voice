"""
賢声 (Kensei) - ユーザー表示用ミニウィンドウ

目的：
    音声認識の結果をリアルタイムでユーザーに表示する。
    ユーザーが入力中の文書を遮らないよう、コンパクトなサイズで
    常に最前面に表示される。

使用方法：
    from src.ui.display_window import DisplayWindow
    
    # MainWindow の root を渡して初期化
    window = DisplayWindow(parent_root)
    window.update_text("認識されたテキスト")
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Optional


class DisplayWindow:
    """
    音声認識結果を表示するミニウィンドウ。
    
    Toplevel ウィンドウとして作成され、親ウィンドウと同じ
    Tkinter イベントループを共有する。
    常に最前面に表示され、ユーザーが音声入力の内容を
    リアルタイムで確認できる。
    """
    
    # ウィンドウのデフォルトサイズ
    DEFAULT_WIDTH = 600
    DEFAULT_HEIGHT = 120
    
    # 表示設定
    FONT_FAMILY = "Yu Gothic UI"  # Windows向けゴシックフォント
    FONT_SIZE = 14
    BG_COLOR = "#FFFFFF"  # 背景色（白）
    FG_COLOR = "#1A1A1A"  # 文字色（黒に近いグレー）
    PADDING = 8  # 内側の余白
    
    def __init__(self, parent: Optional[tk.Tk] = None):
        """
        ウィンドウを初期化する。
        
        Args:
            parent: 親となる Tk ルートウィンドウ。
                    Noneの場合は単体テスト用に新規作成する。
        """
        # 親ウィンドウがない場合は単体テスト用に作成
        if parent is None:
            self._parent = tk.Tk()
            self._parent.withdraw()  # 親ウィンドウは非表示
            self._owns_parent = True
        else:
            self._parent = parent
            self._owns_parent = False
        
        # Toplevel として作成（親と同じイベントループを共有）
        self._window = tk.Toplevel(self._parent)
        self._setup_window()
        self._create_widgets()
    
    def _setup_window(self):
        """
        ウィンドウの基本設定を行う。
        """
        # タイトルとサイズ
        self._window.title("賢声 - Kensei")
        self._window.geometry(
            f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}"
        )
        
        # リサイズを許可
        self._window.resizable(True, True)
        
        # 最小サイズを設定（小さすぎると読めないため）
        self._window.minsize(300, 60)
        
        # 常に最前面に表示
        self._window.attributes("-topmost", True)
        
        # 背景色
        self._window.configure(bg=self.BG_COLOR)
        
        # ×ボタンで閉じる際の処理（親ウィンドウは閉じない）
        self._window.protocol("WM_DELETE_WINDOW", self._on_close_button)
    
    def _on_close_button(self):
        """
        ×ボタンが押された時の処理。
        
        ミニウィンドウだけを隠す（親ウィンドウは閉じない）。
        """
        self._window.withdraw()
    
    def _create_widgets(self):
        """
        テキスト表示エリアを作成する。
        """
        # フォント設定
        text_font = tkfont.Font(
            family=self.FONT_FAMILY,
            size=self.FONT_SIZE
        )
        
        # テキストウィジェット（複数行表示・自動折り返し対応）
        self._text_widget = tk.Text(
            self._window,
            font=text_font,
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            wrap=tk.WORD,  # 単語単位で折り返し
            padx=self.PADDING,
            pady=self.PADDING,
            relief=tk.FLAT,  # 枠線なし（シンプルな見た目）
            cursor="arrow",  # カーソルを矢印に（編集不可を示唆）
            state=tk.DISABLED  # 編集不可
        )
        
        # ウィンドウ全体に広げる
        self._text_widget.pack(fill=tk.BOTH, expand=True)
    
    def update_text(self, text: str):
        """
        表示テキストを更新する。
        
        常に最新の内容（末尾）が見えるように自動スクロールする。
        
        Args:
            text: 表示するテキスト
        """
        # ウィンドウが隠れていたら表示
        if not self._window.winfo_viewable():
            self._window.deiconify()
        
        # 編集可能にしてから更新
        self._text_widget.config(state=tk.NORMAL)
        
        # 既存のテキストをクリア
        self._text_widget.delete("1.0", tk.END)
        
        # 新しいテキストを挿入
        self._text_widget.insert(tk.END, text)
        
        # 末尾にスクロール（最新の内容を表示）
        self._text_widget.see(tk.END)
        
        # 再び編集不可に
        self._text_widget.config(state=tk.DISABLED)
    
    def show(self):
        """
        ウィンドウを表示する。
        """
        self._window.deiconify()
    
    def hide(self):
        """
        ウィンドウを非表示にする。
        """
        self._window.withdraw()
    
    def close(self):
        """
        ウィンドウを完全に閉じる。
        """
        try:
            self._window.destroy()
        except tk.TclError:
            pass  # 既に破棄されている場合は無視
        
        # 単体テスト用に親を作成した場合は親も閉じる
        if self._owns_parent:
            try:
                self._parent.destroy()
            except tk.TclError:
                pass
    
    @property
    def root(self) -> tk.Toplevel:
        """
        Toplevel ウィンドウを返す。
        
        外部からウィンドウを制御する場合に使用。
        """
        return self._window


# 単体テスト用
if __name__ == "__main__":
    # 単体テスト用に親なしで作成
    window = DisplayWindow()
    
    # テスト用のサンプルテキスト
    sample_texts = [
        "こんにちは、賢声です。",
        "こんにちは、賢声です。音声認識のテストを行っています。",
        "こんにちは、賢声です。音声認識のテストを行っています。"
        "このウィンドウには、あなたの声がリアルタイムで文字に変換されて表示されます。",
    ]
    
    current_index = 0
    
    def update_sample():
        """サンプルテキストを順番に表示する。"""
        global current_index
        window.update_text(sample_texts[current_index])
        current_index = (current_index + 1) % len(sample_texts)
        # 2秒後に再度呼び出し
        window.root.after(2000, update_sample)
    
    # 初回表示
    update_sample()
    
    # メインループ開始
    print("ミニウィンドウを表示中... 閉じるにはウィンドウの×ボタンを押してください。")
    window._parent.mainloop()
