from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction, FlexSendMessage
)
import os

from stadium_weather import STADIUM_WEATHER
app = Flask(__name__)

# 從環境變數讀取
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

@app.get("/healthz")
def healthz():
    return "ok", 200

STADIUMS = [
    "天母棒球場",
    "臺北大巨蛋",
    "新莊棒球場",
    "桃園國際棒球場",
    "臺中洲際棒球場",
    "臺南市立棒球場",
    "澄清湖棒球場",
]

def make_quick_reply():
    return TextSendMessage(
        text="請選擇球場：",
        quick_reply=QuickReply(
            items=[
                QuickReplyButton(action=MessageAction(label=s, text=s))
                for s in STADIUMS
            ]
        ),
    )

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"
def build_flex_all(stadium: str, data: dict) -> FlexSendMessage:
    """
    將 STADIUM_WEATHER(...).data 轉成 Flex Carousel。
    - 每個「日期」可分成多個 bubble（每 bubble 最多放 CHUNK = 10 個時段）
    - 直接帶回所有資料（不做省略）
    """
    CHUNK = 10

    def make_row(time_str, wx, pop):
        return {
            "type": "box", "layout": "baseline", "spacing": "sm",
            "contents": [
                {"type": "text", "text": time_str, "size": "sm", "flex": 2, "wrap": True},
                {"type": "text", "text": wx or "-", "size": "sm", "flex": 5, "wrap": True},
                {"type": "text", "text": f"降雨 {pop or '-'}", "size": "sm", "flex": 3, "align": "end"},
            ]
        }

    bubbles = []
    for date, rows in data.items():
        for part_idx in range(0, len(rows), CHUNK):
            part = rows[part_idx:part_idx + CHUNK]

            body_contents = [
                {"type": "text", "text": stadium, "weight": "bold", "size": "md", "wrap": True},
                {"type": "text", "text": date if len(rows) <= CHUNK else f"{date}（{part_idx+1}-{min(part_idx+CHUNK, len(rows))}/{len(rows)}）",
                 "size": "sm", "color": "#888888", "margin": "sm"},
                {"type": "separator", "margin": "md"},
            ]

            for r in part:
                body_contents.append(make_row(r.get("time", "-"), r.get("天氣", "-"), r.get("降雨機率", "-")))

            bubbles.append({
                "type": "bubble",
                "body": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": body_contents}
            })

    return FlexSendMessage(
        alt_text=f"{stadium} 天氣預報",
        contents={"type": "carousel", "contents": bubbles[:10]}
    )
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()
    normalized = user_text.replace("台", "臺")

    if normalized in STADIUMS:
        try:
            weather = STADIUM_WEATHER(normalized)
            flex = build_flex_all(normalized, weather.data)
            line_bot_api.reply_message(event.reply_token, flex)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"查詢失敗：{e}"))
    else:
        line_bot_api.reply_message(event.reply_token, make_quick_reply())

if __name__ == "__main__":
    app.run()