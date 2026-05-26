import os
import sys
import argparse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
    print("エラー: .env ファイルにトークンまたはチャンネルIDが設定されていません。")
    sys.exit(1)


# ── ユーザー名解決（APIコール結果をキャッシュ） ──────────────────────────

def resolve_username(client: WebClient, user_id: str, cache: dict) -> str:
    if user_id in cache:
        return cache[user_id]
    try:
        resp = client.users_info(user=user_id)
        profile = resp["user"]["profile"]
        name = profile.get("display_name") or profile.get("real_name") or user_id
    except SlackApiError:
        name = user_id
    cache[user_id] = name
    return name


# ── スレッド返信取得 ─────────────────────────────────────────────────────

def fetch_thread_replies(client: WebClient, thread_ts: str) -> list[dict]:
    replies = []
    cursor = None
    first_page = True
    try:
        while True:
            resp = client.conversations_replies(
                channel=SLACK_CHANNEL_ID,
                ts=thread_ts,
                cursor=cursor,
                limit=100,
            )
            page = resp["messages"]
            if first_page:
                page = page[1:]   # 先頭は親メッセージ自身なのでスキップ
                first_page = False
            replies.extend(page)
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except SlackApiError as e:
        print(f"  スレッド取得エラー (ts={thread_ts}): {e.response['error']}")
    return replies


# ── トップレベルメッセージ取得 ───────────────────────────────────────────

def fetch_channel_messages(client: WebClient, oldest_ts: str) -> list[dict]:
    messages = []
    cursor = None
    while True:
        resp = client.conversations_history(
            channel=SLACK_CHANNEL_ID,
            oldest=oldest_ts,
            cursor=cursor,
            limit=100,
        )
        if not resp["ok"]:
            print(f"APIエラー: {resp['error']}")
            break
        messages.extend(resp["messages"])
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return sorted(messages, key=lambda m: float(m["ts"]))


# ── Markdown 整形 ────────────────────────────────────────────────────────

def fmt_dt(ts: str) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def render_message(msg: dict, client: WebClient, user_cache: dict, level: int) -> list[str]:
    heading = "#" * level
    user_id = msg.get("user", "")
    username = resolve_username(client, user_id, user_cache) if user_id else "Bot/System"
    text = msg.get("text", "[テキストなし]")
    reply_count = msg.get("reply_count", 0)

    lines = [
        f"{heading} [{fmt_dt(msg['ts'])}] {username} (`{user_id}`)",
        "",
        f"- **type:** {'thread_reply' if msg.get('parent_user_id') else 'message'}",
        f"- **ts:** `{msg['ts']}`",
    ]
    if reply_count:
        lines.append(f"- **reply_count:** {reply_count}")
    lines += ["", text, ""]
    return lines


def build_markdown(
    messages: list[dict],
    client: WebClient,
    user_cache: dict,
    channel_name: str,
    oldest_dt: datetime,
) -> str:
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    oldest_iso = oldest_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    lines: list[str] = [
        "---",
        "source: slack",
        f"channel_id: {SLACK_CHANNEL_ID}",
        f"channel_name: {channel_name}",
        f"fetch_date: {now_iso}",
        f"period_start: {oldest_iso}",
        f"message_count: {len(messages)}",
        "---",
        "",
        f"# Slack Messages: #{channel_name}",
        "",
        f"**期間:** {oldest_dt.strftime('%Y-%m-%d %H:%M:%S UTC')} 以降  ",
        f"**メッセージ数:** {len(messages)} 件",
        "",
        "---",
        "",
    ]

    for msg in messages:
        lines += render_message(msg, client, user_cache, level=2)

        reply_count = msg.get("reply_count", 0)
        if reply_count:
            replies = fetch_thread_replies(client, msg["ts"])
            lines += [f"### スレッド返信 ({len(replies)} 件)", ""]
            for reply in replies:
                lines += render_message(reply, client, user_cache, level=4)

        lines += ["---", ""]

    return "\n".join(lines)


# ── エントリポイント ─────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Slackメッセージを取得してMarkdownに出力します")
    parser.add_argument(
        "--since",
        metavar="YYYY-MM-DD",
        help="取得開始日（例: 2026-04-01）。省略時は30日前。",
    )
    args = parser.parse_args()

    if args.since:
        try:
            oldest_dt = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print("エラー: 日付フォーマットが正しくありません。YYYY-MM-DD 形式で指定してください。")
            sys.exit(1)
    else:
        oldest_dt = datetime.now(timezone.utc) - timedelta(days=30)

    client = WebClient(token=SLACK_BOT_TOKEN)
    user_cache: dict[str, str] = {}

    channel_name = SLACK_CHANNEL_ID
    try:
        ch_resp = client.conversations_info(channel=SLACK_CHANNEL_ID)
        channel_name = ch_resp["channel"].get("name", SLACK_CHANNEL_ID)
    except SlackApiError:
        pass

    print(f"--- {oldest_dt.strftime('%Y-%m-%d %H:%M:%S UTC')} 以降のメッセージを取得します ---")

    try:
        messages = fetch_channel_messages(client, str(oldest_dt.timestamp()))
    except SlackApiError as e:
        print(f"Slack APIエラー: {e.response['error']}")
        sys.exit(1)

    print(f"取得完了！ トップレベル {len(messages)} 件\n")

    markdown = build_markdown(messages, client, user_cache, channel_name, oldest_dt)

    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"slack_messages_{timestamp_str}.md")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"✅ {filepath} に出力しました。")


if __name__ == "__main__":
    main()
