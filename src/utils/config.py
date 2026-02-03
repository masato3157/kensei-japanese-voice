# -*- coding: utf-8 -*-
"""
設定管理 - アプリケーション全体の設定値

このモジュールは、賢声アプリケーションで使用する設定値を一元管理します。
Groq API、プロンプト、UIパラメータなどをここで定義します。
"""

import os
import json
from pathlib import Path
from typing import List

# ============================================
# パス設定
# ============================================

# プロジェクトルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent.parent

# モデルディレクトリ（Whisperモデル用）
MODELS_DIR = PROJECT_ROOT / "models"

# 辞書ファイルパス
DICTIONARY_PATH = Path(__file__).parent.parent / "data" / "dictionary.json"


# ============================================
# Groq API設定
# ============================================

# Groq APIキー（https://console.groq.com で取得）
GROQ_API_KEY = "YOUR_API_KEY_HERE"

# 使用するモデル（日本語に強い最新モデル）
MODEL_NAME = "llama-3.3-70b-versatile"

# 生成設定
LLM_TEMPERATURE = 0.0      # 最も安定した出力
LLM_MAX_TOKENS = 1024      # 最大トークン数


# ============================================
# 辞書読み込み機能
# ============================================

def load_dictionary() -> List[str]:
    """
    辞書ファイルを読み込み、プロンプト用のリストを返す
    
    Returns:
        辞書エントリのリスト（例: ["- 読み「けんせい」 → 正解「賢声」", ...]）
    """
    try:
        if not DICTIONARY_PATH.exists():
            print(f"[Config] 辞書ファイルが見つかりません: {DICTIONARY_PATH}")
            return []
            
        with open(DICTIONARY_PATH, "r", encoding="utf-8") as f:
            dictionary = json.load(f)
            
        entries = []
        for reading, correct in dictionary.items():
            entries.append(f"- 読み「{reading}」 → 正解「{correct}」")
            
        print(f"[Config] 辞書読み込み完了: {len(entries)}件")
        return entries
        
    except json.JSONDecodeError as e:
        print(f"[Config] 辞書ファイルの解析エラー: {e}")
        return []
    except Exception as e:
        print(f"[Config] 辞書読み込みエラー: {e}")
        return []


def build_dictionary_section() -> str:
    """
    辞書セクションを構築する
    
    Returns:
        プロンプトに埋め込む辞書セクション文字列
    """
    entries = load_dictionary()
    
    if not entries:
        return ""
        
    section = """
【修正ルール：用語辞書】
入力テキストの中に、以下の「読み」と同じ読み方をする単語が含まれていた場合、
文脈から判断して最も適切な場合のみ「正解の表記」に書き換えてください。
（多少の音のズレや、誤変換と思われる場合も適用対象とします）

"""
    section += "\n".join(entries)
    
    return section


# ============================================
# システムプロンプト
# ============================================

# 基本プロンプト（厳格版 - 無言の校正機）
_BASE_PROMPT = """あなたは文章校正システムです。
ユーザーから入力されたテキストの誤字・脱字・フィラー（言い淀み）のみを修正して返してください。

【重要ルール】
1. 出力は「修正後のテキスト」のみ。挨拶や前置きは禁止。
2. 誤字やフィラーがない場合は、原文をそのまま出力。
3. 文末のニュアンス（～かな、～だよね）は維持。
4. 句読点が不足している場合のみ補う。"""

# 辞書セクションを追加した完全なプロンプト
SYSTEM_PROMPT = _BASE_PROMPT + build_dictionary_section()


# ============================================
# 音声設定
# ============================================

# Whisperモデルサイズ
WHISPER_MODEL_SIZE = "base"

# Whisperデバイス・計算精度
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

# 録音設定
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1


# ============================================
# UI設定
# ============================================

# メインウィンドウサイズ
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 320

# クリップボード貼り付け遅延（秒）
PASTE_DELAY = 0.1


# ============================================
# ユーティリティ関数
# ============================================

def ensure_models_dir() -> Path:
    """モデルディレクトリが存在することを確認し、なければ作成する"""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR


def is_api_key_configured() -> bool:
    """Groq APIキーが設定されているかチェックする"""
    return GROQ_API_KEY != "YOUR_API_KEY_HERE" and len(GROQ_API_KEY) > 10


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    print("=== 設定値一覧 ===")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"MODEL_NAME: {MODEL_NAME}")
    print(f"APIキー設定済み: {is_api_key_configured()}")
    print(f"辞書パス: {DICTIONARY_PATH}")
    print()
    print("=== システムプロンプト ===")
    print(SYSTEM_PROMPT)

# ==========================================
# 互換性維持のためのダミー関数
# ==========================================
def model_exists():
    """Groq版ではモデルファイルは不要なので、常にTrue（準備OK）を返す"""
    return True