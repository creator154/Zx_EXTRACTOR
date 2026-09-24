import config

from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Extractor import app
from Extractor.core import script
from Extractor.core.func import subscribe

# Existing login flow
from Extractor.modules.pw import pw_login


# ============================================================
# MAIN BUTTONS
# ============================================================

buttons = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "👨‍💻 Developer 🇮🇳",
            url="https://t.me/SUMIT_ZX"
        )
    ],
    [
        InlineKeyboardButton(
            "🔐 Physics Wallah Login",
            callback_data="pw_"
        )
    ],
    [
        InlineKeyboardButton(
            "📖 Physics Wallah Without Login",
            callback_data="without_login_"
        )
    ]
])


# ============================================================
# PHOTO
# ============================================================

def photo():
    return config.THUMB_URL


# ============================================================
# START COMMAND
# ============================================================

@app.on_message(filters.command("start"))
async def start(_, message):

    join = await subscribe(_, message)

    if join == 1:
        return

    try:
        await message.reply_photo(
            photo=photo(),
            caption=script.START_TXT.format(
                message.from_user.mention
            ),
            reply_markup=buttons
        )

    except Exception as e:

        print(f"Error in start command: {e}")

        await message.reply_text(
            script.START_TXT.format(
                message.from_user.mention
            ),
            reply_markup=buttons
        )


# ============================================================
# CALLBACK HANDLER
# ============================================================

@app.on_callback_query()
async def handle_callback(client: Client, query):

    data = query.data

    # --------------------------------------------------------
    # HOME
    # --------------------------------------------------------

    if data == "home_":

        await query.answer()

        await query.message.edit_text(
            script.START_TXT.format(
                query.from_user.mention
            ),
            reply_markup=buttons
        )

        return

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    if data == "pw_":

        await query.answer()

        try:

            await pw_login(
                app,
                query.message
            )

        except Exception as e:

            print(f"Login error: {e}")

            await query.message.reply_text(
                "❌ Login process में error आया।\n"
                "Please try again."
            )

        return

    # --------------------------------------------------------
    # WITHOUT LOGIN
    # --------------------------------------------------------

    if data == "without_login_":

        await query.answer()

        without_login_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "𝐁𝐀𝐂𝐊",
                    callback_data="home_"
                )
            ]
        ])

        await query.message.edit_text(
            "📖 <b>WITHOUT LOGIN</b>\n\n"
            "Please send your authorized/public PDF here.",
            reply_markup=without_login_buttons
        )

        return

    # --------------------------------------------------------
    # UNKNOWN CALLBACK
    # --------------------------------------------------------

    await query.answer(
        "This option is not available.",
        show_alert=True
    )
