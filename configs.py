# (c) @dasqinnagiyev

import os


class Config(object):
    API_ID = int(os.environ.get("API_ID", 12345))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    SESSION_NAME = os.environ.get("SESSION_NAME", "Rename-Bot-0")
    SLEEP_TIME = int(os.environ.get("SLEEP_TIME", 5))
    BOT_OWNER = os.environ.get("BOT_OWNER", 1778839425)
    CAPTION = "Yenidən adlandırıldı. Bot by @dasqinnagiyev"
    UPDATES_CHANNEL = os.environ.get("UPDATES_CHANNEL", None)
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100))
    MONGODB_URI = os.environ.get("MONGODB_URI", "")
    DOWNLOAD_PATH = os.environ.get("DOWNLOAD_PATH", "./downloads")
    BROADCAST_AS_COPY = bool(os.environ.get("BROADCAST_AS_COPY", False))
    ONE_PROCESS_ONLY = bool(os.environ.get("ONE_PROCESS_ONLY", False))
    START_TEXT = """
Mən faylları yenidən adlandırıram.

Adını dəyişmək vəya kiçik şəkil (thumbnail) əlavə etmək istədiyin faylı mənə göndər.

Digər xüsusiyyətləri görmək üçün /ayarlar de.
    """
    PROGRESS = """
Faiz : {0}%
Bitdi: {1}
Cəmi: {2}
Sürət: {3}/s
Təxmini çatma vaxtı: {4}
    """
