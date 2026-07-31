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
    flag = True

    if daily_type == "faltsk":
        daily_type = "task"
        flag = False

    if daily_type not in ["30", "bonus", "task", "dstart"]:
        return await message.reply(
            "Use /daily 30, /daily bonus, /daily task, /daily dstart or /daily faltsk"
        )

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else message.from_user.first_name
    )

    await db.mark_daily(
        message.from_user.id,
        username,
        daily_type,
        flag
    )

    await message.reply("✅ Recorded")


last_report_date = None

async def daily_oreport_loop(bot):
    global last_report_date

    ist = pytz.timezone("Asia/Kolkata")

    while True:
        now = datetime.now(ist)

        if (
            now.hour >= 18
            and last_report_date != now.date()
        ):

            last_report_date = now.date()
            users = await db.get_daily()

            text = (
                f"📊 Daily Report\n\n"
                f"👥 Total Users: {len(users)}\n\n"
            )

            for user in users:
                text += (
                    f"{user.get('username')}\n"
                    f"🆔 `{user['user_id']}`\n"
                    f"Start: {'✅' if user.get('dstart') else '❌'}\n"
                    f"End 30: {'✅' if user.get('30') else '❌'}\n"
                    f"Task: {'✅' if user.get('task') else '❌'}\n"
                    f"Bonus: {'✅' if user.get('bonus') else '❌'}\n\n"
                )

            await bot.send_message(
                ADMIN_ID,
                text
            )
            last_report_date = now.date()

            await asyncio.sleep(65)

        await asyncio.sleep(20)


last_reset_date = None

async def daily_reset_loop(bot):
    global last_reset_date

    ist = pytz.timezone("Asia/Kolkata")

    while True:
        now = datetime.now(ist)

        if (
            now.hour == 3
            and last_reset_date != now.date()
        ):
            await send_daily_report(bot)
            await db.reset_daily()

            last_reset_date = now.date()

        await asyncio.sleep(20)

async def send_daily_report(bot):
    users = await db.get_daily()

    text = (
        f"📊 Daily Report\n\n"
        f"👥 Total Users: {len(users)}\n\n"
    )

    for user in users:
        text += (
            f"{user.get('username')}\n"
            f"🆔 `{user['user_id']}`\n"
            f"Start: {'✅' if user.get('dstart') else '❌'}\n"
            f"End 30: {'✅' if user.get('30') else '❌'}\n"
            f"Task: {'✅' if user.get('task') else '❌'}\n"
            f"Bonus: {'✅' if user.get('bonus') else '❌'}\n\n"
        )

    await bot.send_message(ADMIN_ID, text)
    
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
            f"Start: {'✅' if user.get('dstart') else '❌'}\n"
            f"End 30: {'✅' if user.get('30') else '❌'}\n"
            f"Task: {'✅' if user.get('task') else '❌'}\n"
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
        daily_report_loop(client)
    )
    asyncio.create_task(
        daily_oreport_loop(client)
    )
    asyncio.create_task(
        daily_reset_loop(client)
    )

    await message.reply(
        "✅ Daily report loop started."
    )
