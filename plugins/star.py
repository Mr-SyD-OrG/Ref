from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
BOT_TOKEN = Config.BOT_TOKEN

ADMIN_ID = 1733124290  # Replace with your Telegram ID

from pyrogram import Client, filters
#from pyromod import listen
import aiohttp
from uuid import uuid4


@Client.on_message(filters.command("star") & filters.private)
async def star_cmd(client, message):
    ask = await client.ask(
        message.chat.id,
        "⭐ Enter amount of Stars (1-2500):",
        timeout=120
    )

    if not ask.text.isdigit():
        return await message.reply(
            "❌ Please enter a valid number."
        )

    amount = int(ask.text)

    if not 1 <= amount <= 2500:
        return await message.reply(
            "❌ Amount must be between 1 and 2500."
        )

    try:
        payload = f"stars_{message.from_user.id}_{amount}_{uuid4().hex}"

        async with aiohttp.ClientSession() as session:
            r = await session.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice",
                json={
                    "chat_id": message.chat.id,
                    "title": f"{amount} Telegram Stars",
                    "description": (
                        f"Purchase {amount} Telegram Stars"
                    ),
                    "payload": payload,
                    "currency": "XTR",
                    "provider_token": "",
                    "prices": [
                        {
                            "label": "XTR",
                            "amount": amount
                        }
                    ]
                }
            )

            data = await r.json()

        if not data.get("ok"):
            return await message.reply(
                f"❌ Invoice Error\n\n"
                f"`{data}`"
            )

    except Exception as e:
        await message.reply(
            f"❌ Error\n\n`{e}`"
        )


@Client.on_pre_checkout_query()
async def pre_checkout(client, query):
    try:
        await query.answer(True)

        await client.send_message(
            ADMIN_ID,
            "✅ PRECHECKOUT ANSWERED"
        )

    except Exception as e:
        await client.send_message(
            ADMIN_ID,
            f"❌ PRECHECKOUT ERROR\n\n`{e}`"
        )


@Client.on_message(filters.successful_payment)
async def successful_payment(client, message):
    payment = message.successful_payment

    await message.reply(
        "✅ Payment successful!\n\n"
        f"⭐ Amount: {payment.total_amount}\n"
        f"🧾 Charge ID:\n"
        f"`{payment.telegram_payment_charge_id}`"
    )

    await client.send_message(
        ADMIN_ID,
        f"💰 New Stars Purchase\n\n"
        f"👤 User: {message.from_user.mention}\n"
        f"🆔 ID: `{message.from_user.id}`\n"
        f"⭐ Amount: {payment.total_amount}\n"
        f"🧾 Charge ID:\n"
        f"`{payment.telegram_payment_charge_id}`"
    )


@Client.on_message(filters.command("checkpre"))
async def checkpre(client, message):
    from pyrogram.types import PreCheckoutQuery
    import inspect
    await message.reply(
        f"`{inspect.signature(PreCheckoutQuery.answer)}`"
    )

@Client.on_message(filters.command("balance") & filters.user(ADMIN_ID))
async def balance_cmd(client, message):
    async with aiohttp.ClientSession() as session:
        r = await session.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getMyStarBalance"
        )

        data = await r.json()

    if not data.get("ok"):
        return await message.reply(
            f"❌ Error\n\n`{data}`"
        )

    balance = data["result"]["amount"]

    await message.reply(
        f"⭐ Star Balance: `{balance}`"
    )



async def get_available_gifts():
    async with aiohttp.ClientSession() as session:
        r = await session.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getAvailableGifts"
        )
        return await r.json()


async def send_gift(user_id, gift_id):
    async with aiohttp.ClientSession() as session:
        r = await session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendGift",
            json={
                "user_id": user_id,
                "gift_id": gift_id
            }
        )
        return await r.json()


@Client.on_message(filters.command("gift") & filters.user(ADMIN_ID))
async def gift_cmd(client, message):
    try:
        ask = await client.ask(
            message.chat.id,
            "🎁 Send target user ID:",
            timeout=120
        )

        if not ask.text.isdigit():
            return await message.reply("❌ Invalid ID")

        target_id = int(ask.text)

        data = await get_available_gifts()

        if not data.get("ok"):
            return await message.reply(
                f"❌ Failed to fetch gifts\n\n`{data}`"
            )

        gifts = data["result"]["gifts"]

        txt = (
            f"🎯 Target: `{target_id}`\n\n"
            "Available Gifts:\n\n"
        )

        gift_map = {}

        for i, gift in enumerate(gifts, start=1):
            gift_id = gift["id"]
            stars = gift.get("star_count", "?")

            gift_map[str(i)] = gift_id

            txt += (
                f"`{i}` → Gift ID: `{gift_id}` "
                f"({stars}⭐)\n"
            )

        txt += "\nSend the number of the gift to send."

        choose = await client.ask(
            message.chat.id,
            txt,
            timeout=300
        )

        if choose.text not in gift_map:
            return await message.reply(
                "❌ Invalid selection"
            )

        selected_gift = gift_map[choose.text]

        confirm = await client.ask(
            message.chat.id,
            f"⚠️ Confirm sending gift?\n\n"
            f"Target: `{target_id}`\n"
            f"Gift: `{selected_gift}`\n\n"
            f"Reply with `YES`",
            timeout=120
        )

        if confirm.text.upper() != "YES":
            return await message.reply(
                "❌ Cancelled"
            )

        result = await send_gift(
            user_id=target_id,
            gift_id=selected_gift
        )

        await message.reply(
            f"📨 Result:\n\n`{result}`"
        )

    except Exception as e:
        await message.reply(
            f"❌ Error\n\n`{e}`"
    )
