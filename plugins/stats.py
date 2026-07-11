from pyrogram import Client, filters
import asyncio
from datetime import datetime
import pytz

ADMIN_ID = 123456789

# Predefined usernames
USERNAMES = [
    "@USER1",
    "@USER2",
    "@USER3"
]

# Status storage
DAILY_STATUS = {
    username: {
        "30": False,
        "bonus": False
    }
    for username in USERNAMES
}


@Client.on_message(filters.command("daily"))
async def daily_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply(
            "Usage:\n/daily 30\n/daily bonus"
        )

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else None
    )

    if username not in DAILY_STATUS:
        return

    arg = message.command[1].lower()

    if arg == "30":
        DAILY_STATUS[username]["30"] = True
    elif arg == "bonus":
        DAILY_STATUS[username]["bonus"] = True
    else:
        return await message.reply(
            "Use /daily 30 or /daily bonus"
        )

    await message.reply("✅ Recorded")


@Client.on_message(
    filters.command("status")
    & filters.user(ADMIN_ID)
)
async def status_cmd(client, message):
    report = build_report()
    await message.reply(report)


def build_report():
    lines = ["📊 Daily Report\n"]

    for username, data in DAILY_STATUS.items():
        lines.append(
            f"{username}\n"
            f"  30: {'✅' if data['30'] else '❌'}\n"
            f"  Bonus: {'✅' if data['bonus'] else '❌'}\n"
        )

    return "\n".join(lines)


async def daily_report_loop(client):
    ist = pytz.timezone("Asia/Kolkata")

    while True:
        now = datetime.now(ist)

        if now.hour == 18 and now.minute == 0:
            await client.send_message(
                ADMIN_ID,
                build_report()
            )

            await asyncio.sleep(65)

        await asyncio.sleep(20)


async def reset_loop():
    ist = pytz.timezone("Asia/Kolkata")

    while True:
        now = datetime.now(ist)

        if now.hour == 0 and now.minute == 0:
            for username in DAILY_STATUS:
                DAILY_STATUS[username]["30"] = False
                DAILY_STATUS[username]["bonus"] = False

            await asyncio.sleep(65)

        await asyncio.sleep(20)


@app.on_message(filters.command("startreport") & filters.user(ADMIN_ID))
async def start_report(_, message):
    asyncio.create_task(daily_report_loop(app))
    asyncio.create_task(reset_loop())

    await message.reply("✅ Report loops started")
