from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError,
    PhoneNumberInvalidError,
    FloodWaitError
)


from pyrogram import Client, filters

@Client.on_message(filters.command("generate") & filters.private)
async def generate_cmd(bot, message):
    await generate_session(bot, message)
  
async def cancelled(message):
    if "/cancel" in message.text:
        await message.reply_text(
            "**Cancelled the ongoing string generation process.**"
        )
        return True
    return False


async def generate_session(bot, message):
    user_id = message.from_user.id

    try:
        phone = await bot.ask(
            user_id,
            "Send your phone number with country code.\n\nExample: `+911234567890`",
            timeout=300
        )
    except ListenerTimeout:
        return await bot.send_message(
            user_id,
            "Timed out after 5 minutes."
        )

    if await cancelled(phone):
        return

    phone = phone.text.strip()

    client = TelegramClient(
        StringSession(),
        Config.API_ID,
        Config.API_HASH
    )

    await client.connect()

    try:
        sent = await client.send_code_request(phone)

    except FloodWaitError as e:
        return await bot.send_message(
            user_id,
            f"FloodWait: Wait {e.seconds} seconds."
        )

    except PhoneNumberInvalidError:
        return await bot.send_message(
            user_id,
            "Invalid phone number."
        )

    await bot.send_message(
        user_id,
        "OTP sent.\n\nSend it like:\n`1 2 3 4 5`"
    )

    try:
        otp = await bot.ask(
            user_id,
            "Enter OTP:",
            timeout=600
        )
    except ListenerTimeout:
        return await bot.send_message(
            user_id,
            "Timed out after 10 minutes."
        )

    if await cancelled(otp):
        return

    otp = otp.text.replace(" ", "")

    try:
        await client.sign_in(
            phone=phone,
            code=otp,
            phone_code_hash=sent.phone_code_hash
        )

    except PhoneCodeInvalidError:
        return await bot.send_message(
            user_id,
            "Wrong OTP."
        )

    except PhoneCodeExpiredError:
        return await bot.send_message(
            user_id,
            "OTP expired."
        )

    except SessionPasswordNeededError:

        try:
            pwd = await bot.ask(
                user_id,
                "2-Step Verification enabled.\nSend password:",
                timeout=300
            )
        except ListenerTimeout:
            return await bot.send_message(
                user_id,
                "Timed out after 5 minutes."
            )

        if await cancelled(pwd):
            return

        try:
            await client.sign_in(
                password=pwd.text
            )

        except PasswordHashInvalidError:
            return await bot.send_message(
                user_id,
                "Wrong password."
            )

    except Exception as e:
        return await bot.send_message(
            user_id,
            f"Error:\n`{e}`"
        )

    string_session = client.session.save()

    await bot.send_message(
        user_id,
        f"**Telethon String Session:**\n\n`{string_session}`"
    )

    await client.disconnect()
