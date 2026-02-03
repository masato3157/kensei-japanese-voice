# -*- coding: utf-8 -*-
"""
コレクター - Groq APIによる超高速AIテキスト整形

このモジュールは、Groqクラウドを使用して
音声認識結果を読みやすく整形する機能を提供します。
Groqは超低レイテンシ（数百ミリ秒）で応答します。
"""

from typing import Optional
from groq import Groq

from src.utils.config_loader import (
    get_settings,
    get_system_prompt,
    is_api_key_configured,
)


class TextCorrector:
    """
    AIテキスト整形クラス（Groq版）
    
    Groq APIを使用して、音声認識されたテキストを
    文法的に正しく、読みやすい形式に整形します。
    
    使用例:
        corrector = TextCorrector()
        corrected = corrector.correct("えーとこれは検性のテストです")
        print(corrected)  # "これは賢声のテストです。"
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
        
        # システムプロンプトを取得
        self._system_prompt = get_system_prompt()
        
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
        
    def correct(self, text: str) -> str:
        """
        テキストをAIで整形する
        
        Args:
            text: 整形対象のテキスト（音声認識結果）
            
        Returns:
            整形されたテキスト
        """
        if self._client is None:
            raise RuntimeError("Groqクライアントが初期化されていません")
            
        if not text or not text.strip():
            return ""
        
        # メッセージを構築
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": text.strip()}
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
            
            return result
            
        except Exception as e:
            print(f"[Corrector] 整形エラー: {e}")
            # エラー時は元のテキストをそのまま返す
            return text.strip()
    
    def get_model_info(self) -> dict:
        """
        現在のモデル情報を返す
        
        Returns:
            モデル情報の辞書
        """
        return {
            "model_name": self._settings.get("MODEL_NAME"),
            "provider": "Groq",
            "initialized": self._client is not None
        }
    
    def dispose(self) -> None:
        """リソースを解放する"""
        self._client = None
        print("[Corrector] リソース解放完了")


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    import time
    
    print("=== TextCorrector (Groq版) テスト ===")
    print()
    
    # APIキーチェック
    if not is_api_key_configured():
        print(f"エラー: Groq APIキーが設定されていません")
        print(f"settings.py の GROQ_API_KEY を設定してください")
        exit(1)
    
    # クライアント初期化
    start_time = time.time()
    corrector = TextCorrector()
    init_time = time.time() - start_time
    print(f"初期化時間: {init_time:.2f} 秒")
    print()
    
    # テストケース
    test_cases = [
        "えーとこれは検性のテストですあのちゃんと動くかな",
        "今日はいい天気だねー散歩行きたい",
        "まあ、今の段階としてはいいかな",
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"--- テスト {i} ---")
        print(f"入力: {test_text}")
        
        start_time = time.time()
        result = corrector.correct(test_text)
        elapsed = time.time() - start_time
        
        print(f"出力: {result}")
        print(f"処理時間: {elapsed:.2f} 秒")
        print()
    
    corrector.dispose()
    print("テスト終了")
