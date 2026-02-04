# -*- coding: utf-8 -*-
"""
コレクター - Groq APIによる超高速AIテキスト整形（自動判定版）

このモジュールは、Groqクラウドを使用して
音声認識結果を読みやすく整形する機能を提供します。
v0.4では、クリップボードの内容と比較して「修正」か「新規入力」かを自動判定します。
"""

from typing import Optional, Tuple
from groq import Groq

from src.utils.config_loader import (
    get_settings,
    get_system_prompt,
    is_api_key_configured,
)
from src.utils.memory import UserProfile, ContextManager
from src.utils.dictionary import Dictionary
from src.ai.learner import LearningEngine
from src.utils.similarity import TextSimilarity


class TextCorrector:
    """
    AIテキスト整形クラス（自動判定版）
    
    Groq APIを使用して、音声認識されたテキストを
    文法的に正しく、読みやすい形式に整形します。
    
    v0.4の追加機能:
    - UserProfile: ユーザーの文体設定を反映
    - ContextManager: 直近の会話履歴を考慮
    - LearningEngine: ユーザーの修正から学習
    - TextSimilarity: 修正か新規入力かを自動判定
    - Dictionary: 単語の誤りを辞書に登録
    
    使用例:
        corrector = TextCorrector()
        
        # 通常の整形
        result = corrector.correct("えーとこれは検性のテストです")
        
        # 自動判定（クリップボードと比較）
        result, status = corrector.correct_auto(voice_text, clipboard_text)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        コレクターを初期化する
        
        Args:
            api_key: Groq APIキー（省略時はsettings.pyから読み込み）
        """
        # 設定を読み込み
        self._settings = get_settings()
        self._api_key = api_key or self._settings.get("GROQ_API_KEY")
        self._client: Optional[Groq] = None
        
        # ベースのシステムプロンプトを取得
        self._base_system_prompt = get_system_prompt()
        
        # === 記憶モジュールの初期化 ===
        self._user_profile = UserProfile()
        self._context_manager = ContextManager()
        
        # === 辞書の初期化 ===
        self._dictionary = Dictionary()
        
        # === 学習エンジンの初期化 ===
        self._learning_engine = LearningEngine(api_key=self._api_key)
        
        # クライアントを初期化
        self._init_client()
        
    def _init_client(self) -> None:
        """Groqクライアントを初期化する"""
        if not is_api_key_configured(self._settings):
            raise ValueError(
                "Groq APIキーが設定されていません。\n"
                "settings.py の GROQ_API_KEY を設定してください。\n"
                "APIキーは https://console.groq.com で取得できます。"
            )
            
        model_name = self._settings.get("MODEL_NAME", "llama-3.3-70b-versatile")
        print(f"[Corrector] Groq API クライアント初期化中...")
        
        self._client = Groq(api_key=self._api_key)
        
        print(f"[Corrector] Groq API 準備完了 (モデル: {model_name})")
        print(f"[Corrector] 記憶モジュール: 有効")
        print(f"[Corrector] 学習エンジン: 有効")
        print(f"[Corrector] 辞書: {self._dictionary.count}件")
        print(f"[Corrector] 自動判定: 有効")
        
    def _build_system_prompt(self) -> str:
        """
        システムプロンプトを構築する
        
        ベースプロンプト + 文体指定（UserProfile）を結合
        
        Returns:
            完全なシステムプロンプト
        """
        prompt = self._base_system_prompt
        
        # 文体指定を追加
        style_instruction = self._user_profile.get_instruction()
        if style_instruction:
            prompt += "\n" + style_instruction
            
        return prompt
        
    def _build_user_prompt(self, text: str) -> str:
        """
        ユーザープロンプトを構築する
        
        入力テキスト + 文脈情報（ContextManager）を結合
        
        Args:
            text: 整形対象のテキスト
            
        Returns:
            完全なユーザープロンプト
        """
        prompt = ""
        
        # 文脈情報を追加
        context_prompt = self._context_manager.get_context_prompt(limit=5)
        if context_prompt:
            prompt += context_prompt + "\n"
            
        # 今回の入力テキスト
        prompt += f"【今回の入力】\n{text}"
        
        return prompt
        
    def correct(self, text: str) -> str:
        """
        テキストをAIで整形する（通常入力フロー）
        
        Args:
            text: 整形対象のテキスト（音声認識結果）
            
        Returns:
            整形されたテキスト
        """
        if self._client is None:
            raise RuntimeError("Groqクライアントが初期化されていません")
            
        if not text or not text.strip():
            return ""
            
        # 辞書を適用
        text = self._dictionary.apply(text)
        
        # プロンプトを構築
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(text.strip())
        
        # メッセージを構築
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 設定値を取得
        model_name = self._settings.get("MODEL_NAME", "llama-3.3-70b-versatile")
        temperature = self._settings.get("LLM_TEMPERATURE", 0.0)
        max_tokens = self._settings.get("LLM_MAX_TOKENS", 1024)
        
        try:
            # Groq APIで生成
            response = self._client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # レスポンスからテキストを抽出
            result = response.choices[0].message.content
            
            # 余分な空白や改行を整理
            result = result.strip()
            
            # === 履歴を保存 ===
            self._context_manager.add_entry(text.strip(), result)
            
            return result
            
        except Exception as e:
            print(f"[Corrector] 整形エラー: {e}")
            # エラー時は元のテキストをそのまま返す
            return text.strip()
            
    def learn_from_correction(self, original_text: str, corrected_text: str) -> str:
        """
        ユーザーの修正から学習する
        
        Args:
            original_text: AIが出力したテキスト（修正前）
            corrected_text: ユーザーが修正したテキスト（修正後）
            
        Returns:
            学習結果のレポートメッセージ
        """
        return self._learning_engine.learn(
            original_text=original_text,
            corrected_text=corrected_text,
            profile=self._user_profile,
            dictionary=self._dictionary
        )
        
    def correct_auto(self, voice_text: str, clipboard_text: str) -> Tuple[str, str]:
        """
        自動判定フロー: クリップボードの内容と比較して処理を分岐
        
        判定ロジック:
        - 類似度 0.3〜0.95 → 修正として学習
        - それ以外 → 新規入力として整形
        
        Args:
            voice_text: 音声認識結果
            clipboard_text: クリップボードの内容
            
        Returns:
            (確定テキスト, ステータスメッセージ) のタプル
        """
        # クリップボードが空、または入力が短い場合は通常処理
        if not clipboard_text or len(voice_text) < 2:
            return self.correct(voice_text), "通常入力"
            
        # 類似度で判定
        if TextSimilarity.is_correction(clipboard_text, voice_text):
            # 修正として学習
            print("[Corrector] 修正検知 -> 学習開始")
            report = self.learn_from_correction(clipboard_text, voice_text)
            return voice_text, f"学習完了: {report}"
        else:
            # 新規入力として整形
            print("[Corrector] 新規入力判定")
            return self.correct(voice_text), "通常入力"
    
    def get_model_info(self) -> dict:
        """
        現在のモデル情報を返す
        
        Returns:
            モデル情報の辞書
        """
        return {
            "model_name": self._settings.get("MODEL_NAME"),
            "provider": "Groq",
            "initialized": self._client is not None,
            "context_count": self._context_manager.count,
            "dictionary_count": self._dictionary.count,
            "learning_enabled": True,
            "auto_detect_enabled": True,
        }
        
    def clear_context(self) -> None:
        """会話履歴をクリアする"""
        self._context_manager.clear()
    
    def dispose(self) -> None:
        """リソースを解放する"""
        self._client = None
        self._learning_engine.dispose()
        print("[Corrector] リソース解放完了")


# ============================================
# モジュールテスト
# ============================================

if __name__ == "__main__":
    import time
    
    print("=== TextCorrector (自動判定版) テスト ===")
    print()
    
    # APIキーチェック
    if not is_api_key_configured():
        print(f"エラー: Groq APIキーが設定されていません")
        print(f"settings.py の GROQ_API_KEY を設定してください")
        exit(1)
    
    # クライアント初期化
    corrector = TextCorrector()
    print()
    
    # テスト1: 通常入力（クリップボード空）
    print("--- テスト1: 通常入力 ---")
    voice = "えーとこれは検性のテストです"
    result, status = corrector.correct_auto(voice, "")
    print(f"音声: {voice}")
    print(f"結果: {result}")
    print(f"ステータス: {status}")
    print()
    
    # テスト2: 修正検知
    print("--- テスト2: 修正検知 ---")
    clipboard = "これは賢声のテストです。"
    voice = "これは賢声のテストだよ"
    result, status = corrector.correct_auto(voice, clipboard)
    print(f"クリップ: {clipboard}")
    print(f"音声: {voice}")
    print(f"結果: {result}")
    print(f"ステータス: {status}")
    print()
    
    corrector.dispose()
    print("テスト終了")
