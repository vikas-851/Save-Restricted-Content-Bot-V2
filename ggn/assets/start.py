import pymongo
from telethon import events, Button
from pyrogram import Client, filters
from yt_dlp import YoutubeDL
import logging
import os
import cv2
from datetime import datetime, timedelta
from config import MONGODB_CONNECTION_STRING, OWNER_ID, LOG_GROUP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "start_users"
COLLECTION_NAME = "registered_users_collection"

mongo_client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

VERIFICATION_DURATION = timedelta(hours=4)
PUBLIC_EARN_API_KEY = "ea9211bfcf13f78d50c8a47a8a9f0569ec947509"

def is_verified(user_id):
    user_doc = collection.find_one({"user_id": user_id})
    if user_doc and "verified_at" in user_doc:
        verified_at = user_doc["verified_at"]
        if datetime.utcnow() - verified_at < VERIFICATION_DURATION:
            return True
    return False

def update_verification(user_id):
    collection.update_one({"user_id": user_id}, {"$set": {"verified_at": datetime.utcnow()}}, upsert=True)

@gagan.on(events.NewMessage(pattern="^/start"))
async def start(event):
    user_id = event.sender_id
    update_verification(user_id)
    buttons = [
        [Button.url("Verify Here", url=f"https://publicearn.com/verify?api={PUBLIC_EARN_API_KEY}&user_id={user_id}")],
        [Button.url("Join Channel", url="https://t.me/devggn")],
        [Button.url("Contact Me", url="https://t.me/ggnhere")],
    ]
    await event.respond(
        "Please verify yourself by clicking the verification link below.",
        buttons=buttons
    )

async def check_verification(event):
    user_id = event.sender_id
    if not is_verified(user_id):
        await event.respond("Please verify yourself first by clicking the verification link in the /start message.")
        return False
    return True

@gagan.on(events.NewMessage(pattern="^/gcast"))
async def broadcast(event):
    if event.sender_id != OWNER_ID:
        return await event.respond("You are not authorized to use this command.")
    
    if not await check_verification(event):
        return
    
    message = event.message.text.split(' ', 1)[1]
    for user_doc in collection.find():
        try:
            user_id = user_doc["user_id"]
            await gagan.send_message(user_id, message)
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {str(e)}")

@gagan.on(events.NewMessage(pattern="^/get"))
async def get_registered_users_command(event):
    if event.sender_id != OWNER_ID:
        return await event.respond("You are not authorized to use this command.")
    
    if not await check_verification(event):
        return
    
    registered_users = get_registered_users()
    filename = "registered_users.txt"
    save_user_ids_to_txt(registered_users, filename)
    await event.respond(file=filename, force_document=True)
    os.remove(filename)

def get_registered_users():
    registered_users = []
    for user_doc in collection.find():
        registered_users.append((str(user_doc["user_id"]), user_doc.get("first_name", "")))
    return registered_users

def save_user_ids_to_txt(users_info, filename):
    with open(filename, "w") as file:
        for user_id, first_name in users_info:
            file.write(f"{user_id}: {first_name}\n")

@app.on_message(filters.command("dl", prefixes="/"))
async def youtube_dl_command(_, message):
    if not await check_verification(message):
        await message.reply("Please verify yourself first by clicking the verification link in the /start message.")
        return
    
    if len(message.command) > 1:
        youtube_url = message.command[1]
        progress_message = await message.reply("Fetching video info...")
        try:
            video_info = get_youtube_video_info(youtube_url)
            if not video_info:
                await progress_message.edit_text("Failed to fetch video info.")
                return

            if video_info['duration'] > 10800:
                await progress_message.edit_text("Video duration exceeds 3 hours. Not allowed.")
                return
            
            await progress_message.edit_text("Downloading video...")
            original_file = f"{video_info['title'].replace('/', '_').replace(':', '_')}.mp4"
            ydl_opts = {
                'format': 'best',
                'outtmpl': original_file,
                'noplaylist': True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            if not os.path.exists(original_file):
                await progress_message.edit_text("Failed to download video.")
                return

            await progress_message.edit_text("Uploading video...")
            metadata = video_metadata(original_file)
            caption = f"{video_info['title']}\n\n__**Powered by [Advance Content Saver Bot](https://t.me/advance_content_saver_bot)**__"
            k = thumbnail(message.chat.id)
            result = await app.send_video(
                chat_id=message.chat.id,
                video=original_file,
                caption=caption,
                thumb=k,
                width=metadata['width'],
                height=metadata['height'],
                duration=metadata['duration'],
            )
            await result.copy(LOG_GROUP)
            os.remove(original_file)
            await progress_message.delete()
        except Exception as e:
            await progress_message.edit_text(f"An error occurred: {str(e)}")
    else:
        await message.reply("Please provide a YouTube URL after /dl.")

def get_youtube_video_info(url):
    ydl_opts = {'quiet': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        if not info_dict:
            return None
        return {
            'title': info_dict.get('title', 'Unknown Title'),
            'duration': info_dict.get('duration', 0),
        }

def video_metadata(file):
    vcap = cv2.VideoCapture(f'{file}')
    width = round(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = round(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = vcap.get(cv2.CAP_PROP_FPS)
    frame_count = vcap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = round(frame_count / fps)
    return {'width': width, 'height': height, 'duration': duration}

def thumbnail(chat_id):
    return f'{chat_id}.jpg' if os.path.exists(f'{chat_id}.jpg') else f'thumb.jpg'
