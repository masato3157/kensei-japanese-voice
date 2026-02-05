# -*- coding: utf-8 -*-
"""
類似度計算 - テキストの類似度を算出

このモジュールは、2つのテキスト間の類似度を計算し、
「修正」か「新規入力」かを自動判定する機能を提供します。
"""

import difflib
import logging

# モジュール用のロガーを設定
logger = logging.getLogger(__name__)


class TextSimilarity:
    """
    テキスト類似度を計算するユーティリティクラス
    
    責務:
    - 2つのテキスト間の類似度を算出
    - 修正か新規入力かを判定
    
    使用例:
        score = TextSimilarity.calculate("こんにちは", "こんばんは")
        is_corr = TextSimilarity.is_correction("これはテスト", "これはテストです")
    """
    
    @staticmethod
    def calculate(text1: str, text2: str) -> float:
        """
        2つのテキストの類似度を算出する
        
        Args:
            text1: 比較元テキスト
            text2: 比較先テキスト
            
        Returns:
            類似度スコア (0.0 - 1.0)
        """
        if not text1 or not text2:
            return 0.0
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    @staticmethod
    def is_correction(original: str, new_input: str) -> bool:
        """
        修正指示かどうかを判定する
        
        判定基準:
        - 類似度が 0.3以上 0.95未満 = 修正（似ているが、少し違う）
        - 0.3未満 = まったく別の新規入力
        - 0.95以上 = ほぼ同じ（修正なし）
        
        Args:
            original: 元のテキスト（クリップボードの内容）
            new_input: 新しい入力（音声認識結果）
            
        Returns:
            修正と判定された場合True
        """
        sim = TextSimilarity.calculate(original, new_input)
        logger.debug(f"[Similarity] Score: {sim:.2f}")
        return 0.3 <= sim < 0.95


# ============================================
# モジュールテスト
# ============================================

if __name__ == "__main__":
    print("=== TextSimilarity テスト ===")
    print()
    
    # テストケース
    test_cases = [
        ("こんにちは", "こんにちは"),           # 完全一致
        ("これはテスト", "これはテストです"),   # 軽微な修正
        ("おはようございます", "こんばんは"),   # まったく別
        ("今日は天気が良いですね", "今日は天気がいいね"),  # 表現変更
    ]
    
    for text1, text2 in test_cases:
        score = TextSimilarity.calculate(text1, text2)
        is_corr = TextSimilarity.is_correction(text1, text2)
        print(f"「{text1}」 vs 「{text2}」")
        print(f"  類似度: {score:.2f}, 修正判定: {is_corr}")
        print()
