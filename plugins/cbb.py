from pyrogram import __version__
from bot import Bot
from config import OWNER_USERNAME
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    if data == "about":
        await query.message.edit_text(
            text = f"<b>○ ᴏᴡɴᴇʀ : <a href='https://t.me/{OWNER_USERNAME}'>ᴘs - sᴜᴘᴘᴏʀᴛ​</a>\n○ ʟᴀɴɢᴜᴀɢᴇ : <code>ᴘʏᴛʜᴏɴ3</code>\n○ ʟɪʙʀᴀʀʏ : <a href='https://docs.pyrogram.org/'>ᴘʏʀᴏɢʀᴀᴍ ᴀꜱʏɴᴄɪᴏ {__version__}</a>\n○ ꜱᴏᴜʀᴄᴇ ᴄᴏᴅᴇ : <a href='https://t.me/pssupport_Robot'>ᴄʟɪᴄᴋ ʜᴇʀᴇ</a>\n○ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ : <a href='https://t.me/ps_updates'>𝙏𝙃𝙀 𝙋𝙎 𝘽𝙊𝙏𝙎</a>\n○ ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ : <a href='https://t.me/ps_discuss'>𝙋𝙎 - 𝘿𝙄𝙎𝘾𝙐𝙎𝙎𝙄𝙊𝙉 𝙂𝙍𝙊𝙐𝙋</a></b>",
            disable_web_page_preview = True,
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                    InlineKeyboardButton("⚡️ ᴄʟᴏsᴇ", callback_data = "close")
                    ]
                ]
            )
        )
  
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pas
