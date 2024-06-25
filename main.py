import logging
import requests
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Tokens
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHECK_INTERVAL = int(os.getenv("GITHUB_CHECK_INTERVAL", 60))

# Global state variables
state = {
    "last_notif_id": None,
    "chat_id": None,
    "github_token": None,
    "awaiting_token": False,
}

# Emoji and title dictionaries for notifications
notification_emojis = {
    "approval_requested": "👀",
    "assign": "📌",
    "author": "✍️",
    "comment": "💬",
    "ci_activity": "⚙️",
    "invitation": "📧",
    "manual": "🛠️",
    "member_feature_requested": "🚀",
    "mention": "🔔",
    "review_requested": "👀",
    "security_alert": "🔒",
    "security_advisory_credit": "🏆",
    "state_change": "🔄",
    "subscribed": "👁️",
    "team_mention": "👥",
}

notification_titles = {
    "approval_requested": "New pull request approval",
    "assign": "Assigned",
    "author": "New comment",
    "comment": "New comment",
    "ci_activity": "New CI activity",
    "invitation": "New invitation",
    "manual": "New manual",
    "member_feature_requested": "New member feature request",
    "mention": "New mention",
    "review_requested": "New pull request review",
    "security_alert": "New security alert",
    "security_advisory_credit": "New security advisory credit",
    "state_change": "New state change",
    "subscribed": "New subscribed",
    "team_mention": "New team mention",
}


def format_notification_message(notif):
    emoji = notification_emojis.get(notif["reason"], "")
    notification_title = notification_titles.get(notif["reason"], "")
    repo_name = notif["repository"]["full_name"]
    subject_title = notif["subject"]["title"]
    subject_url = notif["subject"]["url"]
    thread_id = notif["id"]
    repo_url = notif["repository"]["html_url"]

    notification_message = (
        f"{emoji} {notification_title} in `{repo_name}`\n{subject_title}\n"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔗 Go to notifications", url="https://github.com/notifications"
            ),
            InlineKeyboardButton("➡️ Go to repository", url=repo_url),
        ],
        [
            InlineKeyboardButton("👀 Mark as read", callback_data=f"read_{thread_id}"),
            InlineKeyboardButton("✅ Mark as done", callback_data=f"done_{thread_id}"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return notification_message, reply_markup


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state["chat_id"] = update.message.chat_id
    state["awaiting_token"] = True

    await update.message.reply_text(
        "Please provide a GitHub token. You can create a Personal Access Token (classic) "
        "with notifications permissions only. For more information, visit: "
        "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens"
    )


async def receive_github_token(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if state["awaiting_token"]:
        state["github_token"] = update.message.text

        # Verify the GitHub token by fetching notifications
        if not verify_github_token(state["github_token"]):
            await update.message.reply_text(
                "Invalid or unauthorized GitHub token. Please create a Personal Access Token (classic) "
                "with notifications permissions only. For more information, visit: "
                "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens"
            )
            return

        await update.message.reply_text(f"Token verified.")
        state["awaiting_token"] = False

        # Process notifications immediately after verification
        await process_notifications(context)

        # Initialize the JobQueue to check for GitHub notifications periodically
        job_queue = context.application.job_queue
        job_queue.run_repeating(
            process_notifications,
            interval=CHECK_INTERVAL,
            first=CHECK_INTERVAL,
            chat_id=state["chat_id"],
        )


def fetch_github_notifications():
    url = "https://api.github.com/notifications"
    headers = {
        "Authorization": f"token {state['github_token']}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def verify_github_token(token):
    url = "https://api.github.com/notifications"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.get(url, headers=headers)
    return response.status_code == 200


def mark_thread(thread_id, action):
    url = f"https://api.github.com/notifications/threads/{thread_id}"
    headers = {
        "Authorization": f"token {state['github_token']}",
        "Accept": "application/vnd.github.v3+json",
    }
    if action == "read":
        response = requests.patch(url, headers=headers)
    elif action == "done":
        response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.status_code


async def process_notifications(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        notifications = fetch_github_notifications()
        if not notifications:
            logger.info("No new notifications.")
            return

        for notif in notifications:
            if notif["id"] == state["last_notif_id"]:
                break

            notification_message, reply_markup = format_notification_message(notif)

            await context.bot.send_message(
                chat_id=state["chat_id"],
                text=notification_message,
                reply_markup=reply_markup,
                parse_mode=constants.ParseMode.MARKDOWN_V2,
            )

        state["last_notif_id"] = notifications[0]["id"]
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    action, thread_id = query.data.split("_")
    mark_thread(thread_id, action)
    await query.edit_message_text(text=f"Marked as {action}.")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers for commands and callback queries
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, receive_github_token)
    )
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
