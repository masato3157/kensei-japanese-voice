# 開発ルール（AI用）

このリポジトリは「*賢声（賢い日本語音声入力）*」の開発用です。
AIは、以下のルールを必ず守ってください。

## 1. コード提示ルール（最重要）
- ユーザーが「コードを出して」と言った場合、**必ずファイル全文**を提示する。
- 差分だけ、数行だけ、抜粋だけ、は禁止。
- 「ここを直して」などの口頭指示だけで済ませない。
- 例外はなし。

## 2. ステップ進行ルール
- 手順は必ずステップ形式で説明する。
- **ユーザーが「できた」「理解した」と言うまで次のステップに進まない。**
- 1ステップに複数の作業を詰め込まない。

## 3. 変更の安全ルール
- 推測で壊しそうな変更をしない。
- 変更前に「何が原因か」を一言で説明する。
- 保存や起動に影響する変更は特に慎重に扱う。

## 4. 名前の統一ルール
- アプリ名は **賢声** 意味は「賢い日本語音声入力」
- 英語表記は `kensei-japanese-voice` を正とする。

## 5. 返答の文章ルール（日本語）
- 思考中も含めて、ユーザーの目に触れる表示はすべて日本語。
- 短く、シンプルな文を連ねる。
- 中学3年生にわかる言葉を使う。
- ていねいな話し言葉にする。

## 6. 技術的な制約ルール（Windows/Python）
- コード内のコメントはすべて**日本語**で書く。
- ファイルの読み書きには必ず `encoding='utf-8'` を指定する（Windows文字化け対策）。
- `pip install` が必要なライブラリを使う時は、コードを出す前に必ずインストールコマンドを提示する。

## 7.もっとも重要なルール
You must follow Python best practices strictly.

Coding rules:
- Follow PEP 8 at all times.
- Use explicit and readable code over clever code.
- One function must do one thing only.
- Keep functions short and simple.
- Avoid global state.
- Prefer pure functions when possible.

Restrictions:
- Do NOT invent your own coding style.
- Do NOT optimize prematurely.
- Do NOT use advanced patterns unless explicitly requested.
- If unsure, choose the simplest standard Python solution.

Output rules:
- Always output complete files.
- Never output partial diffs.
- Code must be immediately runnable.
