from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyromod import listen
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB

from motor.motor_asyncio import AsyncIOMotorClient


class Database:

    def __init__(self, uri):

        self.mongo = AsyncIOMotorClient(uri)
        self.db = self.mongo["bot"]

        self.users = self.db["verified_users"]
        self.accounts = self.db["accounts"]
        self.referrals = self.db["referrals"]

    # -----------------
    # VERIFIED USERS
    # -----------------

    async def is_verified(self, user_id):

        return await self.users.find_one(
            {"user_id": user_id}
        ) is not None

    async def add_verified(self, user_id):

        await self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id
                }
            },
            upsert=True
        )

    async def remove_verified(self, user_id):

        return await self.users.delete_one(
            {"user_id": user_id}
        )

    async def get_verified(self):

        return await self.users.find().to_list(
            length=None
        )

    # -----------------
    # ACCOUNTS
    # -----------------

    async def add_account(
        self,
        acc_id,
        api_id,
        api_hash,
        session,
        url
    ):

        await self.accounts.insert_one(
            {
                "acc_id": acc_id,
                "api_id": api_id,
                "api_hash": api_hash,
                "session": session,
                "url": url,
                "paused": False,
                "total_ref": 0,
                "valid_ref": 0,
                "reref": 0
            }
        )

    async def get_account(self, acc_id):

        return await self.accounts.find_one(
            {"acc_id": acc_id}
        )

    async def get_accounts(self):

        return await self.accounts.find().to_list(
            length=None
        )

    async def get_active_accounts(self):

        return await self.accounts.find(
            {"paused": False}
        ).to_list(length=None)

    async def pause_account(
        self,
        acc_id,
        paused
    ):

        await self.accounts.update_one(
            {"acc_id": acc_id},
            {
                "$set": {
                    "paused": paused
                }
            }
        )

    async def delete_account(self, acc_id):

        await self.accounts.delete_one(
            {"acc_id": acc_id}
        )

        await self.referrals.delete_many(
            {"acc_id": acc_id}
        )

    # -----------------
    # REFERRALS
    # -----------------

    async def add_referral(
        self,
        acc_id,
        name,
        stars,
        valid,
        timestamp
    ):

        await self.referrals.insert_one(
            {
                "acc_id": acc_id,
                "name": name,
                "stars": stars,
                "valid": valid,
                "timestamp": timestamp
            }
        )

        update = {
            "$inc": {
                "total_ref": 1
            }
        }

        if valid:
            update["$inc"]["valid_ref"] = 1
        else:
            update["$inc"]["reref"] = 1

        await self.accounts.update_one(
            {"acc_id": acc_id},
            update
        )

    async def get_referrals(self, acc_id):

        return await self.referrals.find(
            {"acc_id": acc_id}
        ).to_list(length=None)

    async def latest_referral(self, acc_id):

        return await self.referrals.find_one(
            {"acc_id": acc_id},
            sort=[("timestamp", -1)]
        )
        
ADMINS = [123456789]  # Admin IDs


from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


@Client.on_message(filters.command("users"))
async def users_cmd(client, message):
    user_id = message.from_user.id

    if user_id not in ADMINS:
        return await message.reply(
            "❌ Admin only."
        )

    await message.reply(
        "User Management",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➕ To Add",
                        callback_data="add_user"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "➖ To Remove",
                        callback_data="remove_user"
                    )
                ]
            ]
        )
    )


@Client.on_callback_query(filters.regex("^add_user$"))
async def add_user(client, query):

    if query.from_user.id not in ADMINS:
        return await query.answer(
            "Not allowed",
            show_alert=True
        )

    await query.message.reply(
        "Send User ID to verify:"
    )

    reply = await client.listen(
        chat_id=query.message.chat.id,
        user_id=query.from_user.id
    )

    try:
        user_id = int(reply.text.strip())

    except Exception:
        return await query.message.reply(
            "Invalid User ID."
        )

    if await db.is_verified(user_id):

        return await query.message.reply(
            f"`{user_id}` is already verified."
        )

    await db.add_verified(user_id)

    await query.message.reply(
        f"✅ Verified User\n\n"
        f"`{user_id}`"
    )


@Client.on_callback_query(filters.regex("^remove_user$"))
async def remove_user(client, query):

    if query.from_user.id not in ADMINS:
        return await query.answer(
            "Not allowed",
            show_alert=True
        )

    users = await db.get_verified()

    if not users:

        return await query.message.reply(
            "No verified users found."
        )

    text = "Verified Users\n\n"

    for user in users:

        text += (
            f"`{user['user_id']}`\n"
        )

    text += "\nSend User ID to remove:"

    await query.message.reply(text)

    reply = await client.listen(
        chat_id=query.message.chat.id,
        user_id=query.from_user.id
    )

    try:
        user_id = int(reply.text.strip())

    except Exception:
        return await query.message.reply(
            "Invalid User ID."
        )

    result = await db.remove_verified(
        user_id
    )

    if result.deleted_count:

        await query.message.reply(
            f"✅ Removed User\n\n"
            f"`{user_id}`"
        )

    else:

        await query.message.reply(
            "User ID not found."
    )






from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import random

ADMINS = [123456789]


def generate_acc_id():
    return str(random.randint(100000, 999999))


@Client.on_message(filters.command("accounts"))
async def accounts_cmd(client, message):

    if message.from_user.id not in ADMINS:
        return await message.reply("❌ Admin only.")

    accounts = await db.get_accounts()

    buttons = [
        [
            InlineKeyboardButton(
                "➕ Add Account",
                callback_data="add_account"
            )
        ]
    ]

    for acc in accounts:

        status = (
            "⏸"
            if acc.get("paused")
            else "▶️"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    f"{status} {acc['acc_id']}",
                    callback_data=f"acc_{acc['acc_id']}"
                )
            ]
        )

    await message.reply(
        f"📱 Accounts: {len(accounts)}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^add_account$"))
async def add_account(client, query):

    if query.from_user.id not in ADMINS:
        return

    msg = query.message

    await msg.reply("Send API ID:")
    api_id = (
        await client.listen(
            chat_id=msg.chat.id,
            user_id=query.from_user.id
        )
    ).text.strip()

    await msg.reply("Send API HASH:")
    api_hash = (
        await client.listen(
            chat_id=msg.chat.id,
            user_id=query.from_user.id
        )
    ).text.strip()

    await msg.reply("Send SESSION STRING:")
    session = (
        await client.listen(
            chat_id=msg.chat.id,
            user_id=query.from_user.id
        )
    ).text.strip()

    await msg.reply("Send URL:")
    url = (
        await client.listen(
            chat_id=msg.chat.id,
            user_id=query.from_user.id
        )
    ).text.strip()

    while True:

        acc_id = generate_acc_id()

        if not await db.get_account(acc_id):
            break

    await db.add_account(
        acc_id=acc_id,
        api_id=int(api_id),
        api_hash=api_hash,
        session=session,
        url=url
    )

    await msg.reply(
        f"✅ Account Added\n\n"
        f"ID: `{acc_id}`"
    )


@Client.on_callback_query(filters.regex(r"^acc_(.+)$"))
async def account_view(client, query):

    if query.from_user.id not in ADMINS:
        return

    acc_id = query.data.split("_", 1)[1]

    acc = await db.get_account(acc_id)

    if not acc:

        return await query.message.reply(
            "Account not found."
        )

    status = (
        "⏸ Paused"
        if acc.get("paused")
        else "▶️ Active"
    )

    text = (
        f"📱 Account: `{acc_id}`\n\n"
        f"Status: {status}\n\n"
        f"🔗 URL:\n{acc.get('url', 'N/A')}\n\n"
        f"📊 Statistics\n"
        f"Total: {acc.get('total_ref', 0)}\n"
        f"Valid: {acc.get('valid_ref', 0)}\n"
        f"Re-Refer: {acc.get('reref', 0)}"
    )

    await query.message.reply(
        text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⏸ Pause/Resume",
                        callback_data=f"toggle_{acc_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🗑 Delete",
                        callback_data=f"delete_{acc_id}"
                    )
                ]
            ]
        )
    )






import asyncio
import re

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from datetime import datetime
from zoneinfo import ZoneInfo

RUNNING_ACCOUNTS = {}

BOT_ID = 123456789
LOG_CHANNEL = -1001234567890


async def start_account(acc):

    acc_id = acc["acc_id"]

    if acc_id in RUNNING_ACCOUNTS:
        return False

    try:

        tg_client = TelegramClient(
            StringSession(acc["session"]),
            acc["api_id"],
            acc["api_hash"]
        )

        await tg_client.start()

        RUNNING_ACCOUNTS[acc_id] = tg_client

        @tg_client.on(
            events.NewMessage(
                from_users=BOT_ID
            )
        )
        async def referral_handler(event):

            text = event.raw_text

            m = re.search(
                r"\+(\d+)⭐️,\s*(.*?)\s+активировал",
                text
            )

            if not m:
                return

            stars = int(m.group(1))
            name = m.group(2).strip()

            valid = stars >= 3

            now = datetime.now(
                ZoneInfo("Asia/Kolkata")
            )

            await db.add_referral(
                acc_id=acc_id,
                name=name,
                stars=stars,
                valid=valid,
                timestamp=now.timestamp()
            )

            status = (
                "✅ Valid Refer"
                if valid
                else "♻️ Re-Refer"
            )

            ist_time = now.strftime(
                "%d-%m-%Y %I:%M:%S %p"
            )

            await app.send_message(
                LOG_CHANNEL,
                f"📱 Account: {acc_id}\n"
                f"👤 Name: {name}\n"
                f"⭐ Stars: +{stars}\n"
                f"📌 Status: {status}\n"
                f"🕒 IST: {ist_time}"
            )

        asyncio.create_task(
            tg_client.run_until_disconnected()
        )

        return True

    except Exception as e:

        print(
            f"Failed to start {acc_id}: {e}"
        )

        return False


async def start_all_accounts():

    accounts = await db.get_active_accounts()

    started = 0

    for acc in accounts:

        if await start_account(acc):
            started += 1

    return started

from pyrogram import Client, filters

@Client.on_message(
    filters.command("startacc")
)
async def startacc_cmd(client, message):

    if message.from_user.id not in ADMINS:
        return

    count = await start_all_accounts()

    await message.reply(
        f"✅ Started {count} account(s)\n\n"
        f"Running: {len(RUNNING_ACCOUNTS)}"
    )




@Client.on_callback_query(filters.regex(r"^delete_(.+)$"))
async def delete_account(client, query):

    if query.from_user.id not in ADMINS:
        return

    acc_id = query.data.split("_", 1)[1]

    tg_client = RUNNING_ACCOUNTS.get(
        acc_id
    )

    if tg_client:

        try:

            await tg_client.disconnect()

        except Exception:
            pass

        RUNNING_ACCOUNTS.pop(
            acc_id,
            None
        )

    await db.delete_account(acc_id)

    await query.message.reply(
        f"🗑 Account Deleted\n\n"
        f"ID: `{acc_id}`"
    )

    await query.answer()


@Client.on_callback_query(filters.regex(r"^toggle_(.+)$"))
async def toggle_account(client, query):

    if query.from_user.id not in ADMINS:
        return

    acc_id = query.data.split("_", 1)[1]

    acc = await db.get_account(acc_id)

    if not acc:

        return await query.answer(
            "Account not found",
            show_alert=True
        )

    new_state = not acc["paused"]

    await db.pause_account(
        acc_id,
        new_state
    )

    if new_state:

        tg_client = RUNNING_ACCOUNTS.get(
            acc_id
        )

        if tg_client:

            try:

                await tg_client.disconnect()

            except Exception:
                pass

            RUNNING_ACCOUNTS.pop(
                acc_id,
                None
            )

        text = "⏸ Account Paused"

    else:

        asyncio.create_task(
            start_account(acc)
        )

        text = "▶️ Account Resumed"

    await query.answer(
        text,
        show_alert=True
    )
