# (c) @dasqinnagiyev

import os
import time
import psutil
import shutil
import string
import asyncio
from pyromod import listen
from pyrogram import Client, filters
from asyncio import TimeoutError
from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

from configs import Config
from helpers.settings import OpenSettings
from helpers.database.access_db import db
from helpers.forcesub import ForceSub
from helpers.check_gap import CheckTimeGap
from helpers.setup_prefix import SetupPrefix
from helpers.broadcast import broadcast_handler
from helpers.uploader import UploadFile, UploadVideo, UploadAudio
from helpers.database.add_user import AddUserToDatabase
from helpers.display_progress import progress_for_pyrogram, humanbytes

RenameBot = Client(
    session_name=Config.SESSION_NAME,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)


@RenameBot.on_message(filters.private & filters.command("start"))
async def start_handler(bot: Client, event: Message):
    await AddUserToDatabase(bot, event)
    FSub = await ForceSub(bot, event)
    if FSub == 400:
        return
    await event.reply_text(
        text=f"Salam, {event.from_user.mention}\n{Config.START_TEXT}",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("DAQO MODS", url="https://t.me/daqomods"),
                 InlineKeyboardButton("Maraqlı botlar", url="https://t.me/daqobots")],
                [InlineKeyboardButton("Sahibim - @dasqinnagiyev", url="https://t.me/dasqinnagiyev")]
            ]
        )
    )


@RenameBot.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def rename_handler(bot: Client, event: Message):
    await AddUserToDatabase(bot, event)
    FSub = await ForceSub(bot, event)
    if FSub == 400:
        return
    isInGap, t_ = await CheckTimeGap(user_id=event.from_user.id)
    if (Config.ONE_PROCESS_ONLY is False) and (isInGap is True):
        await event.reply_text(f"Bağışlayın,\nFlooda icazə verilmir!\n `{str(t_)}s` sonra videonu göndərin!!", quote=True)
        return
    elif (Config.ONE_PROCESS_ONLY is True) and (isInGap is True):
        await event.reply_text(f"Bağışlayın,\nFlooda icazə verilmir!\n{t_}", quote=True)
        return
    media = event.video or event.audio or event.document
    if media and media.file_name:
        reply_ = await event.reply_text(
            text=f"**Faylın hazırki adı:** `{media.file_name}`\n\nMənə fayla vermək istədiyin yeni adı göndər!",
            quote=True
        )
        download_location = f"{Config.DOWNLOAD_PATH}/{str(event.from_user.id)}/{str(time.time())}/"
        if os.path.exists(download_location):
            os.makedirs(download_location)
        try:
            ask_: Message = await bot.listen(event.chat.id, timeout=300)
            if ask_.text and (ask_.text.startswith("/") is False):
                ascii_ = ''.join([i if (i in string.digits or i in string.ascii_letters or i == " ") else "" for i in ask_.text.rsplit('.', 1)[0]])
                prefix_ = await db.get_prefix(event.from_user.id)
                new_file_name = f"{download_location}{prefix_ if (prefix_ is not None) else ''}{ascii_.replace(' ', '_')}.{media.file_name.rsplit('.', 1)[-1]}"
                if len(new_file_name) > 255:
                    await reply_.edit("Bağışlayın,\nFayl adının uzunluğu 255 baytdan çoxdur!")
                    return
                await ask_.delete(True)
                await reply_.edit("Fayl yüklənir...")
                await asyncio.sleep(Config.SLEEP_TIME)
                c_time = time.time()
                try:
                    await bot.download_media(
                        message=event,
                        file_name=new_file_name,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            "Fayl yüklənir...",
                            reply_,
                            c_time
                        )
                    )
                    if not os.path.lexists(new_file_name):
                        try:
                            await reply_.edit("Birşeylər tərs getdi!\nFaylı tapa bilmədim.")
                        except:
                            print(f"Birşeylər tərs getdi!\n {str(event.from_user.id)} üçün fayl tapılmadı !!")
                        return
                    await asyncio.sleep(Config.SLEEP_TIME)
                    await reply_.edit("Faylı göndərirəm...")
                    upload_as_doc = await db.get_upload_as_doc(event.from_user.id)
                    if upload_as_doc is True:
                        await UploadFile(
                            bot,
                            reply_,
                            file_path=new_file_name,
                            file_size=media.file_size
                        )
                    else:
                        if event.audio:
                            duration_ = event.audio.duration if event.audio.duration else 0
                            performer_ = event.audio.performer if event.audio.performer else None
                            title_ = event.audio.title if event.audio.title else None
                            await UploadAudio(
                                bot,
                                reply_,
                                file_path=new_file_name,
                                file_size=media.file_size,
                                duration=duration_,
                                performer=performer_,
                                title=title_
                            )
                        elif event.video or (event.document and event.document.mime_type.startswith("video/")):
                            thumb_ = event.video.thumbs[0] if ((event.document is None) and (event.video.thumbs is not None)) else None
                            duration_ = event.video.duration if ((event.document is None) and (event.video.thumbs is not None)) else 0
                            width_ = event.video.width if ((event.document is None) and (event.video.thumbs is not None)) else 0
                            height_ = event.video.height if ((event.document is None) and (event.video.thumbs is not None)) else 0
                            await UploadVideo(
                                bot,
                                reply_,
                                file_path=new_file_name,
                                file_size=media.file_size,
                                default_thumb=thumb_,
                                duration=duration_,
                                width=width_,
                                height=height_
                            )
                        else:
                            await UploadFile(
                                bot,
                                reply_,
                                file_path=new_file_name,
                                file_size=media.file_size
                            )
                except Exception as err:
                    try:
                        await reply_.edit(f"Faylı yükləmək mümkün olmadı!\n**Xəta:** `{err}`")
                    except:
                        print(f"{str(event.from_user.id)} üçün faylı yükləmək mümkün olmadı!!\n**Xəta:** `{err}`")
            elif ask_.text and (ask_.text.startswith("/") is True):
                await reply_.edit("Hazırki proses ləğv edildi!")
        except TimeoutError:
            await reply_.edit("Bağışlayın,\n5 Dəqiqə Keçdi! Daha çox gözləyə bilmərəm. Adını dəyişdirmək üçün faylı mənə yenidən göndər.")


@RenameBot.on_message(filters.private & filters.photo & ~filters.edited)
async def photo_handler(bot: Client, event: Message):
    await AddUserToDatabase(bot, event)
    FSub = await ForceSub(bot, event)
    if FSub == 400:
        return
    editable = await event.reply_text("Gözlə...")
    await db.set_thumbnail(event.from_user.id, thumbnail=event.photo.file_id)
    await editable.edit("Kiçik şəkil yadda saxlanıldı!")


@RenameBot.on_message(filters.private & filters.command(["delete_thumbnail", "delete_thumb", "del_thumb", "delthumb", "sekilsil"]) & ~filters.edited)
async def delete_thumb_handler(bot: Client, event: Message):
    await AddUserToDatabase(bot, event)
    FSub = await ForceSub(bot, event)
    if FSub == 400:
        return
    await db.set_thumbnail(event.from_user.id, thumbnail=None)
    await event.reply_text(
        "Kiçik şəkil uğurla silindi!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Ayarlara gir", callback_data="openSettings")],
            [InlineKeyboardButton("Bağla", callback_data="closeMeh")]
        ])
    )


@RenameBot.on_message(filters.private & filters.command(["show_thumbnail", "show_thumb", "showthumbnail", "showthumb", "sekilebax"]) & ~filters.edited)
async def show_thumb_handler(bot: Client, event: Message):
    await AddUserToDatabase(bot, event)
    FSub = await ForceSub(bot, event)
    if FSub == 400:
        return
    _thumbnail = await db.get_thumbnail(event.from_user.id)
    if _thumbnail is not None:
        try:
            await bot.send_photo(
                chat_id=event.chat.id,
                photo=_thumbnail,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Şəkili sil", callback_data="deleteThumbnail")]]
                ),
                reply_to_message_id=event.message_id
            )
        except Exception as err:
            try:
                await bot.send_message(
                    chat_id=event.chat.id,
                    text=f"Kiçik şəkil göndərilə bilmir!\n\n**Xəta:** `{err}`",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❎ Bağla", callback_data="closeMeh")]]),
                    reply_to_message_id=event.message_id
                )
            except:
                pass
    else:
        await event.reply_text("Yaddaşda kiçik şəkil tapılmadı!\nYadda saxlamaq üçün kiçik şəkil göndər.", quote=True)


@RenameBot.on_message(filters.private & filters.command(["delete_caption", "del_caption", "remove_caption", "rm_caption", "bsil"]) & ~filters.edited)
async def delete_caption(bot: Client, event: Message):
    await AddUserToDatabase(bot, event)
    FSub = await ForceSub(bot, event)
    if FSub == 400:
        return
    await db.set_caption(event.from_user.id, caption=None)
    await event.reply_text("Xüsusi başlıq uğurla silindi!")


@RenameBot.on_message(filters.private & filters.command("toplumesaj") & filters.user(Config.BOT_OWNER) & filters.reply)
async def _broadcast(_, event: Message):
    await broadcast_handler(event)


@RenameBot.on_message(filters.private & filters.command("vezyet") & filters.user(Config.BOT_OWNER))
async def show_status_count(_, event: Message):
    total, used, free = shutil.disk_usage(".")
    total = humanbytes(total)
    used = humanbytes(used)
    free = humanbytes(free)
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    total_users = await db.total_users_count()
    await event.reply_text(
        text=f"**Ümumi disk yaddaşı:** {total} \n**İstifadə olunub:** {used}({disk_usage}%) \n**Boş yer:** {free} \n**CPU istifadəsi:** {cpu_usage}% \n**RAM istifadəsi:** {ram_usage}%\n\n**DB-dəki ümumi istifadəçi sayı:** `{total_users}`",
        parse_mode="Markdown",
        quote=True
    )


@RenameBot.on_message(filters.private & filters.command("ayarlar"))
async def settings_handler(bot: Client, event: Message):
    await AddUserToDatabase(bot, event)
    FSub = await ForceSub(bot, event)
    if FSub == 400:
        return
    editable = await event.reply_text(
        text="Gözlə..."
    )
    await OpenSettings(editable, user_id=event.from_user.id)


@RenameBot.on_callback_query()
async def callback_handlers(bot: Client, cb: CallbackQuery):
    if "closeMeh" in cb.data:
        await cb.message.delete(True)
    elif "openSettings" in cb.data:
        await OpenSettings(cb.message, user_id=cb.from_user.id)
    elif "triggerUploadMode" in cb.data:
        upload_as_doc = await db.get_upload_as_doc(cb.from_user.id)
        if upload_as_doc is True:
            await db.set_upload_as_doc(cb.from_user.id, upload_as_doc=False)
        else:
            await db.set_upload_as_doc(cb.from_user.id, upload_as_doc=True)
        await OpenSettings(cb.message, user_id=cb.from_user.id)
    elif "forceNewPrefix" in cb.data:
        await cb.message.edit(
            text="Mənə yeni fayl adı prefiksini göndər!"
        )
        try:
            ask_: Message = await bot.listen(cb.message.chat.id, timeout=300)
            if ask_.text and (ask_.text.startswith("/") is False):
                await ask_.delete(True)
                await SetupPrefix(ask_.text, user_id=cb.from_user.id, editable=cb.message)
            elif ask_.text and (ask_.text.startswith("/") is True):
                await cb.message.edit(
                    text="Hazırki proses ləğv edildi!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Geriyə qayıt", callback_data="openSettings")]])
                )
        except TimeoutError:
            await cb.message.edit(
                text="Bağışlayın,\n5 Dəqiqə keçdi! Daha çox gözləyə bilmərəm. Adını dəyişdirmək istədiyin faylı mənə yenidən göndər.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Geriyə qayıt", callback_data="openSettings")]])
            )
    elif "triggerPrefix" in cb.data:
        current_prefix = await db.get_prefix(cb.from_user.id)
        if current_prefix is None:
            await cb.answer("Hal-hazırda heç bir fayl adı prefiksi təyin etməmisiz!", show_alert=True)
            await cb.message.edit(
                text="Mənə bir fayl adı prefiksi göndər!"
            )
            try:
                ask_: Message = await bot.listen(cb.message.chat.id, timeout=300)
                if ask_.text and (ask_.text.startswith("/") is False):
                    await ask_.delete(True)
                    await SetupPrefix(ask_.text, user_id=cb.from_user.id, editable=cb.message)
                elif ask_.text and (ask_.text.startswith("/") is True):
                    await cb.message.edit(
                        text="Hazırki proses ləğv olundu!",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Geriyə qayıt", callback_data="openSettings")]])
                    )
            except TimeoutError:
                await cb.message.edit(
                    text="Bağışlayın,\n5 Dəqiqə keçdi! daha çox gözləyə bilmərəm.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Geriyə qayıt", callback_data="openSettings")]])
                )
        else:
            await cb.message.edit(
                text=f"**Hazırki Prefiks:** `{current_prefix}`",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Yeni Prefiks təyin et", callback_data="forceNewPrefix")],
                        [InlineKeyboardButton("Geriyə qayıt", callback_data="openSettings")]
                    ]
                )
            )
    elif "triggerThumbnail" in cb.data:
        thumbnail = await db.get_thumbnail(cb.from_user.id)
        if thumbnail is None:
            await cb.answer("Yaddaşda kiçik şəkil tapılmadı!\nYadda saxlamaq üçün şəkil göndər.", show_alert=True)
        else:
            await cb.answer("Yaddaşda kiçik şəkil tapılmadı!\nŞəkil göndərməyə çalışılır.", show_alert=True)
            try:
                await bot.send_photo(
                    chat_id=cb.message.chat.id,
                    photo=thumbnail,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Şəkili sil", callback_data="deleteThumbnail")]])
                )
            except Exception as err:
                try:
                    await bot.send_message(
                        chat_id=cb.message.chat.id,
                        text=f"Kiçik şəkil göndərilə bilmir!\n\n**Xəta:** `{err}`",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❎ Bağla", callback_data="closeMeh")]])
                    )
                except:
                    pass
    elif "deleteThumbnail" in cb.data:
        await db.set_thumbnail(cb.from_user.id, thumbnail=None)
        await cb.answer("Hazırki kiçik şəkil uğurla silindi!", show_alert=True)
        await OpenSettings(cb.message, user_id=cb.from_user.id)
    elif ("triggerCaption" in cb.data) or ("forceChangeCaption" in cb.data):
        custom_caption_ = await db.get_caption(cb.from_user.id)
        if custom_caption_ is not None:
            try:
                await cb.message.edit(
                    text=f"**Hazırki xüsusi başlıq:**\n\n`{custom_caption_}`\nSilmək üçün /bsil komandasını işlət.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Başlığı dəyiş", callback_data="forceChangeCaption")]])
                )
            except MessageNotModified:
                pass
            if "forceChangeCaption" not in cb.data:
                return
        elif custom_caption_ is None:
            await cb.answer("Hazırda heç bir fayl başlığı təyin etməmisiniz!", show_alert=True)
        await cb.message.edit(
            text="Mənə fayl başlığı göndər!"
        )
        try:
            ask_: Message = await bot.listen(cb.message.chat.id, timeout=300)
            if ask_.text and (ask_.text.startswith("/") is False):
                if len(ask_.text) > 1024:
                    await ask_.reply_text(
                        "Bağışlayın,\nBaşlıq mətninin uzunluğu 1024 baytdan çoxdur!",
                        quote=True,
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [InlineKeyboardButton("Yenidən cəhd elə", callback_data="triggerCaption")],
                                [InlineKeyboardButton("Geriyə qayıt", callback_data="openSettings")]
                            ]
                        )
                    )
                    return
                caption = ask_.text.markdown
                await ask_.delete(True)
                await db.set_caption(cb.from_user.id, caption=caption)
                await cb.message.edit(
                    "Xüsusi başlıq uğurla silindi!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Ayarlara gir", callback_data="openSettings")],
                        [InlineKeyboardButton("Bağla", callback_data="closeMeh")]
                    ])
                )
            elif ask_.text and (ask_.text.startswith("/") is True):
                await cb.message.edit(
                    text="Hazırki proses ləğv edildi!",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Geriyə qayıt", callback_data="openSettings")]])
                )
        except TimeoutError:
            await cb.message.edit(
                text="Bağışlayın,,\n5 Dəqiqə keçdi! daha çox gözləyə bilmərəm.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Geriyə qayıt", callback_data="openSettings")]])
            )


RenameBot.run()
