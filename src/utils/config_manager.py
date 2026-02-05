# -*- coding: utf-8 -*-
"""
設定マネージャー - アプリケーション設定の永続化

このモジュールは、アプリケーションの設定をJSONファイルとして
保存・読み込みする機能を提供します。

エンジン切り替え（Cloud/Local）や、モデルパスなどの
ユーザー設定を管理します。
"""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict


# 設定ファイルのデフォルトパス
CONFIG_FILE_NAME = "config.json"
CONFIG_DIR = Path(__file__).parent.parent.parent  # プロジェクトルート


@dataclass
class AppConfig:
    """
    アプリケーション設定を管理するデータクラス
    
    Attributes:
        inference_mode: 推論モード ("cloud" = Groq, "local" = LFM)
        groq_api_key: Groq APIキー
        groq_model_id: Groqで使用するモデルID
        local_model_path: ローカルLLMモデルのパス (.gguf)
        whisper_model_size: Whisperモデルサイズ
    """
    # 推論モード: "cloud" (Groq) または "local" (LFM)
    inference_mode: str = "cloud"
    
    # Groq API設定
    groq_api_key: str = ""
    groq_model_id: str = "llama-3.3-70b-versatile"
    
    # ローカルLLM設定
    local_model_path: str = ""
    
    # Whisper設定
    whisper_model_size: str = "medium"


class ConfigManager:
    """
    設定の読み書きを管理するクラス
    
    JSONファイルを使用して設定を永続化します。
    シングルトンパターンで実装し、アプリ全体で同じインスタンスを共有します。
    
    使用例:
        # 設定の読み込み
        config = ConfigManager.get_instance()
        print(config.settings.inference_mode)
        
        # 設定の変更と保存
        config.settings.inference_mode = "local"
        config.save()
    """
    
    _instance: Optional["ConfigManager"] = None
    
    @classmethod
    def get_instance(cls) -> "ConfigManager":
        """シングルトンインスタンスを取得する"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        ConfigManagerを初期化する
        
        Args:
            config_path: 設定ファイルのパス（省略時はデフォルト）
        """
        self._config_path = config_path or (CONFIG_DIR / CONFIG_FILE_NAME)
        self._settings = AppConfig()
        
        # 設定ファイルが存在すれば読み込む
        self.load()
        
    @property
    def settings(self) -> AppConfig:
        """現在の設定を取得する"""
        return self._settings
    
    @property
    def config_path(self) -> Path:
        """設定ファイルのパスを取得する"""
        return self._config_path
    
    def load(self) -> bool:
        """
        設定ファイルを読み込む
        
        Returns:
            読み込みに成功した場合はTrue
        """
        if not self._config_path.exists():
            print(f"[ConfigManager] 設定ファイルが見つかりません。デフォルト設定を使用します。")
            return False
            
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # 読み込んだデータで設定を更新（存在するキーのみ）
            for key, value in data.items():
                if hasattr(self._settings, key):
                    setattr(self._settings, key, value)
                    
            print(f"[ConfigManager] 設定読み込み完了: {self._config_path}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"[ConfigManager] 設定ファイルの解析エラー: {e}")
            return False
        except Exception as e:
            print(f"[ConfigManager] 設定読み込みエラー: {e}")
            return False
    
    def save(self) -> bool:
        """
        設定ファイルに保存する
        
        Returns:
            保存に成功した場合はTrue
        """
        try:
            # ディレクトリが存在しない場合は作成
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # データクラスを辞書に変換して保存
            data = asdict(self._settings)
            
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"[ConfigManager] 設定保存完了: {self._config_path}")
            return True
            
        except Exception as e:
            print(f"[ConfigManager] 設定保存エラー: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """設定をデフォルトに戻す"""
        self._settings = AppConfig()
        print("[ConfigManager] 設定をデフォルトにリセットしました")
    
    def is_cloud_mode(self) -> bool:
        """クラウドモード（Groq）かどうかを返す"""
        return self._settings.inference_mode == "cloud"
    
    def is_local_mode(self) -> bool:
        """ローカルモード（LFM）かどうかを返す"""
        return self._settings.inference_mode == "local"
    
    def is_groq_configured(self) -> bool:
        """Groq APIキーが設定されているかを返す"""
        key = self._settings.groq_api_key
        return key and len(key) > 10 and key != "YOUR_API_KEY_HERE"
    
    def is_local_model_configured(self) -> bool:
        """ローカルモデルが設定されているかを返す"""
        path = self._settings.local_model_path
        return path and Path(path).exists()


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    print("=== ConfigManager テスト ===")
    
    # インスタンス取得
    config = ConfigManager.get_instance()
    
    print(f"\n設定ファイル: {config.config_path}")
    print(f"推論モード: {config.settings.inference_mode}")
    print(f"Groqモデル: {config.settings.groq_model_id}")
    print(f"Whisperサイズ: {config.settings.whisper_model_size}")
    print(f"クラウドモード: {config.is_cloud_mode()}")
    print(f"Groq設定済み: {config.is_groq_configured()}")
    
    # 保存テスト
    config.save()
    print("\nテスト終了")
