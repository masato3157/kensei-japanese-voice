# -*- coding: utf-8 -*-
"""
賢声 (Kensei) - ユーザー設定ファイル

このファイルはユーザーが編集する設定専用ファイルです。
関数やクラスは含まれていません。変数の値を変更してカスタマイズしてください。
"""

# ============================================
# Groq API設定
# ============================================

# Groq APIキー（https://console.groq.com で取得）
GROQ_API_KEY = "YOUR_API_KEY_HERE"

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
