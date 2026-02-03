# -*- coding: utf-8 -*-
"""
賢声 (Kensei) - 常駐型音声入力アプリ

エントリーポイント

このファイルはアプリケーションの起動点です。
メインウィンドウを初期化し、イベントループを開始します。
"""

import sys
import os

# srcディレクトリをパスに追加（相対インポートを可能にする）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_window import create_main_window


def main():
    """
    アプリケーションのメイン関数
    
    処理フロー:
    1. メインウィンドウを作成
    2. 初期ログを表示
    3. イベントループを開始
    """
    # メインウィンドウを作成
    window = create_main_window()
    
    # 起動メッセージを表示
    window.add_log("[システム] 賢声を起動しました")
    window.add_log("[ヒント] 左Ctrlキーで音声入力を開始できます")
    window.add_log("[ヒント] 右Ctrlキーで修正指示モードに切り替わります")
    
    # メインループを開始
    window.run()


if __name__ == "__main__":
    main()
