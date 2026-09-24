# freepw.py

import os
import re
import aiohttp

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Extractor import app
from config import PREMIUM_LOGS


# =========================================================
# CONFIG
# =========================================================

PDF_API_BASE_URL = os.getenv("PDF_API_BASE_URL", "").rstrip("/")

BATCH_SEARCH_PATH = os.getenv(
    "BATCH_SEARCH_PATH",
    "/batches/search"
)

PDF_LIST_PATH = os.getenv(
    "PDF_LIST_PATH",
    "/pdfs"
)

REQUEST_TIMEOUT = 30


# =========================================================
# HELPERS
# =========================================================

def clean_name(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    return name[:80].strip() or "PDF"


async def api_get(session, path, token, params=None):
    if not PDF_API_BASE_URL:
        return None

    url = f"{PDF_API_BASE_URL}{path}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

        async with session.get(
            url,
            headers=headers,
            params=params or {},
            timeout=timeout
        ) as response:

            if response.status != 200:
                return None

            return await response.json()

    except Exception:
        return None


def get_list(data):
    if not isinstance(data, dict):
        return []

    for key in ("data", "results", "items", "batches", "pdfs"):
        value = data.get(key)

        if isinstance(value, list):
            return value

        if isinstance(value, dict):
            for subkey in ("data", "results", "items"):
                if isinstance(value.get(subkey), list):
                    return value[subkey]

    return []


def get_value(item, *keys):
    if not isinstance(item, dict):
        return None

    for key in keys:
        value = item.get(key)

        if value is not None:
            return value

    return None


def is_pdf(item):
    if not isinstance(item, dict):
        return False

    file_type = str(
        get_value(item, "type", "contentType", "mimeType") or ""
    ).lower()

    url = str(
        get_value(
            item,
            "url",
            "pdfUrl",
            "fileUrl",
            "downloadUrl",
            "attachmentUrl"
        ) or ""
    ).lower()

    title = str(
        get_value(item, "title", "name", "fileName") or ""
    ).lower()

    return (
        "pdf" in file_type
        or url.endswith(".pdf")
        or ".pdf?" in url
        or title.endswith(".pdf")
    )


# =========================================================
# MAIN FLOW
# =========================================================

async def process_pwwp(bot, message, user_id):

    # -----------------------------------------------------
    # API CHECK
    # -----------------------------------------------------

    if not PDF_API_BASE_URL:

        await message.reply_text(
            "⚠️ PDF API is not configured.\n\n"
            "Set PDF_API_BASE_URL in your environment variables "
            "before using WITHOUT LOGIN."
        )
        return

    # -----------------------------------------------------
    # TOKEN
    # -----------------------------------------------------

    token_msg = await message.reply_text(
        "🔐 <b>Enter Working Access Token</b>\n\n"
        "Send your authorized access token."
    )

    try:
        token_response = await bot.listen(
            message.chat.id,
            filters=filters.user(user_id),
            timeout=120
        )

        token = token_response.text.strip()

    except Exception:
        await token_msg.edit_text(
            "⏰ Token input timed out."
        )
        return

    if not token:
        await token_response.reply_text(
            "❌ Invalid token."
        )
        return

    # -----------------------------------------------------
    # BATCH NAME
    # -----------------------------------------------------

    batch_msg = await token_response.reply_text(
        "📚 <b>Enter Batch Name</b>"
    )

    try:
        batch_response = await bot.listen(
            message.chat.id,
            filters=filters.user(user_id),
            timeout=120
        )

        batch_name = batch_response.text.strip()

    except Exception:
        await batch_msg.edit_text(
            "⏰ Batch input timed out."
        )
        return

    if not batch_name:
        await batch_response.reply_text(
            "❌ Batch name cannot be empty."
        )
        return

    # -----------------------------------------------------
    # SEARCH BATCHES
    # -----------------------------------------------------

    searching = await batch_response.reply_text(
        "🔎 Searching batches..."
    )

    async with aiohttp.ClientSession() as session:

        data = await api_get(
            session,
            BATCH_SEARCH_PATH,
            token,
            {
                "q": batch_name,
                "name": batch_name
            }
        )

    batches = get_list(data)

    if not batches:
        await searching.edit_text(
            "❌ No batch found."
        )
        return

    # -----------------------------------------------------
    # BATCH KEYBOARD
    # -----------------------------------------------------

    buttons = []

    for index, batch in enumerate(batches[:20], start=1):

        name = get_value(
            batch,
            "name",
            "batchName",
            "title"
        )

        batch_id = get_value(
            batch,
            "id",
            "_id",
            "batchId"
        )

        if not batch_id:
            continue

        name = str(name or f"Batch {index}")

        buttons.append([
            InlineKeyboardButton(
                f"{index}. {name[:45]}",
                callback_data=f"freebatch:{batch_id}"
            )
        ])

    if not buttons:
        await searching.edit_text(
            "❌ No valid batch data returned by API."
        )
        return

    buttons.append([
        InlineKeyboardButton(
            "❌ Cancel",
            callback_data="freecancel"
        )
    ])

    await searching.edit_text(
        "📚 <b>Select Batch</b>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# =========================================================
# BATCH SELECTION
# =========================================================

@app.on_callback_query(filters.regex(r"^freebatch:"))
async def free_batch_callback(client, query):

    await query.answer()

    user_id = query.from_user.id

    if not query.message:
        return

    batch_id = query.data.split(":", 1)[1]

    await query.message.edit_text(
        "📅 <b>Enter Date</b>\n\n"
        "Example:\n"
        "<code>23/09/2026</code>\n\n"
        "Multiple dates:\n"
        "<code>23/09/2026&24/09/2026</code>"
    )

    try:
        date_msg = await client.listen(
            query.message.chat.id,
            filters=filters.user(user_id),
            timeout=120
        )

        date_text = date_msg.text.strip()

    except Exception:
        await query.message.edit_text(
            "⏰ Date input timed out."
        )
        return

    dates = [
        x.strip()
        for x in date_text.split("&")
        if x.strip()
    ]

    if not dates:
        await date_msg.reply_text(
            "❌ Invalid date."
        )
        return

    # -----------------------------------------------------
    # TOKEN
    # -----------------------------------------------------
    #
    # Token is intentionally NOT recovered from global
    # storage. Your authorized backend should provide a
    # secure session mechanism if the callback needs it.
    #
    # -----------------------------------------------------

    await date_msg.reply_text(
        "⚠️ Batch selected successfully.\n\n"
        "To fetch PDFs securely, connect this callback "
        "to your authorized backend/session token."
    )


# =========================================================
# CANCEL
# =========================================================

@app.on_callback_query(filters.regex(r"^freecancel$"))
async def free_cancel_callback(client, query):

    await query.answer("Cancelled")

    if query.message:
        await query.message.edit_text(
            "❌ WITHOUT LOGIN cancelled."
        )
