
# Python環境の構築

## 仮想環境の作成
```python
# macOS / Linux / Windows 共通
python -m venv .venv
```

## アクティベート

Mac
``` python
source .venv/bin/activate
```


# Slack メッセージ取得ツール (get-slack-message)

このツールは、指定したSlackチャンネルから過去30日分のメッセージ履歴を取得し、Markdown形式のファイルとして outputs/ ディレクトリに自動出力するPythonスクリプトです。

1. Slack API 側の設定手順（事前準備）
プログラムを動作させるには、Slackの管理画面でアプリを作成し、適切な権限を付与してチャンネルへ招待する必要があります。

## ステップ 1-1: Slackアプリの新規作成
1. ブラウザで Slack API 管理画面 にアクセスします。[Slack APIはこちら](https://docs.slack.dev/)
2. 画面右上にある 「Create New App」 ボタンをクリックします。
3. ポップアップが表示されたら、「From scratch」 を選択します。
4. 以下の項目を入力・選択します：
* App Name: アプリ名（例: Slack Message Fetcher）
* Pick a workspace...: スクリプトを実行したい（メッセージを取得したい）Slackのワークスペースを選択

5. 「Create App」 ボタンをクリックします。

## ステップ 1-2: 権限（Scopes）の設定
1. アプリ管理画面の左メニューにある 「OAuth & Permissions」 をクリックします。
2. ページをスクロールし、「Scopes」 セクションを探します。
3. 「Bot Token Scopes」（※User Token Scopesではないので注意）にある 「Add an OAuth Scope」 をクリックします。
4. 以下の2つの権限を追加してください：
 * channels:history （公開チャンネルのメッセージ履歴を取得する権限）
 * groups:history （非公開チャンネル（プライベートグループ）からも取得したい場合に必要）

## ステップ 1-3: アプリのインストールとトークンの取得
1. 同ページの少し上にある 「OAuth Tokens for Your Workspace」 セクションに移動します。
2. 「Install to Workspace」 ボタンをクリックします。権限確認画面（「〜がワークスペースにアクセスする権限をリクエストしています」）が表示されるので、「許可 (Allow)」 をクリックします。
3. インストールが完了すると、「Bot OAuth Token」 が発行されます（xoxb- から始まる長い文字列）。これをコピーしておきます。

## ステップ 1-4: チャンネルIDの確認とボットの招待
1. Slackアプリを開き、メッセージを取得したいチャンネルへ移動します。画面上部のチャンネル名をクリックして詳細画面を開き、ポップアップ最下部にある 「チャンネルID」（C または G から始まる英数字。例: C0123456789）をコピーします。
2. ボットの招待: 対象チャンネルのチャット欄で、以下のように入力して送信します。

```
/invite @アプリ名
```

※「@アプリ名」は、ステップ1-1で設定した名前です。この招待作業を行わないと、実行時に not_in_channel エラーが発生します。

## 2. ローカル環境のセットアップ手順ステップ
2-1: Gitリポジトリから最新ソースコードをプルローカル環境のターミナルを起動し、リポジトリのディレクトリ（get-slack-message）に移動して最新コードを取得します。git pull origin main

# ステップ 2-2: Python 仮想環境（venv）の構築
競合を避けるために仮想環境を作成し、アクティベート（有効化）します。

macOS / Linux の場合:
```python3 -m venv .venv
source .venv/bin/activate
```

Windows の場合（コマンドプロンプト）:
```
python -m venv .venv
.venv\Scripts\activate
```

Windows の場合（PowerShell）:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

※アクティベートが成功すると、ターミナルの左端に (.venv) と表示されます。

## ステップ 2-3: 依存パッケージのインストール
仮想環境が有効な状態で、必要なライブラリをインストールします。

```
pip install -r requirements.txt
```

## ステップ 2-4: 環境変数（.env）の設定
プロジェクト内にある .env.example をコピーして、新規に .env ファイルを作成します。作成した .env をテキストエディタで開き、取得したトークンとチャンネルIDを記述します。
```
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_CHANNEL_ID=C0123456789
```

## 3. スクリプトの実行方法
仮想環境が有効化されている状態で、以下のコマンドを実行します。
```
python src/fetch_message.py
```
実行時の出力ログ例実行に成功すると、ターミナルに以下のような進捗ログが表示されます。

```
--- 過去30日分（2026-04-21 14:04:22 UTC 以降）のメッセージを取得します ---

取得完了！ 合計: 42 件のメッセージが見つかりました。
✅ outputs/slack_messages_20260521_231500.md にMarkdownファイルとして出力しました。
```


## 1. 出力されるファイルについて
スクリプトを実行すると、自動的に /outputs ディレクトリが作成され、その中に日時を冠したMarkdownファイル（.md）が書き出されます。
* ファイル名の例: slack_messages_20260521_231500.md
* 出力形式:

```
# Slack Messages

**取得対象期間:** 2026-04-21 14:04:22 UTC 以降

---
### U0123456789 - 2026-05-20 09:30:15 UTC
お疲れ様です！本日のタスク報告です。
---

```

# 5. トラブルシューティング
❌ not_in_channel エラーが発生する場合
* 原因: 作成したSlackアプリ（Bot）が、指定したチャンネルに参加していません。
* 解決策: Slackアプリ上で取得対象のチャンネルを開き、メッセージ入力欄に /invite @アプリ名 と入力して送信し、アプリをメンバーに加えてください。

❌ 「エラー: .env ファイルにトークンまたはチャンネルIDが設定されていません。」となる場合
* 原因: .env ファイルの名前が .env.txt などに誤って変わっているか、環境変数名がプログラムと一致していません。
* 解決策:ファイル名が正しく .env であるか確認してください。変数名が SLACK_BOT_TOKEN、および SLACK_CHANNEL_ID と正確に記述されているかチェックしてください（特に CHANNEL のLの数に注意）。