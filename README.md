# Slack メッセージ取得ツール (get-slack-message)

指定した日付以降の Slack チャンネルのメッセージとスレッド返信を取得し、AI が読み取りやすい Markdown 形式で `outputs/` ディレクトリに出力する Python スクリプトです。

---

## 1. Slack API の設定（事前準備）

プログラムを動作させるには、Slack の管理画面でアプリを作成し、適切な権限を付与してチャンネルへ招待する必要があります。

### ステップ 1-1: Slack アプリの新規作成

1. ブラウザで [Slack API 管理画面](https://docs.slack.dev/) にアクセスします。
2. 画面右上にある「Create New App」ボタンをクリックします。
3. ポップアップが表示されたら「From scratch」を選択します。
4. 以下の項目を入力・選択します。
   - **App Name:** アプリ名（例: Slack Message Fetcher）
   - **Pick a workspace...:** メッセージを取得したい Slack ワークスペースを選択
5. 「Create App」ボタンをクリックします。

### ステップ 1-2: 権限（Scopes）の設定

1. アプリ管理画面の左メニューにある「OAuth & Permissions」をクリックします。
2. ページをスクロールし「Scopes」セクションを探します。
3. 「Bot Token Scopes」（※ User Token Scopes ではないので注意）にある「Add an OAuth Scope」をクリックします。
4. 以下の権限をすべて追加してください。

| スコープ | 用途 |
|---|---|
| `channels:history` | 公開チャンネルのメッセージ履歴を取得 |
| `groups:history` | 非公開チャンネルのメッセージ履歴を取得（必要な場合） |
| `channels:read` | チャンネル名を取得 |
| `users:read` | ユーザー ID を表示名に変換 |

### ステップ 1-3: アプリのインストールとトークンの取得

1. 同ページ上部の「OAuth Tokens for Your Workspace」セクションに移動します。
2. 「Install to Workspace」ボタンをクリックし、権限確認画面で「許可 (Allow)」をクリックします。
3. インストール完了後に発行される「Bot OAuth Token」（`xoxb-` から始まる文字列）をコピーしておきます。

> **注意:** スコープを変更した場合は、同ページの「Reinstall to Workspace」ボタンでトークンを再発行してください。

### ステップ 1-4: チャンネル ID の確認とボットの招待

1. Slack アプリでメッセージを取得したいチャンネルへ移動し、画面上部のチャンネル名をクリックして詳細画面を開きます。ポップアップ最下部に表示される「チャンネル ID」（`C` または `G` から始まる英数字。例: `C0123456789`）をコピーします。
2. 対象チャンネルのチャット欄で以下を送信し、ボットを招待します。

```
/invite @アプリ名
```

※ この招待を行わないと、実行時に `not_in_channel` エラーが発生します。

---

## 2. ローカル環境のセットアップ

### ステップ 2-1: 最新コードの取得

```bash
git pull origin main
```

### ステップ 2-2: Python 仮想環境の構築

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows（コマンドプロンプト）:**
```bat
python -m venv .venv
.venv\Scripts\activate
```

**Windows（PowerShell）:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

※ アクティベートが成功すると、ターミナルの左端に `(.venv)` と表示されます。

### ステップ 2-3: 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### ステップ 2-4: 環境変数（.env）の設定

`.env.example` をコピーして `.env` ファイルを作成し、トークンとチャンネル ID を記入します。

```bash
cp .env.example .env
```

```
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_CHANNEL_ID=C0123456789
```

---

## 3. スクリプトの実行方法

仮想環境を有効化した状態で実行します。

```bash
# 直近30日分を取得（デフォルト）
python src/fetch_message.py

# 取得開始日を指定する場合
python src/fetch_message.py --since 2026-05-01
```

| オプション | 説明 |
|---|---|
| `--since YYYY-MM-DD` | 取得開始日を指定。省略時は実行日から30日前。 |

### 実行ログの例

```
--- 2026-05-01 00:00:00 UTC 以降のメッセージを取得します ---
取得完了！ トップレベル 42 件

✅ outputs/slack_messages_20260526_120000.md に出力しました。
```

---

## 4. 出力ファイルについて

実行すると `outputs/` ディレクトリに日時を冠した Markdown ファイルが生成されます。

- **ファイル名の例:** `slack_messages_20260526_120000.md`

### 出力形式

```markdown
---
source: slack
channel_id: C0123456789
channel_name: general
fetch_date: 2026-05-26T12:00:00+00:00
period_start: 2026-05-01T00:00:00+00:00
message_count: 42
---

# Slack Messages: #general

**期間:** 2026-05-01 00:00:00 UTC 以降  
**メッセージ数:** 42 件

---

## [2026-05-20 09:30:15 UTC] 山田 太郎 (`U0123456789`)

- **type:** message
- **ts:** `1747733415.000000`
- **reply_count:** 2

お疲れ様です！本日のタスク報告です。

### スレッド返信 (2 件)

#### [2026-05-20 09:35:00 UTC] 佐藤 花子 (`U0987654321`)

- **type:** thread_reply
- **ts:** `1747733700.000000`

ありがとうございます！

---
```

ファイル先頭の YAML フロントマターにチャンネル情報・取得日時・期間などのメタデータが記載されます。スレッド返信は親メッセージの直下に展開されます。

---

## 5. トラブルシューティング

**`not_in_channel` エラーが発生する場合**
- 原因: ボットが対象チャンネルに参加していません。
- 解決策: 対象チャンネルで `/invite @アプリ名` を実行してボットを招待してください。

**「エラー: .env ファイルにトークンまたはチャンネルIDが設定されていません。」となる場合**
- 原因: `.env` ファイル名が `.env.txt` などになっているか、変数名が一致していません。
- 解決策: ファイル名が正しく `.env` であること、変数名が `SLACK_BOT_TOKEN` および `SLACK_CHANNEL_ID` と正確に記述されていることを確認してください（`CHANNEL` の `L` の数に注意）。

**ユーザー名が ID のまま表示される場合**
- 原因: Bot Token Scopes に `users:read` が追加されていないか、トークンが再発行されていません。
- 解決策: ステップ 1-2 の手順で `users:read` を追加し、「Reinstall to Workspace」でトークンを再発行してください。

**チャンネル名が ID のまま表示される場合**
- 原因: Bot Token Scopes に `channels:read` が追加されていないか、トークンが再発行されていません。
- 解決策: ステップ 1-2 の手順で `channels:read` を追加し、「Reinstall to Workspace」でトークンを再発行してください。
