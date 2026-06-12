from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyromod import listen
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
# MongoDB
from pyrogram.errors import MessageNotModified


from motor.motor_asyncio import AsyncIOMotorClient
ADMINS = Config.ADMINS
RUNNING_ACCOUNTS = {}
BOT_ID = 7996790736
LOG_CHANNEL = Config.LOG_CHANNEL


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
        url,
        max_ref
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
                "reref": 0,
                "max_ref": max_ref,
                "owner_id": None,
            }
        )

    async def get_account(self, acc_id):

        return await self.accounts.find_one(
            {"acc_id": acc_id}
        )

    async def assign_account(self, acc_id, user_id):

        await self.accounts.update_one(
            {"acc_id": acc_id},
            {
                "$set": {
                    "owner_id": user_id
                }
            }
        )

    async def get_user_accounts(self, user_id):

        return await self.accounts.find({"owner_id": user_id}).to_list(length=None)

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
        

db = Database(Config.DB_URL)


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

    await msg.reply("Max Ref:")
    max_ref = (
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
        url=url,
        max_ref=max_ref
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
        f"👤 Owner: `{acc.get('owner_id', 'None')}`\n"
    )

    await query.message.reply(
        text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏸ Pause/Resume", callback_data=f"toggle_{acc_id}")],
            [InlineKeyboardButton("👤 Assign User", callback_data=f"assign_{acc_id}")],
            [InlineKeyboardButton("📊 Manage Refers", callback_data=f"manageref_{acc_id}")],
            [InlineKeyboardButton("🔢 Change Max Ref", callback_data=f"maxref_{acc_id}")],
            [InlineKeyboardButton("🗑 Delete", callback_data=f"delete_{acc_id}")]
        ])
    )


@Client.on_callback_query(filters.regex(r"^assign_(.+)$"))
async def assign_user(client, query):

    if query.from_user.id not in ADMINS:
        return

    acc_id = query.data.split("_", 1)[1]

    await query.message.reply(
        "Send verified user ID:"
    )

    reply = await client.listen(
        chat_id=query.message.chat.id,
        user_id=query.from_user.id
    )

    try:
        user_id = int(reply.text)

    except:
        return await query.message.reply(
            "Invalid user ID."
        )

    if not await db.is_verified(user_id):

        return await query.message.reply(
            "User is not verified."
        )

    await db.assign_account(
        acc_id,
        user_id
    )

    await query.message.reply(
        f"✅ Assigned\n\n"
        f"Account: `{acc_id}`\n"
        f"User: `{user_id}`"
    )
    
@Client.on_callback_query(filters.regex(r"^maxref_(.+)$"))
async def change_max_ref(client, query):

    if query.from_user.id not in ADMINS:
        return

    acc_id = query.data.split("_", 1)[1]

    acc = await db.get_account(acc_id)

    if not acc:
        return await query.message.reply(
            "Account not found."
        )

    await query.message.reply(
        f"Current Max Ref: {acc.get('max_ref', 0)}\n\n"
        "Send new maximum referral count:"
    )

    reply = await client.listen(
        chat_id=query.message.chat.id,
        user_id=query.from_user.id
    )

    try:
        new_max = int(reply.text)

    except Exception:
        return await query.message.reply(
            "Invalid number."
        )

    await db.accounts.update_one(
        {"acc_id": acc_id},
        {
            "$set": {
                "max_ref": new_max
            }
        }
    )

    await query.message.reply(
        f"✅ Max Ref updated\n\n"
        f"Account: `{acc_id}`\n"
        f"New Limit: `{new_max}`"
    )
    
@Client.on_callback_query(filters.regex(r"^manageref_(.+)$"))
async def manage_refers(client, query):

    if query.from_user.id not in ADMINS:
        return

    acc_id = query.data.split("_", 1)[1]

    await query.message.reply(
        f"Manage Referrals\n\n"
        f"Account: `{acc_id}`",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🗑 Remove All",
                        callback_data=f"delallref_{acc_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🗑 Remove One",
                        callback_data=f"deloneref_{acc_id}"
                    )
                ]
            ]
        )
    )

@Client.on_callback_query(filters.regex(r"^delallref_(.+)$"))
async def delete_all_refers(client, query):

    if query.from_user.id not in ADMINS:
        return

    acc_id = query.data.split("_", 1)[1]

    await db.referrals.delete_many(
        {"acc_id": acc_id}
    )

    await db.accounts.update_one(
        {"acc_id": acc_id},
        {
            "$set": {
                "total_ref": 0,
                "valid_ref": 0,
                "reref": 0
            }
        }
    )

    await query.message.reply(
        f"✅ All referrals removed from `{acc_id}`"
    )


@Client.on_callback_query(filters.regex(r"^deloneref_(.+)$"))
async def delete_one_ref_menu(client, query):

    if query.from_user.id not in ADMINS:
        return

    acc_id = query.data.split("_", 1)[1]

    refs = await db.get_referrals(acc_id)

    if not refs:
        return await query.message.reply(
            "No referrals found."
        )

    text = ""

    for i, ref in enumerate(refs, start=1):

        status = (
            "Valid"
            if ref["valid"]
            else "Re"
        )

        text += (
            f"{i}. {ref['name']} "
            f"(+{ref['stars']}) "
            f"[{status}]\n"
        )

    text += "\nSend referral number to remove."

    await query.message.reply(text)

    reply = await client.listen(
        chat_id=query.message.chat.id,
        user_id=query.from_user.id
    )

    try:
        index = int(reply.text)

    except Exception:

        return await query.message.reply(
            "Invalid number."
        )

    if index < 1 or index > len(refs):

        return await query.message.reply(
            "Out of range."
        )

    ref = refs[index - 1]

    await db.referrals.delete_one(
        {"_id": ref["_id"]}
    )

    update = {
        "$inc": {
            "total_ref": -1
        }
    }

    if ref["valid"]:

        update["$inc"]["valid_ref"] = -1

    else:

        update["$inc"]["reref"] = -1

    await db.accounts.update_one(
        {"acc_id": acc_id},
        update
    )

    await query.message.reply(
        f"✅ Removed Referral\n\n"
        f"👤 {ref['name']}\n"
        f"⭐ +{ref['stars']}"
        )

import asyncio
import re

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from datetime import datetime
from zoneinfo import ZoneInfo



async def start_account(client, acc):

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
                from_users=BOT_ID,
                pattern=r"(?i)(✅ Ты заработал(а)|✅ Пользователь)"
            )
        )
        async def referral_handler(event):

            text = event.raw_text

            m = re.search(
                r"\+(\d+)⭐️,\s*(.*?)\s+активировал",
                text
            )

            if m:

                stars = int(m.group(1))
                name = m.group(2).strip()

            else:

                m = re.search(
                r"Пользователь\s+(@[^\s]+).*?\+(\d+)⭐️",
                text
                )

                if not m:
                    return

                name = m.group(1)
                stars = int(m.group(2))

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

            await client.send_message(
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


async def start_all_accounts(client):

    accounts = await db.get_active_accounts()

    started = 0

    for acc in accounts:

        if await start_account(client, acc):
            started += 1

    return started

from pyrogram import Client, filters

@Client.on_message(
    filters.command("startacc")
)
async def startacc_cmd(client, message):

    if message.from_user.id not in ADMINS:
        return

    count = await start_all_accounts(client)

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
            start_account(client, acc)
        )

        text = "▶️ Account Resumed"

    await query.answer(
        text,
        show_alert=True
    )



from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from datetime import datetime
from zoneinfo import ZoneInfo


@Client.on_message(filters.command("refer"))
async def refer_cmd(client, message):

    user_id = message.from_user.id

    if (
        user_id not in ADMINS
        and not await db.is_verified(user_id)
    ):
        return await message.reply(
            "❌ Access denied."
        )

    if user_id in ADMINS:
        accounts = await db.get_accounts()
    else:
        accounts = await db.get_user_accounts(user_id)
    if not accounts:
        return await message.reply(
            "No accounts found."
        )

    buttons = []

    for acc in accounts:

        buttons.append(
            [
                InlineKeyboardButton(
                    f"📱 {acc['acc_id']}",
                    callback_data=f"ref_{acc['acc_id']}"
                )
            ]
        )

    await message.reply(
        "Select Account",
        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


@Client.on_callback_query(filters.regex(r"^ref_(.+)$"))
async def refer_account(client, query):

    user_id = query.from_user.id

    if (user_id not in ADMINS and acc.get("owner_id") != user_id):
        return await query.answer("Access denied.", show_alert=True)

    acc_id = query.data.split(
        "_",
        1
    )[1]

    acc = await db.get_account(
        acc_id
    )

    if not acc:

        return await query.message.reply(
            "Account not found."
        )

    valid_ref = int(acc.get("valid_ref", 0))
    max_ref = int(acc.get("max_ref", 4))
    paused = acc.get("paused", False)
    if paused:

        text = (
            f"📱 Account: `{acc_id}`\n\n"
            f"⏸ Account Paused\n"
            f"❌ Don't refer now.\n\n"
            f"🍃 Valid Ref: {valid_ref}\n"
            f"⚠️ Maximum Ref: {max_ref}"
        )

    elif valid_ref >= max_ref:

        text = (
            f"📱 Account: `{acc_id}`\n\n"
            f"🔒 Link Hidden\n"
            f"Maximum Valid Referrals Reached.\n"
            f"Please withdraw the amount.\n\n"
            f"🍃 Valid Ref: {valid_ref}\n"
            f"⚠️ Maximum Ref: {max_ref}"
        )

    else:

        text = (
            f"📱 Account: `{acc_id}`\n\n"
            f"🔗 Link:\n"
            f"{acc['url']}\n\n"
            f"🍃 Valid Ref: {valid_ref}\n"
            f"⚠️ Maximum Ref: {max_ref}"
        )

    try:
        await query.message.edit(
            text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 All Refer", callback_data=f"allref_{acc_id}")],
                [InlineKeyboardButton("🆕 Latest Refer", callback_data=f"latestref_{acc_id}")],
                [InlineKeyboardButton("📊 Counts", callback_data=f"countref_{acc_id}")]
            ])
        )
    except MessageNotModified:
        pass
    except Exception as e:
        await client.send_message(1733124290, f"E: {e}")


#@Client.on_callback_query(filters.regex(r"^countref_(.+)$"))
async def referral_xcount(client, query):

    acc_id = query.data.split(
        "_",
        1
    )[1]

    acc = await db.get_account(
        acc_id
    )

    if not acc:

        return await query.message.reply(
            "Account not found."
        )

    await query.message.reply(
        f"📊 Statistics\n\n"
        f"Account: `{acc_id}`\n\n"
        f"Total: {acc.get('total_ref', 0)}\n"
        f"Valid: {acc.get('valid_ref', 0)}\n"
        f"Re-Refer: {acc.get('reref', 0)}"
    )


@Client.on_callback_query(filters.regex(r"^latestref_(.+)$"))
async def latest_ref(client, query):

    acc_id = query.data.split(
        "_",
        1
    )[1]

    ref = await db.latest_referral(
        acc_id
    )

    if not ref:

        return await query.message.reply(
            "No referrals."
        )

    ist_time = datetime.fromtimestamp(
        ref["timestamp"],
        ZoneInfo("Asia/Kolkata")
    ).strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )

    await query.message.reply(
        f"🆕 Latest Referral\n\n"
        f"👤 Name: {ref['name']}\n"
        f"⭐ Stars: +{ref['stars']}\n"
        f"📌 Status: "
        f"{'Valid' if ref['valid'] else 'Re-Refer'}\n"
        f"🕒 IST: {ist_time}"
    )


@Client.on_callback_query(filters.regex(r"^allref_(.+)$"))
async def all_refers(client, query):

    acc_id = query.data.split(
        "_",
        1
    )[1]

    refs = await db.get_referrals(
        acc_id
    )

    if not refs:

        return await query.message.reply(
            "No referrals."
        )

    text = (
        f"📋 All Referrals\n"
        f"Account: {acc_id}\n\n"
    )

    for ref in refs:

        status = (
            "✅"
            if ref["valid"]
            else "♻️"
        )

        text += (
            f"{status} "
            f"{ref['name']} "
            f"(+{ref['stars']})\n"
        )

    await query.message.reply(
        text[:4096]
    )

@Client.on_callback_query(filters.regex(r"^countref_(.+)$"))
async def referral_count(client, query):

    acc_id = query.data.split("_", 1)[1]

    acc = await db.get_account(acc_id)

    if not acc:

        return await query.message.reply(
            "Account not found."
        )

    valid_ref = acc.get("valid_ref", 0)
    reref = acc.get("reref", 0)

    balance = (valid_ref * 3) + (reref * 1)

    await query.message.reply(
        f"📊 Statistics\n\n"
        f"Account: `{acc_id}`\n\n"
        f"Total: {acc.get('total_ref', 0)}\n"
        f"Valid: {valid_ref}\n"
        f"Re-Refer: {reref}\n\n"
        f"💰 Balance\n"
        f"Valid Refer ({valid_ref} × ₹3) = ₹{valid_ref * 3}\n"
        f"Re-Refer ({reref} × ₹1) = ₹{reref * 1}\n\n"
        f"Total Balance = ₹{balance}"
        ,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "💸 Withdraw",
                        callback_data=f"withdraw_{acc_id}"
                    )
                ]
            ]
        )
    )



ADMIN_USERNAME = "Syd_XyZ"


@Client.on_callback_query(filters.regex(r"^withdraw_(.+)$"))
async def withdraw_info(client, query):

    acc_id = query.data.split("_", 1)[1]

    await query.message.reply(
        "💸 Withdrawal Information\n\n"
        "• First 5 withdrawals have no minimum limit.\n"
        "• After 5 withdrawals, minimum withdrawal is ₹10.\n\n"
        "Withdrawal methods:\n"
        "• UPI\n"
        "• Crypto\n"
        "• Telegram Stars\n"
        "• Telegram Account\n\n"
        "Contact admin to request withdrawal.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "👤 Contact Admin",
                        url=f"https://t.me/{ADMIN_USERNAME}"
                    )
                ]
            ]
        )
    )


import re



FRUIT_EMOJIS = {
    "яблоко": "🍎",
    "клубника": "🍓",
    "банан": "🍌",
    "апельсин": "🍊",
    "лимон": "🍋",
    "арбуз": "🍉",
    "вишня": "🍒",
    "виноград": "🍇",
    "персик": "🍑",
    "груша": "🍐",
    "ананас": "🍍",
    "киви": "🥝",
    "манго": "🥭",
    "кокос": "🥥",
    "черника": "🫐",
}


@Client.on_message(filters.forwarded)
async def fruit_checker(client, message):

    if not message.forward_from:

        return

    if message.forward_from.id != BOT_ID:

        return

    text = message.text or message.caption or ""

    if not text.startswith(
        "🤖 ПРОВЕРКА НА РОБОТА"
    ):
        return

    fruit_match = re.search(
        r'«(.*?)»',
        text
    )

    if not fruit_match:
        return

    fruit_name = re.sub(
        r'[^а-яё]',
        '',
        fruit_match.group(1).lower()
    )

    fruit_name = re.sub(
        r'[\u200b\u200c\u200d\ufeff\xa0]',
        '',
        fruit_name
    )

    fruit_emoji = FRUIT_EMOJIS.get(
        fruit_name
    )

    if not fruit_emoji:

        return await message.reply(
            f"Unknown fruit:\n`{fruit_name}`"
        )

    await message.reply(
        f"Press: {fruit_emoji}"
    )

    await message.reply(
        fruit_emoji
    )
