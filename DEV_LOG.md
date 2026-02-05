# 賢声 (Kensei) 開発ログ

このファイルは、賢声プロジェクトの開発経緯を記録するためのログファイルです。

---

## 2026-02-03

### v0.1 - 基本プロトタイプ
**コミット**: `651fc5d`

#### 実装内容
- **プロジェクト初期化**: ディレクトリ構造の作成、`requirements.txt` の作成
- **音声録音機能** (`src/audio/recorder.py`): PyAudioを使用した16kHz/mono/16bit録音
- **音声認識機能** (`src/audio/transcriber.py`): faster-whisperによる音声認識（baseモデル、CPU/int8）
- **キーボードハンドラー** (`src/utils/keyboard_handler.py`): 左Ctrlキーのグローバル監視
- **クリップボード操作** (`src/utils/clipboard.py`): テキストのコピー＆ペースト
- **メインウィンドウ** (`src/ui/main_window.py`): Tkinterベースの基本UI
- **プッシュ・トゥ・トーク**: 左Ctrlキーで録音→認識→貼り付けの一連処理

---

### v0.2 - AI整形機能の統合（ローカルLLM版）
**コミット**: `1f6a6bc`

#### 実装内容
- **設定管理** (`src/utils/config.py`): モデルパス、システムプロンプトの一元管理
- **AI整形機能** (`src/ai/corrector.py`): llama.cppによるテキスト校正
  - 使用モデル: `Llama-3-ELYZA-JP-8B-q4_k_m.gguf`
  - 処理時間: 約10秒/リクエスト
- **システムプロンプトの調整**: 会話禁止、ニュアンス保持、フィラー削除のバランス調整
- **処理パイプライン**: Whisper認識 → Llama整形 → 貼り付け

#### 課題
- ローカルLLMの処理速度が遅い（約10秒）
- プロンプト調整が難しい（回答モードに入りやすい）

---

### v0.3 - Groqクラウド版への移行 + リファクタリング
**コミット**: `2b1a606`, `dfdfb1c`

#### 実装内容
- **Groq API対応**: ローカルLLMからクラウド版へ移行
  - 使用モデル: `llama-3.3-70b-versatile`
  - 処理時間: 約0.5〜1秒/リクエスト（大幅な高速化）
- **設定リファクタリング**:
  - `settings.py`: ユーザー編集用の設定ファイル（公開用）
  - `local_settings.py`: 機密情報（APIキー）用ファイル（Git管理外）
  - `src/utils/config_loader.py`: 設定読み込みロジックの分離
- **辞書機能** (`src/data/dictionary.json`): カスタム用語の定義
  - プロンプト辞書注入方式で固有名詞の誤変換を修正
- **セキュリティ強化**: APIキーの分離管理、`.gitignore`の整備
- **起動スクリプト** (`start_kensei.bat`): ダブルクリックで起動可能

#### ファイル構成（v0.3時点）
```
kensei-japanese-voice/
├── main.py                    # エントリーポイント
├── settings.py                # ユーザー設定（公開用）
├── local_settings.py          # 秘密鍵設定（Git管理外）
├── start_kensei.bat           # 起動スクリプト
├── requirements.txt           # 依存関係
├── .gitignore                 # Git除外設定
├── src/
│   ├── audio/
│   │   ├── recorder.py        # 音声録音
│   │   └── transcriber.py     # 音声認識（Whisper）
│   ├── ai/
│   │   └── corrector.py       # AI整形（Groq）
│   ├── ui/
│   │   └── main_window.py     # メインウィンドウ
│   ├── utils/
│   │   ├── config.py          # 旧設定（互換性維持）
│   │   ├── config_loader.py   # 設定読み込みロジック
│   │   ├── keyboard_handler.py # キーボード監視
│   │   └── clipboard.py       # クリップボード操作
│   └── data/
│       └── dictionary.json    # 用語辞書
└── models/                    # AIモデル格納（Git管理外）
```

---

## 2026-02-04

### v0.4.7 - シンプル構成への回帰（コンテキスト主導）
**コミット**: 本日

#### 方針変更
学習機能（辞書登録、オートスキャン、キー操作によるフィードバック）を**全廃**し、
`ContextManager`による「会話履歴の保持」のみを残すシンプル構成へ移行。
LLMの文脈推論能力だけで精度向上を目指す。

#### 削除された機能
- **Alt学習機能**: オートスキャン＋無条件学習（削除）
- **pyperclip依存**: クリップボード操作（削除）
- **TextSimilarity**: 類似度判定（削除）
- **辞書登録**: `dictionary.py`への書き込み（削除）

#### 新しいキー操作
| キー | 機能 |
|------|------|
| **左Ctrl** | 押している間録音（プッシュ・トゥ・トーク） |
| **右Ctrl** | 録音開始/停止（トグル） |

#### 変更されたファイル
- `src/ui/main_window.py`: Alt関連、学習メソッド、pyperclip削除
- `src/utils/config_loader.py`: システムプロンプトをコンテキスト重視に変更
- `main.py`: ヒントログからAlt削除

#### コンテキスト主導の精度向上
- 会話履歴を自動参照
- 同音異義語を文脈から判定（病院の話 → 「かんじゃ」= 患者）

---

## 今後の予定

- [ ] 設定画面の実装
- [ ] ゴーストテキスト表示機能
- [ ] エラーハンドリングの強化
- [ ] パッケージング（exe化）

---

## 2026-02-05

### v0.6.3 - ハイブリッドエンジンの実装 (Cloud/Local切替)
**コミット**: 本日

#### 実装機能
- **ハイブリッド推論エンジン** (`src/ai/hybrid_corrector.py`):
    - **Cloud Mode**: Groq API (Llama 3 70B等) を使用し、高速・高精度な整形を実現。
    - **Local Mode**: ローカルLLMを使用し、完全オフライン環境での動作を実現。
    - **自動切替**: 設定画面 (`SettingsDialog`) からシームレスにモード変更可能。
- **Gemma-2-2B (JP-IT) の採用**:
    - 当初計画していた LFM (Liquid Foundation Model 1.2B) は、ライブラリ (`llama-cpp-python`) のアーキテクチャ非対応により導入を断念。
    - 代替として、Google製軽量モデル **Gemma-2-2B-JP-IT** (GGUF版) を採用。
    - プロンプトを `<start_of_turn>` 形式に最適化し、AIの余計な会話を抑制。
- **冗長性確保**:
    - GPU (CUDA) での動作を優先し、利用不可時は自動でCPUモードにフォールバックするロジックを実装。
    - 設定変更時のエンジン自動リロード機能。

#### 変更されたファイル
- `src/ai/hybrid_corrector.py`: 新規作成。エンジンの統合ロジック。
- `src/ui/main_window.py`: `TextCorrector` を `HybridCorrector` に置き換え。設定画面呼び出しの修正。
- `config.json`: 設定ファイル（モデルパス、APIキーなど）。
- `task.md`, `walkthrough.md`: プロジェクト管理用アーティファクト。

#### 既知の問題・課題
- LFMモデルは現状のWindows環境では動作しない（将来的なライブラリ更新待ち）。
- Gemma 2 はプロンプト次第で会話モードになりやすいため、強力なシステムプロンプトで制御中。
