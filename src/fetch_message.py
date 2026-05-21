import os
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# .env ファイルから環境変数を読み込み
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID") 

if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
    print("エラー: .env ファイルにトークンまたはチャンネルIDが設定されていません。")
    sys.exit(1)

def fetch_30_days_messages():
    # Slackクライアントの初期化
    client = WebClient(token=SLACK_BOT_TOKEN)
    
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    oldest_timestamp = str(thirty_days_ago.timestamp())
    
    messages = []
    cursor = None
    
    print(f"--- 過去30日分（{thirty_days_ago.strftime('%Y-%m-%d %H:%M:%S UTC')} 以降）のメッセージを取得します ---")
    
    try:
        while True:
            response = client.conversations_history(
                channel=SLACK_CHANNEL_ID,
                oldest=oldest_timestamp,
                cursor=cursor,
                limit=100
            )
            
            if response["ok"]:
                page_messages = response["messages"]
                messages.extend(page_messages)
                
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
            else:
                print(f"APIエラー: {response['error']}")
                break
                
        print(f"\n取得完了！ 合計: {len(messages)} 件のメッセージが見つかりました。\n")
        
        # --- ここから Markdown への出力処理を追加 ---
        
        # outputsディレクトリの作成（存在しない場合のみ）
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        # 出力ファイル名の生成（例: slack_messages_20231024_153000.md）
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"slack_messages_{timestamp_str}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Markdownファイルへの書き込み
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Slack Messages\n\n")
            f.write(f"**取得対象期間:** {thirty_days_ago.strftime('%Y-%m-%d %H:%M:%S UTC')} 以降\n\n")
            f.write("---\n\n")
            
            # 取得したメッセージを古い順にソートして書き込む
            for msg in reversed(messages):
                msg_time = datetime.fromtimestamp(float(msg['ts']), tz=timezone.utc)
                user = msg.get('user', 'Bot/System')
                text = msg.get('text', '[テキストなし]')
                
                # Markdown形式でフォーマット
                f.write(f"### {user} - {msg_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
                f.write(f"{text}\n\n")
                f.write("---\n\n")
                
        print(f"✅ {filepath} にMarkdownファイルとして出力しました。")
            
    except SlackApiError as e:
        print(f"Slack APIエラーが発生しました: {e.response['error']}")

if __name__ == "__main__":
    fetch_30_days_messages()