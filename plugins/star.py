from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


ADMIN_ID = 1733124290  # Replace with your Telegram ID

from pyrogram import Client, filters
from pyrogram.types import (
    LabeledPrice,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)



from pyrogram import Client, filters
from pyrogram.types import LabeledPrice
#from pyromod import listen
  # Replace with your Telegram ID


@Client.on_message(filters.command("star") & filters.private)
async def star_cmd(client, message):
    try:
        ask = await client.ask(
            message.chat.id,
            "⭐ Enter the number of Stars:",
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
            await client.send_invoice(
                chat_id=message.chat.id,
                title=f"{amount} Telegram Stars",
                description=f"Purchase {amount} Telegram Stars",
                payload=f"stars_{message.from_user.id}_{amount}",
                currency="XTR",
                prices=[
                    LabeledPrice(
                        label="XTR",
                        amount=amount
                    )
                ],
                provider_token=""
            )

        except Exception as e:
            await message.reply(
                f"❌ Invoice Error\n\n"
                f"Type: `{type(e).__name__}`\n\n"
                f"`{repr(e)}`"
            )

    except Exception as e:
        await message.reply(
            f"❌ Handler Error\n\n"
            f"Type: `{type(e).__name__}`\n\n"
            f"`{repr(e)}`"
        )


@Client.on_pre_checkout_query()
async def pre_checkout(_, query):
    try:
        await query.answer(ok=True)
    except Exception as e:
        print(f"PreCheckout Error: {e}")


@Client.on_message(filters.successful_payment)
async def successful_payment(client, message):
    try:
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

    except Exception as e:
        await message.reply(
            f"❌ Payment Error\n\n"
            f"`{repr(e)}`"
        )
