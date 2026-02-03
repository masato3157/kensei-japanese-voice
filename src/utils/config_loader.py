# -*- coding: utf-8 -*-
"""
設定ローダー - 設定の読み込みとプロンプト生成

このモジュールは、設定ファイル（settings.py）と辞書ファイル（dictionary.json）を
安全に読み込み、システムプロンプトを構築する機能を提供します。
実行ディレクトリに依存せず、どこからでも正しく動作します。
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

# ============================================
# パス解決
# ============================================

def get_project_root() -> Path:
    """
    プロジェクトルートディレクトリを取得する
    
    このファイルは src/utils/config_loader.py にあるため、
    2階層上がプロジェクトルートになる。
    
    Returns:
        プロジェクトルートのPathオブジェクト
    """
    return Path(__file__).parent.parent.parent.resolve()


def get_settings_path() -> Path:
    """settings.py のパスを取得する"""
    return get_project_root() / "settings.py"


def get_dictionary_path() -> Path:
    """dictionary.json のパスを取得する"""
    return get_project_root() / "src" / "data" / "dictionary.json"


# ============================================
# デフォルト値
# ============================================

DEFAULT_SETTINGS = {
    "GROQ_API_KEY": "YOUR_API_KEY_HERE",
    "MODEL_NAME": "llama-3.3-70b-versatile",
    "LLM_TEMPERATURE": 0.0,
    "LLM_MAX_TOKENS": 1024,
    "WHISPER_MODEL_SIZE": "base",
    "WHISPER_DEVICE": "cpu",
    "WHISPER_COMPUTE_TYPE": "int8",
}

DEFAULT_DICTIONARY: Dict[str, str] = {}


# ============================================
# 設定読み込み
# ============================================

def load_settings() -> Dict[str, Any]:
    """
    settings.py から設定を安全に読み込む
    
    ファイルが存在しない場合や読み込みエラー時はデフォルト値を返す。
    
    Returns:
        設定値の辞書
    """
    settings = DEFAULT_SETTINGS.copy()
    settings_path = get_settings_path()
    
    if not settings_path.exists():
        print(f"[ConfigLoader] 警告: settings.py が見つかりません。デフォルト値を使用します。")
        return settings
    
    try:
        # settings.py を動的にインポート
        import importlib.util
        spec = importlib.util.spec_from_file_location("settings", settings_path)
        settings_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings_module)
        
        # 定義されている設定値を取得
        for key in DEFAULT_SETTINGS.keys():
            if hasattr(settings_module, key):
                settings[key] = getattr(settings_module, key)
                
        print(f"[ConfigLoader] settings.py 読み込み完了")
        return settings
        
    except Exception as e:
        print(f"[ConfigLoader] エラー: settings.py の読み込みに失敗しました: {e}")
        print(f"[ConfigLoader] デフォルト値を使用します。")
        return settings


def load_dictionary() -> Dict[str, str]:
    """
    dictionary.json から辞書を安全に読み込む
    
    ファイルが存在しない場合や読み込みエラー時は空の辞書を返す。
    
    Returns:
        読み -> 正解表記 の辞書
    """
    dictionary_path = get_dictionary_path()
    
    if not dictionary_path.exists():
        print(f"[ConfigLoader] 警告: dictionary.json が見つかりません。辞書機能は無効です。")
        return DEFAULT_DICTIONARY.copy()
    
    try:
        with open(dictionary_path, "r", encoding="utf-8") as f:
            dictionary = json.load(f)
            
        if not isinstance(dictionary, dict):
            raise ValueError("辞書ファイルの形式が不正です（オブジェクト形式である必要があります）")
            
        print(f"[ConfigLoader] dictionary.json 読み込み完了: {len(dictionary)}件")
        return dictionary
        
    except json.JSONDecodeError as e:
        print(f"[ConfigLoader] エラー: dictionary.json の解析に失敗しました: {e}")
        return DEFAULT_DICTIONARY.copy()
    except Exception as e:
        print(f"[ConfigLoader] エラー: dictionary.json の読み込みに失敗しました: {e}")
        return DEFAULT_DICTIONARY.copy()


# ============================================
# プロンプト構築
# ============================================

def build_dictionary_section(dictionary: Dict[str, str]) -> str:
    """
    辞書データからプロンプト用のセクションを構築する
    
    Args:
        dictionary: 読み -> 正解表記 の辞書
        
    Returns:
        プロンプトに埋め込む辞書セクション文字列
    """
    if not dictionary:
        return ""
    
    entries = [f"- 読み「{reading}」 → 正解「{correct}」" 
               for reading, correct in dictionary.items()]
    
    section = """

【修正ルール：用語辞書】
入力テキストの中に、以下の「読み」と同じ読み方をする単語が含まれていた場合、
文脈から判断して最も適切な場合のみ「正解の表記」に書き換えてください。
（多少の音のズレや、誤変換と思われる場合も適用対象とします）

"""
    section += "\n".join(entries)
    
    return section


def build_system_prompt() -> str:
    """
    完全なシステムプロンプトを構築する
    
    基本プロンプト + 辞書セクション を結合して返す。
    
    Returns:
        システムプロンプト文字列
    """
    base_prompt = """あなたは文章校正システムです。
ユーザーから入力されたテキストの誤字・脱字・フィラー（言い淀み）のみを修正して返してください。

【重要ルール】
1. 出力は「修正後のテキスト」のみ。挨拶や前置きは禁止。
2. 誤字やフィラーがない場合は、原文をそのまま出力。
3. 文末のニュアンス（～かな、～だよね）は維持。
4. 句読点が不足している場合のみ補う。"""
    
    dictionary = load_dictionary()
    dictionary_section = build_dictionary_section(dictionary)
    
    return base_prompt + dictionary_section


# ============================================
# ユーティリティ関数
# ============================================

def is_api_key_configured(settings: Optional[Dict[str, Any]] = None) -> bool:
    """
    APIキーが設定されているかチェックする
    
    Args:
        settings: 設定辞書（省略時は自動読み込み）
        
    Returns:
        設定されていればTrue
    """
    if settings is None:
        settings = load_settings()
        
    api_key = settings.get("GROQ_API_KEY", "")
    return api_key != "YOUR_API_KEY_HERE" and len(api_key) > 10


def model_exists() -> bool:
    """
    互換性維持のためのダミー関数
    Groq版ではモデルファイルは不要なので、常にTrueを返す
    
    Returns:
        常にTrue
    """
    return True


# ============================================
# グローバル設定インスタンス（遅延初期化）
# ============================================

_cached_settings: Optional[Dict[str, Any]] = None
_cached_prompt: Optional[str] = None


def get_settings() -> Dict[str, Any]:
    """
    設定を取得する（キャッシュ付き）
    
    Returns:
        設定値の辞書
    """
    global _cached_settings
    if _cached_settings is None:
        _cached_settings = load_settings()
    return _cached_settings


def get_system_prompt() -> str:
    """
    システムプロンプトを取得する（キャッシュ付き）
    
    Returns:
        システムプロンプト文字列
    """
    global _cached_prompt
    if _cached_prompt is None:
        _cached_prompt = build_system_prompt()
    return _cached_prompt


# ============================================
# 後方互換性のためのエイリアス
# ============================================

# 旧 config.py と同じインターフェースを提供
def _get_setting(key: str, default: Any = None) -> Any:
    """設定値を取得するヘルパー"""
    return get_settings().get(key, default)


# よく使う設定値をモジュールレベル変数として公開
GROQ_API_KEY = property(lambda self: _get_setting("GROQ_API_KEY"))
MODEL_NAME = property(lambda self: _get_setting("MODEL_NAME"))
LLM_TEMPERATURE = property(lambda self: _get_setting("LLM_TEMPERATURE"))
LLM_MAX_TOKENS = property(lambda self: _get_setting("LLM_MAX_TOKENS"))
SYSTEM_PROMPT = property(lambda self: get_system_prompt())


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    print("=== ConfigLoader テスト ===")
    print()
    print(f"プロジェクトルート: {get_project_root()}")
    print(f"settings.py パス: {get_settings_path()}")
    print(f"dictionary.json パス: {get_dictionary_path()}")
    print()
    
    print("=== 設定値 ===")
    settings = get_settings()
    for key, value in settings.items():
        if "KEY" in key:
            print(f"{key}: {'*' * 10}（非表示）")
        else:
            print(f"{key}: {value}")
    print()
    
    print(f"APIキー設定済み: {is_api_key_configured(settings)}")
    print()
    
    print("=== システムプロンプト ===")
    print(get_system_prompt())
