# -*- coding: utf-8 -*-
"""
設定管理 - アプリケーション全体の設定値

このモジュールは、賢声アプリケーションで使用する設定値を一元管理します。
モデルパス、プロンプト、UIパラメータなどをここで定義します。
"""

import os
from pathlib import Path

# ============================================
# パス設定
# ============================================

# プロジェクトルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent.parent

# モデルディレクトリ
MODELS_DIR = PROJECT_ROOT / "models"

# デフォルトのLLMモデルパス
MODEL_PATH = str(MODELS_DIR / "Llama-3-ELYZA-JP-8B-q4_k_m.gguf")


# ============================================
# AI設定
# ============================================

# LLMのコンテキストサイズ
LLM_CONTEXT_SIZE = 2048

# LLMの生成設定
LLM_TEMPERATURE = 0.1      # 低く設定して安定性を重視
LLM_TOP_P = 0.9
LLM_REPEAT_PENALTY = 1.1   # 繰り返し防止

# システムプロンプト（厳格版 - 無言の校正機）
SYSTEM_PROMPT = """あなたは文章校正システムです。
ユーザーから入力されたテキストの誤字・脱字・フィラー（言い淀み）のみを修正して返してください。

【重要ルール】
1. **出力は「修正後のテキスト」のみ**にすること。挨拶、説明、前置き（例:「修正します」）は一切禁止。
2. 誤字やフィラーがない場合は、**原文をそのまま**出力すること。
3. 文末のニュアンス（～かな、～だよね）は変更しないこと。
4. 句読点が不足している場合のみ補うこと。

【例】
User: まあ、今の段階としてはいいかな
System: まあ、今の段階としてはいいかな。

User: あのねあのねメールアドリスが届いているはずだから
System: あのね、メールアドレスが届いているはずだから。

User: ちょっと疲れちゃったわ。今日、昨日はね、ちょっと飲み過ぎてね。もう、疲れ。
System: ちょっと疲れちゃったわ。今日、昨日はね、ちょっと飲みすぎてね。もう、疲れた。"""


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


def model_exists() -> bool:
    """LLMモデルファイルが存在するかチェックする"""
    return os.path.exists(MODEL_PATH)


# モジュールを直接実行した場合のテスト用
if __name__ == "__main__":
    print("=== 設定値一覧 ===")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"MODELS_DIR: {MODELS_DIR}")
    print(f"MODEL_PATH: {MODEL_PATH}")
    print(f"モデル存在: {model_exists()}")
    print()
    print("=== システムプロンプト ===")
    print(SYSTEM_PROMPT)
