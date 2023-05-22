import threading
import os
import socket
import asyncio
import random

from config import *
from door import *

from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

# Named global logger from config
logger = logging.getLogger("garage")


# Update(
# message=Message(channel_chat_created=False,
#   chat=Chat(first_name='Vladimir', id=524269296, last_name='Ofitserov',
#             type=<ChatType.PRIVATE>, username='mgtu273'),
#   date=datetime.datetime(2023, 4, 30, 22, 22, 35, tzinfo=datetime.timezone.utc),
#   delete_chat_photo=False,
#   entities=(
#       MessageEntity(length=5, offset=0, type=<MessageEntityType.BOT_COMMAND>),),
#       from_user=User(first_name='Vladimir', id=524269296, is_bot=False, language_code='en', last_name='Ofitserov', username='mgtu273'),
# group_chat_created=False, message_id=30, supergroup_chat_created=False, text='/caps test'), update_id=165963743)

class TelegramDoorController(threading.Thread):
    def __init__(self, door):
        threading.Thread.__init__(self)
        self.application = None
        self.loop = None
        logger.info("created telegram door controller")
        self.door = door
        self.phrases = open(SAY_PHRASES, "r").readlines()
        return

    async def update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = str(update)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        return

    async def startbot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.chat.id == TELEGRAM_USERID:
            text = "Welcome, " + update.message.chat.first_name + "!"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        else:
            text = "Sorry, %s this bot is private." % update.message.chat.first_name
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            await context.bot.shutdown()
            pass
        logger.info("telegram: " + text)
        return

    async def command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.lower().replace("\n", " ")
        sender_id = update.message.chat.id
        logger.info("telegram got command: \"%s\" from \"%s\""
                    % (text, sender_id))
        if sender_id != TELEGRAM_USERID:
            logger.info(
                "telegram message from \"%s\" is ignored, expecting only \"%s\"" % \
                (sender_id, TELEGRAM_USERID))
            return
        reply = "Unrecognized command, try \"status\" or \"help\""
        if text.find("close") == 0:
            reply = self.door.close()
            pass
        if text.find("stop") == 0 or text.find("silence") == 0:
            reply = self.door.silence()
            pass
        if text.find("status") == 0:
            reply = self.door.status().replace("<br>", ", ")
            pass
        if text.find("help") == 0:
            reply = "Available commands are: close, stop/silence, status"
            pass
        if text.find("awesome") != -1 or text.find("awsome") != -1:
            reply = "You sure are awesome!"
            pass
        if text.find("say") != -1:
            reply = random.choice(self.phrases)
            pass
        if text.find("quitquitquit") == 0:
            reply = "Killing server right now."
            await self.application.shutdown()
            pass
        await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)
        return

    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Sorry, I didn't understand that command.")

    async def notify(self, context: ContextTypes.DEFAULT_TYPE):
        if self.door.check() and self.door.notify():
            reply = self.door.message()
            logger.info("telegram sending \"%s\"" % reply)
            await context.bot.send_message(chat_id=TELEGRAM_USERID, text=reply)
        return

    def run(self):
        # event loop is only created by default in the main thread
        # this code does not run on the main thread, so we create
        # our own event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        logger.info("setting up telegram bot: FosterCityDoorBot")
        self.application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        command_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), self.command)
        start_handler = CommandHandler('start', self.startbot)
        update_handler = CommandHandler('update', self.update)
        unknown_handler = MessageHandler(filters.COMMAND, self.unknown)

        self.application.add_handler(start_handler)
        self.application.add_handler(command_handler)
        self.application.add_handler(update_handler)
        self.application.add_handler(unknown_handler)

        job_queue = self.application.job_queue
        job_minute = job_queue.run_repeating(self.notify, interval=NOTIFY, first=5)
        logger.info("setup is done: FosterCityDoorBot")

        logger.info("telegram polling forever...")
        self.application.run_polling(stop_signals=None)
        logger.info("...done polling telegram")
        return

    def shutdown(self):
        def system_exit():
            raise SystemExit
        logger.info("telegram scheduling shutdown...")
        self.loop.call_soon_threadsafe(system_exit)
        return
