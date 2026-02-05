# -*- coding: utf-8 -*-
"""
ハイブリッド・コレクター - Cloud/Local併用型AIテキスト整形

このモジュールは、設定に応じてGroq（クラウド）またはLFM（ローカルLLM）を
切り替えて使用するテキスト整形機能を提供します。
"""

import os
from typing import Optional
from pathlib import Path

# ConfigManager
from src.utils.config_manager import ConfigManager

# Cloud: Groq
try:
    from groq import Groq
    _HAS_GROQ = True
except ImportError:
    _HAS_GROQ = False

# Local: llama-cpp-python
try:
    from llama_cpp import Llama
    _HAS_LLAMA = True
except ImportError:
    _HAS_LLAMA = False


class HybridCorrector:
    """
    ハイブリッドAIテキスト整形クラス
    
    設定（ConfigManager）に基づいて、以下のいずれかのエンジンを使用します：
    1. Cloud Mode: Groq API (Llama 3 70B等) - 高精度、高速、ネット必須
    2. Local Mode: LFM (Llama 3 8B等) - オフライン、PCリソース使用
    
    使用例:
        corrector = HybridCorrector()
        result = corrector.correct("認識されたテキスト")
    """
    
    def __init__(self):
        """コレクターを初期化する"""
        self._config = ConfigManager.get_instance()
        self._groq_client: Optional['Groq'] = None
        self._local_model: Optional['Llama'] = None
        self._last_mode: Optional[str] = None
        
        # 初期化（設定に基づいてエンジンをロード）
        self._reload_engine()
        
    def _reload_engine(self) -> None:
        """設定に基づいてエンジンを再読み込みする"""
        settings = self._config.settings
        current_mode = settings.inference_mode
        
        # モードが変わっていなければ何もしない（初回はNoneなので実行される）
        if self._last_mode == current_mode and (self._groq_client or self._local_model):
            return
            
        print(f"[HybridCorrector] エンジン切り替え: {current_mode}")
        
        # リソース解放
        self._groq_client = None
        if self._local_model:
            del self._local_model
            self._local_model = None
            
        if current_mode == "cloud":
            self._init_cloud_engine()
        elif current_mode == "local":
            self._init_local_engine()
            
        self._last_mode = current_mode
        
    def _init_cloud_engine(self) -> None:
        """Cloudエンジン (Groq) を初期化"""
        if not _HAS_GROQ:
            print("[HybridCorrector] エラー: groqライブラリがインストールされていません")
            return
            
        api_key = self._config.settings.groq_api_key
        if not api_key or len(api_key) < 10:
            print("[HybridCorrector] 警告: Groq APIキーが設定されていません")
            return
            
        try:
            self._groq_client = Groq(api_key=api_key)
            print(f"[HybridCorrector] Groqクライアント初期化完了 (モデル: {self._config.settings.groq_model_id})")
        except Exception as e:
            print(f"[HybridCorrector] Groq初期化エラー: {e}")
            
    def _init_local_engine(self) -> None:
        """Localエンジン (LFM/llama-cpp) を初期化"""
        print("[HybridCorrector] Localエンジン初期化開始...")
        
        if not _HAS_LLAMA:
            print("[HybridCorrector] エラー: llama-cpp-pythonライブラリがインストールされていません")
            return
            
        # パスを取得し、文字列として確実に処理
        raw_path = self._config.settings.local_model_path
        print(f"[HybridCorrector] 設定パス: '{raw_path}'")
        
        if not raw_path:
            print(f"[HybridCorrector] 警告: ローカルモデルパスが空です")
            return
            
        # パスオブジェクトを作成して存在確認
        try:
            model_path_obj = Path(raw_path)
            if not model_path_obj.exists():
                print(f"[HybridCorrector] 警告: モデルファイルが見つかりません (絶対パス): {model_path_obj.absolute()}")
                return
            
            # llama-cpp-pythonのmodel_pathは文字列で渡す必要がある
            model_path_str = str(model_path_obj.resolve())
            print(f"[HybridCorrector] ローカルモデル読み込み開始: {model_path_str}")
            
            try:
                # まずGPUオフロードを試みる
                print("[HybridCorrector] GPUモードで読み込み中...")
                self._local_model = Llama(
                    model_path=model_path_str,
                    n_gpu_layers=-1,
                    n_ctx=2048,
                    verbose=False
                )
                print("[HybridCorrector] ローカルモデル読み込み完了 (GPU)")
                
            except Exception as e_gpu:
                print(f"[HybridCorrector] GPUロード失敗: {e_gpu}")
                print("[HybridCorrector] CPUモードで再試行します...")
                
                # 失敗したらCPUモードで再試行
                try:
                    self._local_model = Llama(
                        model_path=model_path_str,
                        n_gpu_layers=0,  # GPUオフロードなし
                        n_ctx=2048,
                        verbose=False
                    )
                    print("[HybridCorrector] ローカルモデル読み込み完了 (CPU)")
                except Exception as e_cpu:
                    print(f"[HybridCorrector] CPUロードも失敗しました: {e_cpu}")
                    raise e_cpu  # 元のエラーハンドラへ
            
        except Exception as e:
            print(f"[HybridCorrector] ローカルモデル初期化エラーの詳細: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self._local_model = None
            
    def correct(self, text: str) -> str:
        """
        テキストを整形する
        
        Args:
            text: 入力テキスト（音声認識結果）
            
        Returns:
            整形後のテキスト
        """
        if not text:
            return ""
            
        # 設定が変更されていないか確認し、必要ならリロード
        if self._config.settings.inference_mode != self._last_mode:
            print(f"[HybridCorrector] モード変更検知: {self._last_mode} -> {self._config.settings.inference_mode}")
            self._reload_engine()
            
        mode = self._config.settings.inference_mode
        
        # Localモードかつモデル未ロードの場合、再試行
        if mode == "local" and self._local_model is None:
            print("[HybridCorrector] Localモデル未ロードのため再読み込みを試行...")
            self._init_local_engine()
        
        if mode == "cloud":
            return self._correct_cloud(text)
        elif mode == "local":
            return self._correct_local(text)
        else:
            return text
            
    def _correct_cloud(self, text: str) -> str:
        """Groq APIを使用して整形"""
        if not self._groq_client:
            return "[エラー] Groq APIキーを設定してください"
            
        system_prompt = (
            "あなたは優秀な編集者です。ユーザーの音声認識テキストを、意味を変えずに読みやすく整えてください。"
            "余計な返事はせず、修正後のテキストのみを出力してください。"
        )
        
        try:
            response = self._groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                model=self._config.settings.groq_model_id,
                temperature=0.0,
                max_tokens=1024,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[HybridCorrector] Groq推論エラー: {e}")
            return f"[エラー] Cloud推論失敗: {str(e)[:50]}..."
            
    def _correct_local(self, text: str) -> str:
        """ローカルLLMを使用して整形"""
        if not self._local_model:
            return "[エラー] ローカルモデルファイルを設定してください"
            
        # Gemma 2 向けのプロンプト形式 (<start_of_turn>user ... <end_of_turn>)
        # 返答や解説を抑制し、修正のみを行うように強く指示
        prompt = f"""<start_of_turn>user
あなたは優秀な校正AIです。以下のテキストは音声認識の結果です。
文脈を読み取り、誤字脱字を修正して自然な日本語に書き換えてください。
決して挨拶や解説は行わず、修正後のテキストのみを出力してください。

入力: {text}<end_of_turn>
<start_of_turn>model
"""
        
        try:
            output = self._local_model(
                prompt,
                max_tokens=1024,
                stop=["<end_of_turn>", "<eos>"],
                temperature=0.1,
                echo=False
            )
            result = output['choices'][0]['text'].strip()
            return result
        except Exception as e:
            print(f"[HybridCorrector] Local推論エラー: {e}")
            return f"[エラー] Local推論失敗: {str(e)[:50]}..."

    def dispose(self) -> None:
        """リソースを解放する"""
        self._groq_client = None
        if self._local_model:
            del self._local_model
            self._local_model = None
