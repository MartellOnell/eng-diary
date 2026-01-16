"""Telegram bot for English vocabulary learning."""

import random
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN
import database as db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📚 Test All Words"],
        ["📝 Test Last 30 Words"],
        ["➕ Add Word"],
        ["👀 View Words"],
        ["🗑 Delete Word"]
    ],
    resize_keyboard=True
)

ADDING_TYPE, ADDING_VERB_FORMS, ADDING_WORD1, ADDING_WORD2 = range(4)
QUIZ_ANSWER = range(4, 5)[0]
DELETE_WORDS_PER_PAGE = 5
VIEW_WORDS_PER_PAGE = 10


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    is_new = db.register_user(user.id, user.username, user.first_name)
    
    if is_new:
        welcome_text = (
            f"Hello, {user.first_name}! 👋\n\n"
            "Welcome to the English vocabulary learning bot!\n\n"
            "Here you can:\n"
            "📚 Take tests on all added words\n"
            "📝 Test the last 30 words\n"
            "➕ Add new words (translations and irregular verbs)\n\n"
            "Choose an action from the menu below:"
        )
    else:
        welcome_text = (
            f"Welcome back, {user.first_name}! 👋\n\n"
            "Choose an action from the menu below:"
        )
    
    await update.message.reply_text(welcome_text, reply_markup=MAIN_MENU_KEYBOARD)


async def add_word_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the word adding process."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔤 Translation (English ↔ Russian)", callback_data="type_translation")],
        [InlineKeyboardButton("📖 Irregular Verb (3 forms)", callback_data="type_irregular")]
    ])
    
    await update.message.reply_text(
        "What type of word would you like to add?",
        reply_markup=keyboard
    )
    return ADDING_TYPE


async def add_word_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle word type selection."""
    query = update.callback_query
    await query.answer()
    
    word_type = query.data.replace("type_", "")
    context.user_data["word_type"] = word_type
    
    if word_type == "translation":
        await query.edit_message_text(
            "Enter the English word:"
        )
        return ADDING_WORD1
    else:
        keyboard = ReplyKeyboardMarkup(
            [
                ["1️⃣ → 2️⃣ (Infinitive → Past Simple)"],
                ["2️⃣ → 3️⃣ (Past Simple → Past Participle)"],
                ["❌ Cancel"]
            ],
            resize_keyboard=True
        )
        await query.edit_message_text(
            "Choose which forms of the irregular verb you want to add:"
        )
        await query.message.reply_text(
            "Choose a pair of forms:",
            reply_markup=keyboard
        )
        return ADDING_VERB_FORMS


async def add_verb_forms_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle verb forms selection."""
    text = update.message.text
    
    if text == "❌ Cancel":
        await update.message.reply_text(
            "Word addition cancelled.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    if text == "1️⃣ → 2️⃣ (Infinitive → Past Simple)":
        context.user_data["form_pair"] = "1-2"
        await update.message.reply_text(
            "Enter the first form of the verb (Infinitive):\n"
            "For example: go",
            reply_markup=ReplyKeyboardMarkup([["❌ Cancel"]], resize_keyboard=True)
        )
    elif text == "2️⃣ → 3️⃣ (Past Simple → Past Participle)":
        context.user_data["form_pair"] = "2-3"
        await update.message.reply_text(
            "Enter the second form of the verb (Past Simple):\n"
            "For example: went",
            reply_markup=ReplyKeyboardMarkup([["❌ Cancel"]], resize_keyboard=True)
        )
    else:
        await update.message.reply_text(
            "Please choose one of the buttons.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    return ADDING_WORD1


async def add_word1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle first word input."""
    text = update.message.text.strip()
    
    if text == "❌ Cancel":
        await update.message.reply_text(
            "Word addition cancelled.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    context.user_data["word1"] = text
    word_type = context.user_data.get("word_type")
    
    if word_type == "translation":
        await update.message.reply_text("Now enter the Russian translation:")
    else:
        form_pair = context.user_data.get("form_pair")
        if form_pair == "1-2":
            await update.message.reply_text(
                "Enter the second form of the verb (Past Simple):\n"
                "For example: went",
                reply_markup=ReplyKeyboardMarkup([["❌ Cancel"]], resize_keyboard=True)
            )
        else:
            await update.message.reply_text(
                "Enter the third form of the verb (Past Participle):\n"
                "For example: gone",
                reply_markup=ReplyKeyboardMarkup([["❌ Cancel"]], resize_keyboard=True)
            )
    
    return ADDING_WORD2


async def add_word2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle second word input."""
    text = update.message.text.strip()
    
    if text == "❌ Cancel":
        await update.message.reply_text(
            "Word addition cancelled.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    context.user_data["word2"] = text
    word_type = context.user_data.get("word_type")
    
    word1 = context.user_data["word1"]
    word2 = context.user_data["word2"]
    
    if word_type == "translation":
        db.add_translation_word(update.effective_user.id, word1, word2)
        
        await update.message.reply_text(
            f"✅ Word added!\n\n"
            f"🔤 {word1} — {word2}",
            reply_markup=MAIN_MENU_KEYBOARD
        )
    else:
        form_pair = context.user_data.get("form_pair")
        db.add_irregular_verb(update.effective_user.id, word1, word2, form_pair)
        
        if form_pair == "1-2":
            form_label = "Infinitive → Past Simple"
        else:
            form_label = "Past Simple → Past Participle"
        
        await update.message.reply_text(
            f"✅ Irregular verb added!\n\n"
            f"📖 {word1} → {word2}\n"
            f"({form_label})",
            reply_markup=MAIN_MENU_KEYBOARD
        )
    
    return ConversationHandler.END


async def cancel_adding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel word adding."""
    await update.message.reply_text(
        "Word addition cancelled.",
        reply_markup=MAIN_MENU_KEYBOARD
    )
    return ConversationHandler.END


def generate_quiz_question(word: dict, all_words: list) -> dict:
    """Generate a quiz question with options."""
    word_type = word["word_type"]
    
    if word_type == "translation":
        ask_english = random.choice([True, False])
        
        if ask_english:
            question = f"What is the translation of: **{word['word1']}**?"
            correct_answer = word["word2"]
            wrong_pool = [w["word2"] for w in all_words if w["id"] != word["id"]]
        else:
            question = f"What is the translation of: **{word['word2']}**?"
            correct_answer = word["word1"]
            wrong_pool = [w["word1"] for w in all_words if w["id"] != word["id"]]
    else:
        form_pair = word.get("word3", "1-2")
        
        if form_pair == "1-2":
            question = f"What is the second form (Past Simple) of: **{word['word1']}**?"
            correct_answer = word["word2"]
            wrong_pool = [w["word2"] for w in all_words if w["id"] != word["id"] and w.get("word3") == "1-2"]
        else:
            question = f"What is the third form (Past Participle) of: **{word['word1']}**?"
            correct_answer = word["word2"]
            wrong_pool = [w["word2"] for w in all_words if w["id"] != word["id"] and w.get("word3") == "2-3"]
    
    wrong_answers = random.sample(wrong_pool, min(3, len(wrong_pool)))
    
    all_answers = [correct_answer] + wrong_answers
    random.shuffle(all_answers)
    
    return {
        "question": question,
        "correct_answer": correct_answer,
        "options": all_answers,
        "word_id": word["id"]
    }


async def start_quiz_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start quiz with all words."""
    user_id = update.effective_user.id
    
    translation_words = db.get_all_words(user_id, "translation")
    irregular_words = db.get_all_words(user_id, "irregular")
    
    all_words = translation_words + irregular_words
    
    if not all_words:
        await update.message.reply_text(
            "You don't have any words added yet! 📭\n"
            "First add some words through the menu.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    random.shuffle(all_words)
    
    context.user_data["quiz_words"] = all_words
    context.user_data["quiz_translation_pool"] = translation_words
    context.user_data["quiz_irregular_pool"] = irregular_words
    context.user_data["quiz_index"] = 0
    context.user_data["quiz_score"] = 0
    context.user_data["quiz_total"] = len(all_words)
    
    return await send_quiz_question(update, context)


async def start_quiz_last30(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start quiz with last 30 words."""
    user_id = update.effective_user.id
    
    translation_words = db.get_last_words(user_id, 30, "translation")
    irregular_words = db.get_last_words(user_id, 30, "irregular")
    
    all_last_words = translation_words + irregular_words
    all_last_words.sort(key=lambda x: x["created_at"], reverse=True)
    all_last_words = all_last_words[:30]
    
    if not all_last_words:
        await update.message.reply_text(
            "You don't have any words added yet! 📭\n"
            "First add some words through the menu.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    random.shuffle(all_last_words)
    
    translation_pool = [w for w in all_last_words if w["word_type"] == "translation"]
    irregular_pool = [w for w in all_last_words if w["word_type"] == "irregular"]
    
    context.user_data["quiz_words"] = all_last_words
    context.user_data["quiz_translation_pool"] = translation_pool
    context.user_data["quiz_irregular_pool"] = irregular_pool
    context.user_data["quiz_index"] = 0
    context.user_data["quiz_score"] = 0
    context.user_data["quiz_total"] = len(all_last_words)
    
    return await send_quiz_question(update, context)


async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send the current quiz question."""
    quiz_words = context.user_data.get("quiz_words", [])
    quiz_index = context.user_data.get("quiz_index", 0)
    
    if quiz_index >= len(quiz_words):
        return await end_quiz(update, context)
    
    current_word = quiz_words[quiz_index]
    
    if current_word["word_type"] == "translation":
        pool = context.user_data["quiz_translation_pool"]
    else:
        pool = context.user_data["quiz_irregular_pool"]
    
    question_data = generate_quiz_question(current_word, pool)
    context.user_data["current_question"] = question_data
    
    keyboard = []
    for i, option in enumerate(question_data["options"]):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"answer_{i}")])
    
    keyboard.append([InlineKeyboardButton("❌ Finish Test", callback_data="quit_quiz")])
    
    progress = f"Question {quiz_index + 1}/{context.user_data['quiz_total']}"
    message_text = f"📊 {progress}\n\n{question_data['question']}"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    return QUIZ_ANSWER


async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quiz answer."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "quit_quiz":
        return await end_quiz(update, context, quit_early=True)
    
    answer_index = int(query.data.replace("answer_", ""))
    question_data = context.user_data.get("current_question")
    
    if not question_data:
        await query.edit_message_text(
            "An error occurred. Start the test again.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    selected_answer = question_data["options"][answer_index]
    correct_answer = question_data["correct_answer"]
    
    if selected_answer == correct_answer:
        context.user_data["quiz_score"] = context.user_data.get("quiz_score", 0) + 1
        result_text = "✅ Correct!"
    else:
        result_text = f"❌ Incorrect!\nCorrect answer: {correct_answer}"
    
    context.user_data["quiz_index"] = context.user_data.get("quiz_index", 0) + 1
    
    keyboard = [[InlineKeyboardButton("➡️ Next Question", callback_data="next_question")]]
    
    await query.edit_message_text(
        f"{result_text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return QUIZ_ANSWER


async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Move to the next question."""
    query = update.callback_query
    await query.answer()
    
    quiz_index = context.user_data.get("quiz_index", 0)
    quiz_words = context.user_data.get("quiz_words", [])
    
    if quiz_index >= len(quiz_words):
        return await end_quiz(update, context)
    
    return await send_quiz_question(update, context)


async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, quit_early: bool = False) -> int:
    """End the quiz and show results."""
    score = context.user_data.get("quiz_score", 0)
    total = context.user_data.get("quiz_total", 0)
    answered = context.user_data.get("quiz_index", 0)
    
    if total > 0:
        percentage = (score / answered * 100) if answered > 0 else 0
    else:
        percentage = 0
    
    if quit_early:
        result_text = (
            f"🏁 Test finished early!\n\n"
            f"📊 Result: {score}/{answered}\n"
            f"📈 Correct percentage: {percentage:.1f}%"
        )
    else:
        if percentage >= 90:
            emoji = "🏆"
        elif percentage >= 70:
            emoji = "👍"
        elif percentage >= 50:
            emoji = "📚"
        else:
            emoji = "💪"
        
        result_text = (
            f"{emoji} Test finished!\n\n"
            f"📊 Result: {score}/{total}\n"
            f"📈 Correct percentage: {percentage:.1f}%"
        )
    
    context.user_data.pop("quiz_words", None)
    context.user_data.pop("quiz_translation_pool", None)
    context.user_data.pop("quiz_irregular_pool", None)
    context.user_data.pop("quiz_index", None)
    context.user_data.pop("quiz_score", None)
    context.user_data.pop("quiz_total", None)
    context.user_data.pop("current_question", None)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(result_text)
        await update.callback_query.message.reply_text(
            "Choose the next action:",
            reply_markup=MAIN_MENU_KEYBOARD
        )
    else:
        await update.message.reply_text(
            result_text,
            reply_markup=MAIN_MENU_KEYBOARD
        )
    
    return ConversationHandler.END


def get_total_pages(total_count: int) -> int:
    """Calculate total number of pages for pagination."""
    return (total_count + DELETE_WORDS_PER_PAGE - 1) // DELETE_WORDS_PER_PAGE


def build_delete_words_keyboard(words: list, page: int, total_count: int) -> InlineKeyboardMarkup:
    """Build inline keyboard for word deletion with pagination."""
    keyboard = []
    
    for word in words:
        if word["word_type"] == "translation":
            label = f"🔤 {word['word1']} — {word['word2']}"
        else:
            label = f"📖 {word['word1']} → {word['word2']}"
        
        # Truncate label if too long for Telegram button
        if len(label) > 40:
            label = label[:37] + "..."
        
        keyboard.append([InlineKeyboardButton(label, callback_data=f"del_word_{word['id']}")])
    
    # Pagination buttons
    nav_buttons = []
    total_pages = get_total_pages(total_count)
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"del_page_{page - 1}"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Forward ➡️", callback_data=f"del_page_{page + 1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="del_close")])
    
    return InlineKeyboardMarkup(keyboard)


async def delete_word_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the word deletion process."""
    user_id = update.effective_user.id
    total_count = db.get_word_count(user_id)
    
    if total_count == 0:
        await update.message.reply_text(
            "You don't have any words added yet! 📭",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    words = db.get_words_paginated(user_id, offset=0, limit=DELETE_WORDS_PER_PAGE)
    keyboard = build_delete_words_keyboard(words, page=0, total_count=total_count)
    
    total_pages = get_total_pages(total_count)
    page_info = f"Page 1/{total_pages}" if total_pages > 1 else ""
    
    await update.message.reply_text(
        f"🗑 Choose a word to delete:\n{page_info}",
        reply_markup=keyboard
    )
    return ConversationHandler.END


async def handle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle delete word callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "del_close":
        await query.edit_message_text("Deletion cancelled.")
        return
    
    if data.startswith("del_page_"):
        page = int(data.replace("del_page_", ""))
        offset = page * DELETE_WORDS_PER_PAGE
        
        total_count = db.get_word_count(user_id)
        words = db.get_words_paginated(user_id, offset=offset, limit=DELETE_WORDS_PER_PAGE)
        
        if not words:
            await query.edit_message_text("Words not found.")
            return
        
        keyboard = build_delete_words_keyboard(words, page=page, total_count=total_count)
        total_pages = get_total_pages(total_count)
        page_info = f"Page {page + 1}/{total_pages}" if total_pages > 1 else ""
        
        await query.edit_message_text(
            f"🗑 Choose a word to delete:\n{page_info}",
            reply_markup=keyboard
        )
        return
    
    if data.startswith("del_word_"):
        word_id = int(data.replace("del_word_", ""))
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes, delete", callback_data=f"del_confirm_{word_id}"),
                InlineKeyboardButton("❌ No", callback_data="del_cancel")
            ]
        ])
        
        await query.edit_message_text(
            "❓ Are you sure you want to delete this word?",
            reply_markup=keyboard
        )
        return
    
    if data.startswith("del_confirm_"):
        word_id = int(data.replace("del_confirm_", ""))
        
        if db.delete_word(user_id, word_id):
            await query.edit_message_text("✅ Word deleted!")
        else:
            await query.edit_message_text("❌ Failed to delete word.")
        return
    
    if data == "del_cancel":
        # Return to word list
        total_count = db.get_word_count(user_id)
        
        if total_count == 0:
            await query.edit_message_text("You have no more words to delete! 📭")
            return
        
        words = db.get_words_paginated(user_id, offset=0, limit=DELETE_WORDS_PER_PAGE)
        keyboard = build_delete_words_keyboard(words, page=0, total_count=total_count)
        total_pages = get_total_pages(total_count)
        page_info = f"Page 1/{total_pages}" if total_pages > 1 else ""
        
        await query.edit_message_text(
            f"🗑 Choose a word to delete:\n{page_info}",
            reply_markup=keyboard
        )


def get_view_total_pages(total_count: int) -> int:
    """Calculate total number of pages for view words pagination."""
    return (total_count + VIEW_WORDS_PER_PAGE - 1) // VIEW_WORDS_PER_PAGE


def build_view_words_message(words: list, page: int, total_pages: int) -> str:
    """Build message text for viewing words."""
    lines = []
    start_num = page * VIEW_WORDS_PER_PAGE + 1
    for i, word in enumerate(words, start=start_num):
        if word["word_type"] == "translation":
            lines.append(f"{i}. 🔤 {word['word1']} — {word['word2']}")
        else:
            lines.append(f"{i}. 📖 {word['word1']} → {word['word2']}")
    
    words_text = "\n".join(lines) if lines else "No words"
    page_info = f"\n\n📄 {page + 1}/{total_pages}"
    legend = "🔤 — translation\n📖 — irregular verb\n"
    
    return f"📚 Your words:\n\n{legend}\n{words_text}{page_info}"


def build_view_words_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Build inline keyboard for viewing words with pagination."""
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"view_page_{page - 1}"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Forward ➡️", callback_data=f"view_page_{page + 1}"))
    
    keyboard = []
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="view_close")])
    
    return InlineKeyboardMarkup(keyboard)


async def view_words_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start viewing words."""
    user_id = update.effective_user.id
    total_count = db.get_word_count(user_id)
    
    if total_count == 0:
        await update.message.reply_text(
            "You don't have any words added yet! 📭",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    words = db.get_words_paginated(user_id, offset=0, limit=VIEW_WORDS_PER_PAGE)
    total_pages = get_view_total_pages(total_count)
    
    message_text = build_view_words_message(words, page=0, total_pages=total_pages)
    keyboard = build_view_words_keyboard(page=0, total_pages=total_pages)
    
    await update.message.reply_text(message_text, reply_markup=keyboard)
    return ConversationHandler.END


async def handle_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle view words callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "view_close":
        await query.edit_message_text("Word list closed.")
        return
    
    if data.startswith("view_page_"):
        page = int(data.replace("view_page_", ""))
        offset = page * VIEW_WORDS_PER_PAGE
        
        total_count = db.get_word_count(user_id)
        words = db.get_words_paginated(user_id, offset=offset, limit=VIEW_WORDS_PER_PAGE)
        
        if not words:
            await query.edit_message_text("Words not found.")
            return
        
        total_pages = get_view_total_pages(total_count)
        message_text = build_view_words_message(words, page=page, total_pages=total_pages)
        keyboard = build_view_words_keyboard(page=page, total_pages=total_pages)
        
        await query.edit_message_text(message_text, reply_markup=keyboard)


async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu button presses."""
    text = update.message.text
    
    if text == "📚 Test All Words":
        await start_quiz_all(update, context)
    elif text == "📝 Test Last 30 Words":
        await start_quiz_last30(update, context)
    elif text == "➕ Add Word":
        await add_word_start(update, context)


def main() -> None:
    """Run the bot."""
    db.init_db()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    add_word_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Add Word$"), add_word_start)
        ],
        states={
            ADDING_TYPE: [CallbackQueryHandler(add_word_type_chosen, pattern="^type_")],
            ADDING_VERB_FORMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_verb_forms_chosen)],
            ADDING_WORD1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_word1)],
            ADDING_WORD2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_word2)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_adding),
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🗑 Delete Word$"), delete_word_start),
            MessageHandler(filters.Regex("^👀 View Words$"), view_words_start),
        ],
    )
    
    quiz_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📚 Test All Words$"), start_quiz_all),
            MessageHandler(filters.Regex("^📝 Test Last 30 Words$"), start_quiz_last30),
        ],
        states={
            QUIZ_ANSWER: [
                CallbackQueryHandler(handle_quiz_answer, pattern="^answer_|^quit_quiz$"),
                CallbackQueryHandler(next_question, pattern="^next_question$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_adding),
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🗑 Delete Word$"), delete_word_start),
            MessageHandler(filters.Regex("^👀 View Words$"), view_words_start),
        ],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(add_word_handler)
    application.add_handler(quiz_handler)
    application.add_handler(MessageHandler(filters.Regex("^🗑 Delete Word$"), delete_word_start))
    application.add_handler(CallbackQueryHandler(handle_delete_callback, pattern="^del_"))
    application.add_handler(MessageHandler(filters.Regex("^👀 View Words$"), view_words_start))
    application.add_handler(CallbackQueryHandler(handle_view_callback, pattern="^view_"))
    
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
