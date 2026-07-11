from pyrogram import Client, filters
import asyncio
from datetime import datetime
import pytz
from .admin_panel import db

ADMIN_ID = 1733124290


@Client.on_message(filters.command("daily"))
async def daily_cmd(client, message):

    if len(message.command) < 2:
        return await message.reply(
            "Usage:\n/daily 30\n/daily bonus"
        )

    daily_type = message.command[1].lower()

    if daily_type not in ["30", "bonus"]:
        return await message.reply(
            "Use /daily 30 or /daily bonus"
        )

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else message.from_user.first_name
    )

    await db.mark_daily(
        message.from_user.id,
        username,
        daily_type
    )

    await message.reply("✅ Recorded")


async def daily_report_loop():
    ist = pytz.timezone("Asia/Kolkata")

    while True:
        now = datetime.now(ist)

        if now.hour == 18 and now.minute == 0:
            users = await db.get_daily()

            text = (
                f"📊 Daily Report\n\n"
                f"👥 Total Users: {len(users)}\n\n"
            )

            for user in users:
                text += (
                    f"{user.get('username')}\n"
                    f"🆔 `{user['user_id']}`\n"
                    f"30: {'✅' if user.get('30') else '❌'}\n"
                    f"Bonus: {'✅' if user.get('bonus') else '❌'}\n\n"
                )

            await bot.send_message(
                ADMIN_ID,
                text
            )

            await asyncio.sleep(65)

        await asyncio.sleep(20)


async def daily_reset_loop():

    ist = pytz.timezone("Asia/Kolkata")

    while True:

        now = datetime.now(ist)

        if now.hour == 0 and now.minute == 0:

            await db.reset_daily()

            await asyncio.sleep(65)

        await asyncio.sleep(20)
        

@Client.on_message(filters.command("status") & filters.user(ADMIN_ID))
async def status_cmd(client, message):
    users = await db.get_daily()

    text = (
        f"📊 Daily Report\n\n"
        f"👥 Total Users: {len(users)}\n\n"
    )

    for user in users:
        text += (
            f"{user.get('username')}\n"
            f"🆔 `{user['user_id']}`\n"
            f"30: {'✅' if user.get('30') else '❌'}\n"
            f"Bonus: {'✅' if user.get('bonus') else '❌'}\n\n"
        )

    await message.reply(text)



REPORT_LOOP_RUNNING = False


@Client.on_message(filters.command("startreport") & filters.user(ADMIN_ID))
async def start_report(client, message):
    global REPORT_LOOP_RUNNING

    if REPORT_LOOP_RUNNING:
        return await message.reply(
            "⚠️ Report loop already running."
        )

    REPORT_LOOP_RUNNING = True

    asyncio.create_task(
        daily_report_loop()
    )

    asyncio.create_task(
        daily_reset_loop()
    )

    await message.reply(
        "✅ Daily report loop started."
    )
