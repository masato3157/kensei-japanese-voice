# -*- coding: utf-8 -*-
"""
辞書管理 - 単語の置換辞書を管理

このモジュールは、音声認識の誤りを修正するための
辞書機能を提供します。
"""

import json
from pathlib import Path
from typing import Dict, Optional


# 辞書ファイルのパス
DICTIONARY_PATH = Path(__file__).parent.parent / "data" / "dictionary.json"


class Dictionary:
    """
    単語置換辞書を管理するクラス
    
    責務:
    - dictionary.jsonの読み書き
    - テキストへの辞書適用
    - 新しい単語ペアの追加
    
    使用例:
        dictionary = Dictionary()
        text = dictionary.apply("けんせい")  # "賢声" に変換
        dictionary.add_word("よつう", "腰痛")  # 新規登録
    """
    
    def __init__(self, path: Optional[Path] = None):
        """
        辞書を初期化する
        
        Args:
            path: 辞書ファイルのパス（省略時はデフォルトパス）
        """
        self._path = path or DICTIONARY_PATH
        self._entries: Dict[str, str] = {}
        self._load()
        
    def _load(self) -> None:
        """辞書ファイルを読み込む"""
        if not self._path.exists():
            print(f"[Dictionary] 警告: 辞書ファイルが見つかりません: {self._path}")
            self._entries = {}
            return
            
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if isinstance(data, dict):
                self._entries = data
                print(f"[Dictionary] 読み込み完了: {len(self._entries)}件")
            else:
                print(f"[Dictionary] 警告: 辞書形式が不正です")
                self._entries = {}
                
        except json.JSONDecodeError as e:
            print(f"[Dictionary] エラー: JSON解析失敗: {e}")
            self._entries = {}
        except IOError as e:
            print(f"[Dictionary] エラー: 読み込み失敗: {e}")
            self._entries = {}
            
    def _save(self) -> bool:
        """
        辞書ファイルに保存する
        
        Returns:
            保存成功時True
        """
        try:
            # ディレクトリがなければ作成
            self._path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, indent=2, ensure_ascii=False)
                
            print(f"[Dictionary] 保存完了: {len(self._entries)}件")
            return True
            
        except IOError as e:
            print(f"[Dictionary] エラー: 保存失敗: {e}")
            return False
            
    def apply(self, text: str) -> str:
        """
        テキストに辞書を適用する
        
        Args:
            text: 置換対象のテキスト
            
        Returns:
            辞書適用後のテキスト
        """
        result = text
        for wrong, correct in self._entries.items():
            result = result.replace(wrong, correct)
        return result
        
    def add_word(self, wrong: str, correct: str) -> bool:
        """
        新しい単語ペアを登録する
        
        Args:
            wrong: 誤った単語（認識誤り）
            correct: 正しい単語
            
        Returns:
            新規登録成功時True、既存の場合はFalse
        """
        # 空文字チェック
        if not wrong or not correct:
            print(f"[Dictionary] 警告: 空の単語は登録できません")
            return False
            
        # 既に同じペアが存在する場合
        if wrong in self._entries and self._entries[wrong] == correct:
            print(f"[Dictionary] スキップ: 既に登録済み ({wrong} -> {correct})")
            return False
            
        # 登録して保存
        self._entries[wrong] = correct
        if self._save():
            print(f"[Dictionary] 登録完了: {wrong} -> {correct}")
            return True
        else:
            # 保存失敗時はメモリからも削除
            del self._entries[wrong]
            return False
            
    def remove_word(self, wrong: str) -> bool:
        """
        単語ペアを削除する
        
        Args:
            wrong: 削除対象の誤り単語
            
        Returns:
            削除成功時True
        """
        if wrong not in self._entries:
            print(f"[Dictionary] 警告: 登録されていません ({wrong})")
            return False
            
        del self._entries[wrong]
        return self._save()
        
    def get_entries(self) -> Dict[str, str]:
        """現在の辞書エントリを取得する"""
        return self._entries.copy()
        
    @property
    def count(self) -> int:
        """登録件数を取得する"""
        return len(self._entries)


# ============================================
# モジュールテスト
# ============================================

if __name__ == "__main__":
    print("=== Dictionary テスト ===")
    print()
    
    dictionary = Dictionary()
    print(f"現在の登録件数: {dictionary.count}")
    print(f"現在のエントリ: {dictionary.get_entries()}")
    print()
    
    # 適用テスト
    test_text = "けんせいは音声入力ツールです"
    result = dictionary.apply(test_text)
    print(f"適用前: {test_text}")
    print(f"適用後: {result}")
    print()
    
    print("テスト終了")
