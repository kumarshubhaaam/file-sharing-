import asyncio
import base64
import logging
import os
import random
import re
import string
import time

from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from config import (
    ADMINS,
    START_PIC,
    FORCE_MSG, 
    START_MSG, 
    CUSTOM_CAPTION, 
    IS_VERIFY, 
    VERIFY_EXPIRE, 
    SHORTLINK_API, 
    SHORTLINK_URL, 
    DISABLE_CHANNEL_BUTTON, 
    PROTECT_CONTENT, 
    TUTORIAL, 
    OWNER_ID,
    AUTO_DELETE_TIME,
    AUTO_DELETE_MSG
)
from helper_func import subscribed, encode, decode, get_messages, get_shortlink, get_verify_status, update_verify_status, get_exp_time, delete_file
from database.database import add_user, del_user, full_userbase, present_user
from shortzy import Shortzy


@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    user = message.from_user
    verify_status = await get_verify_status(user.id)  
    if not await present_user(user.id):
        try:
            await add_user(user.id)
        except:
            pass
            
    if verify_status['is_verified']:
        elapsed_time = time.time() - verify_status['verified_time']
        client.LOGGER(__name__).info(f"Elapsed Time: {elapsed_time}, Verify Expire: {VERIFY_EXPIRE}")
        if elapsed_time > VERIFY_EXPIRE:
            client.LOGGER(__name__).info("Verification expired. Updating status.")
            await update_verify_status(user.id, is_verified=False)
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            await update_verify_status(user.id, verify_token=token, link="")
            g = await get_shortlink(SHORTLINK_URL, SHORTLINK_API,f'https://telegram.dog/{client.username}?start=verify_{token}')
            link = g
            btn = [
                [InlineKeyboardButton("💫 Refresh Access Token", url=link)],
                [InlineKeyboardButton('🎥 Tutorial Video', url=TUTORIAL)]
            ]
            try:
                btn.append([InlineKeyboardButton("♻️ Try Again", url = f"https://t.me/{client.username}?start={message.command[1]}"
                )])
            except IndexError:
                pass
                
            await client.send_message(
                chat_id=user.id, 
                text=f"<i>Your Access Token has expired. Please renew it and try again.\n\n<b>Token Validity:</b> {get_exp_time(VERIFY_EXPIRE)}\n\nThis is an ads-based access token. If you pass 1 access token, you can access messages from sharable links for the next {get_exp_time(VERIFY_EXPIRE)}.</i>", 
                reply_markup=InlineKeyboardMarkup(btn), 
                protect_content=False
                ) 
            return
            
    if "verify_" in message.text:        
        _, token = message.text.split("_", 1)
        if verify_status['verify_token'] != token:
            return await message.reply(
                "Given Access Token is Expired or Invalid. Try again by sending /start"
            )
        await update_verify_status(user.id, is_verified=True, verified_time=time.time())
        if verify_status["link"] == "":
            reply_markup = None
        else:
            btn = [[
                InlineKeyboardButton("📌 Get File 📌", url=f'https://t.me/{client.username}?start={verify_status["link"]}')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
        await client.send_message(
            chat_id = user.id,
            text = f"✨ <i>Successfully Your access token has been renewed. It's valid for the next: {get_exp_time(VERIFY_EXPIRE)}</i>", 
            reply_markup=reply_markup, 
            protect_content=False
        )
        return

    # Check if the user is not an admin and not the owner
    if user.id not in ADMINS and user.id != OWNER_ID:                                  
        if IS_VERIFY and not verify_status['is_verified']:
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            await update_verify_status(user.id, verify_token=token, link="")
            g = await get_shortlink(SHORTLINK_URL, SHORTLINK_API,f'https://telegram.dog/{client.username}?start=verify_{token}')
            link = g
            btn = [
                [InlineKeyboardButton("💫 Refresh Access Token", url=link)],
                [InlineKeyboardButton('🎥 Tutorial Video', url=TUTORIAL)]
            ]
            try:
                btn.append([InlineKeyboardButton("♻️ Try Again", url = f"https://t.me/{client.username}?start={message.command[1]}"
                )])
            except IndexError:
                pass
                
            await client.send_message(
                chat_id = user.id, 
                text=f"<i>Your Access Token has expired. Please renew it and try again.\n\n<b>Token Validity:</b> {get_exp_time(VERIFY_EXPIRE)}\n\nThis is an ads-based access token. If you pass 1 access token, you can access messages from sharable links for the next {get_exp_time(VERIFY_EXPIRE)}.</i>", 
                reply_markup=InlineKeyboardMarkup(btn), 
                protect_content=False
            ) 
            return
    else:
        pass
        
    if len(message.text) > 7:
        try:
            # Split the message text to extract the Base64 string
            base64_string = message.text.split(" ", 1)[1]  # Use message.text here, not text
            bstring = await decode(base64_string)  # Decode the Base64 string
            argument = bstring.split("-")
            
            if len(argument) == 3:
                try:
                    start = int(int(argument[1]) / abs(client.db_channel.id))
                    end = int(int(argument[2]) / abs(client.db_channel.id))
                except ValueError:
                    return await message.reply("Invalid data in argument. Please check your input.")
    
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            elif len(argument) == 2:
                try:
                    ids = [int(int(argument[1]) / abs(client.db_channel.id))]
                except ValueError:
                    return await message.reply("Invalid data in argument. Please check your input.")
            else:
                return await message.reply("Invalid data format in argument. Please check your input.")
    
            temp_msg = await message.reply("Processing your request. Please wait...")
    
            try:
                messages = await get_messages(client, ids)
            except Exception as e:
                await temp_msg.edit(f"An error occurred: {str(e)}")
                return
    
            await temp_msg.delete()
            
            filesent = []
            for msg in messages:
                if bool(CUSTOM_CAPTION) and bool(msg.document):
                    caption = CUSTOM_CAPTION.format(
                        previouscaption="" if not msg.caption else msg.caption.html,
                        filename=msg.document.file_name
                    )
                else:
                    caption = "" if not msg.caption else msg.caption.html
    
                reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None
                
                if AUTO_DELETE_TIME and AUTO_DELETE_TIME > 0:
                    try:
                        copied_msg = await msg.copy(
                            chat_id=message.from_user.id,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup,
                            protect_content=PROTECT_CONTENT
                        )
                        if copied_msg:
                            filesent.append(copied_msg)
                        await asyncio.sleep(0.5)
                    except FloodWait as e:
                        await asyncio.sleep(e.x)
                        await msg.copy(
                            chat_id=message.from_user.id,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup,
                            protect_content=PROTECT_CONTENT
                        )
                        if copied_msg:
                            filesent.append(copied_msg_for_deletion)
                    except Exception as e:
                        client.LOGGER(__name__).error(f"Error copying message: {e}")
                        pass
                else:
                    try:
                        await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                        await asyncio.sleep(0.5)
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                        await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                    except:
                        pass
                         
            if filesent:
                delete_data = await client.send_message(
                    chat_id=message.from_user.id,
                    text=AUTO_DELETE_MSG.format(time=get_exp_time(AUTO_DELETE_TIME))
                )
                # Schedule the file deletion task after all messages have been copied
                asyncio.create_task(delete_file(filesent, client, delete_data))
            else:
                client.LOGGER(__name__).info("No messages to track for deletion.")
                             
            return
        except IndexError:
            return await message.reply("Invalid input format. Please use the correct start parameter.")
                    
    else:  # Owner or Admin actions
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("⚡️ ᴀʙᴏᴜᴛ", callback_data="about"),
              InlineKeyboardButton("🍁 ᴄʟᴏsᴇ", callback_data="close")]]
        )
        if START_PIC:  # Check if START_PIC has a value
            await client.send_photo(
                chat_id=user.id,
                photo=START_PIC,
                caption=START_MSG.format(
                    first=message.from_user.first_name,
                    last=message.from_user.last_name,
                    username=None if not message.from_user.username else '@' + message.from_user.username,
                    mention=message.from_user.mention,
                    id=message.from_user.id
                ),
                reply_markup=reply_markup
            )
        else:
            await client.send_message(
                chat_id = user.id,
                text=START_MSG.format(
                    first=user.first_name,
                    last=user.last_name,
                    username=None if not user.username else '@' + user.username,
                    mention=user.mention,
                    id=user.id
                ),
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
    
        
#=====================================================================================##

WAIT_MSG = """"<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a replay to any telegram message with out any spaces.</code>"""

#=====================================================================================##

    
    
@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton(
                "• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •",
                url = client.invitelink)
        ]
    ]
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = '• ʀᴇʟᴏᴀᴅ •',
                    url = f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = False,
        disable_web_page_preview = True
    )

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()
        
                
