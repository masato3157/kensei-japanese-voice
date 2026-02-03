# -*- coding: utf-8 -*-
"""
コレクター - llama.cppによるAIテキスト整形

このモジュールは、ローカルLLM（llama.cpp）を使用して
音声認識結果を読みやすく整形する機能を提供します。
"""

from typing import Optional
from llama_cpp import Llama

from src.utils import config


class TextCorrector:
    """
    AIテキスト整形クラス
    
    llama.cppを使用して、音声認識されたテキストを
    文法的に正しく、読みやすい形式に整形します。
    
    使用例:
        corrector = TextCorrector()
        corrected = corrector.correct("えーとこれは検性のテストです")
        print(corrected)  # "これは賢声のテストです。"
    """
    
    def __init__(
        self,
        model_path: str = config.MODEL_PATH,
        n_ctx: int = config.LLM_CONTEXT_SIZE,
        verbose: bool = False
    ):
        """
        コレクターを初期化する
        
        Args:
            model_path: GGUFモデルファイルのパス
            n_ctx: コンテキストサイズ（トークン数）
            verbose: 詳細ログを出力するか
        """
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._verbose = verbose
        self._llm: Optional[Llama] = None
        
        # モデルを読み込む
        self._load_model()
        
    def _load_model(self) -> None:
        """LLMモデルを読み込む"""
        if not config.model_exists():
            raise FileNotFoundError(
                f"モデルファイルが見つかりません: {self._model_path}\n"
                f"models/ フォルダにGGUFファイルを配置してください。"
            )
            
        print(f"[Corrector] モデル読み込み中: {self._model_path}...")
        
        self._llm = Llama(
            model_path=self._model_path,
            n_ctx=self._n_ctx,
            verbose=self._verbose,
            n_threads=4,  # CPUスレッド数
        )
        
        print(f"[Corrector] モデル読み込み完了")
        
    def correct(self, text: str) -> str:
        """
        テキストをAIで整形する
        
        Args:
            text: 整形対象のテキスト（音声認識結果）
            
        Returns:
            整形されたテキスト
        """
        if self._llm is None:
            raise RuntimeError("モデルが読み込まれていません")
            
        if not text or not text.strip():
            return ""
            
        # Chat形式のプロンプトを構築
        messages = [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": text.strip()}
        ]
        
        try:
            # LLMで生成
            response = self._llm.create_chat_completion(
                messages=messages,
                max_tokens=None,  # 無制限（入力に応じて自動調整）
                temperature=config.LLM_TEMPERATURE,
                top_p=config.LLM_TOP_P,
                repeat_penalty=config.LLM_REPEAT_PENALTY,
                stop=["<|eot_id|>", "<|end_of_text|>"],  # Llama3の終了トークン
            )
            
            # レスポンスからテキストを抽出
            result = response["choices"][0]["message"]["content"]
            
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
            "model_path": self._model_path,
            "n_ctx": self._n_ctx,
            "loaded": self._llm is not None
        }
    
    def dispose(self) -> None:
        """リソースを解放する"""
        if self._llm is not None:
            del self._llm
            self._llm = None
            print("[Corrector] リソース解放完了")


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    import time
    
    print("=== TextCorrector テスト ===")
    print()
    
    # モデル存在チェック
    if not config.model_exists():
        print(f"エラー: モデルファイルが見つかりません")
        print(f"パス: {config.MODEL_PATH}")
        print()
        print("以下からダウンロードしてください:")
        print("https://huggingface.co/elyza/Llama-3-ELYZA-JP-8B-GGUF")
        exit(1)
    
    # モデル読み込み
    start_time = time.time()
    corrector = TextCorrector()
    load_time = time.time() - start_time
    print(f"モデル読み込み時間: {load_time:.2f} 秒")
    print()
    
    # テストケース
    test_cases = [
        "えーとこれは検性のテストですあのちゃんと動くかな",
        "今日はいい天気ですねえー散歩に行きたいです",
        "あのーこのプロジェクトはえーとPythonで書かれています",
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
