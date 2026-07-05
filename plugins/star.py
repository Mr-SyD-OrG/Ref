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
