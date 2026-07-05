from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


ADMIN_ID = 1733124290  # Replace with your Telegram ID

# Store pending payments
PENDING_STARS = {}


@Client.on_message(filters.command("star") & filters.private)
async def star_cmd(client, message):
    ask = await client.ask(
        message.chat.id,
        "⭐ Enter the number of stars you want to purchase:",
        timeout=120
    )

    if not ask.text.isdigit():
        return await message.reply("❌ Please enter a valid number.")

    stars = int(ask.text)

    purchase_msg = await message.reply_invoice(
        title=f"{stars} Telegram Stars",
        description=f"Purchase of {stars} Telegram Stars",
        currency="XTR",
        prices=[{"label": f"{stars} Stars", "amount": stars}],
        payload=f"stars_{message.from_user.id}_{stars}"
    )

    PENDING_STARS[f"stars_{message.from_user.id}_{stars}"] = {
        "user_id": message.from_user.id,
        "stars": stars
    }


@Client.on_pre_checkout_query()
async def pre_checkout(client, query):
    await query.answer(ok=True)


@Client.on_message(filters.successful_payment)
async def payment_success(client, message):
    payload = message.successful_payment.invoice_payload

    data = PENDING_STARS.get(payload)
    if not data:
        return

    user = message.from_user

    await message.reply(
        f"✅ Payment received!\n\n"
        f"⭐ Stars: {data['stars']}"
    )

    await client.send_message(
        ADMIN_ID,
        f"💰 New Star Purchase\n\n"
        f"👤 User: {user.mention}\n"
        f"🆔 ID: `{user.id}`\n"
        f"⭐ Amount: {data['stars']}"
    )

    PENDING_STARS.pop(payload, None)
