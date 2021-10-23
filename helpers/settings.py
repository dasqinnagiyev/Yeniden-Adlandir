# (c) @dasqinnagiyev

import asyncio
from helpers.database.access_db import db
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


async def OpenSettings(event: Message, user_id: int):
    try:
        await event.edit(
            text="Burda parametrlərinizi təyin edə bilərsiniz:\n\nDigər komandalar:\/nayarlar - Ayarlar panelini göstər\n/sekilsil - Şəkili sil (thumbnail)\n/sekilebax - seçdiyiniz kiçik şəkili göstərir\n/bsil - Xüsusi başlığı sil.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(f"Dokument olaraq göndər {'✅' if ((await db.get_upload_as_doc(user_id)) is True) else '❌'}",
                                          callback_data="triggerUploadMode")],
                    [InlineKeyboardButton("✏️ Fayl adı prefiksi️", callback_data="triggerPrefix")],
                    [InlineKeyboardButton("🖼 kiçik şəkil", callback_data="triggerThumbnail")],
                    [InlineKeyboardButton("🏷 Xüsusi başlıq", callback_data="triggerCaption")],
                    [InlineKeyboardButton("❎ Bağla", callback_data="closeMeh")]
                ]
            )
        )
    except FloodWait as e:
        await asyncio.sleep(e.x)
        await OpenSettings(event, user_id)
    except MessageNotModified:
        pass
