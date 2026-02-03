# -*- coding: utf-8 -*-
"""
賢声 (Kensei) - ユーザー設定ファイル（公開用）

このファイルはユーザーが編集する設定専用ファイルです。
関数やクラスは含まれていません。変数の値を変更してカスタマイズしてください。

【APIキーについて】
本物のAPIキーは `local_settings.py` に記述してください。
このファイル（settings.py）はGitにコミットされます。
"""

# ============================================
# Groq API設定
# ============================================

# APIキーはlocal_settings.pyに記述してください（Git上はダミー）
GROQ_API_KEY = "API_KEY_IS_IN_LOCAL_SETTINGS"

# 使用するモデル（日本語に強い最新モデル）
MODEL_NAME = "llama-3.3-70b-versatile"

# 生成設定（0.0 = 最も安定、1.0 = 最もランダム）
LLM_TEMPERATURE = 0.0

# 最大トークン数
LLM_MAX_TOKENS = 1024


# ============================================
# 音声認識設定
# ============================================

# Whisperモデルサイズ（tiny, base, small, medium, large）
WHISPER_MODEL_SIZE = "base"

# 計算デバイス（cpu または cuda）
WHISPER_DEVICE = "cpu"

# 計算精度（int8, float16, float32）
WHISPER_COMPUTE_TYPE = "int8"


# ============================================
# ローカル設定（秘密鍵）の読み込み
# ============================================
try:
    # local_settings.py があれば、変数を上書きする
    from local_settings import *
except ImportError:
    # ファイルがなくてもエラーにしない（CI環境などへの配慮）
    pass
