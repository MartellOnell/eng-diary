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
        ["📚 Тест по всем словам"],
        ["📝 Тест по 30 последним словам"],
        ["➕ Добавить слово"]
    ],
    resize_keyboard=True
)

ADDING_TYPE, ADDING_VERB_FORMS, ADDING_WORD1, ADDING_WORD2 = range(4)
QUIZ_ANSWER = range(4, 5)[0]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    is_new = db.register_user(user.id, user.username, user.first_name)
    
    if is_new:
        welcome_text = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Добро пожаловать в бот для изучения английского языка!\n\n"
            "Здесь ты можешь:\n"
            "📚 Проходить тесты по всем добавленным словам\n"
            "📝 Тестировать последние 30 слов\n"
            "➕ Добавлять новые слова (переводы и неправильные глаголы)\n\n"
            "Выбери действие из меню ниже:"
        )
    else:
        welcome_text = (
            f"С возвращением, {user.first_name}! 👋\n\n"
            "Выбери действие из меню ниже:"
        )
    
    await update.message.reply_text(welcome_text, reply_markup=MAIN_MENU_KEYBOARD)


async def add_word_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the word adding process."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔤 Перевод (English ↔ Русский)", callback_data="type_translation")],
        [InlineKeyboardButton("📖 Неправильный глагол (3 формы)", callback_data="type_irregular")]
    ])
    
    await update.message.reply_text(
        "Какой тип слова ты хочешь добавить?",
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
            "Введи английское слово:"
        )
        return ADDING_WORD1
    else:
        keyboard = ReplyKeyboardMarkup(
            [
                ["1️⃣ → 2️⃣ (Infinitive → Past Simple)"],
                ["2️⃣ → 3️⃣ (Past Simple → Past Participle)"],
                ["❌ Отмена"]
            ],
            resize_keyboard=True
        )
        await query.edit_message_text(
            "Выбери какие формы неправильного глагола ты хочешь добавить:"
        )
        await query.message.reply_text(
            "Выбери пару форм:",
            reply_markup=keyboard
        )
        return ADDING_VERB_FORMS


async def add_verb_forms_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle verb forms selection."""
    text = update.message.text
    
    if text == "❌ Отмена":
        await update.message.reply_text(
            "Добавление слова отменено.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    if text == "1️⃣ → 2️⃣ (Infinitive → Past Simple)":
        context.user_data["form_pair"] = "1-2"
        await update.message.reply_text(
            "Введи первую форму глагола (Infinitive):\n"
            "Например: go",
            reply_markup=ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)
        )
    elif text == "2️⃣ → 3️⃣ (Past Simple → Past Participle)":
        context.user_data["form_pair"] = "2-3"
        await update.message.reply_text(
            "Введи вторую форму глагола (Past Simple):\n"
            "Например: went",
            reply_markup=ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)
        )
    else:
        await update.message.reply_text(
            "Пожалуйста, выбери одну из кнопок.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    return ADDING_WORD1


async def add_word1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle first word input."""
    text = update.message.text.strip()
    
    if text == "❌ Отмена":
        await update.message.reply_text(
            "Добавление слова отменено.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    context.user_data["word1"] = text
    word_type = context.user_data.get("word_type")
    
    if word_type == "translation":
        await update.message.reply_text("Теперь введи перевод на русский:")
    else:
        form_pair = context.user_data.get("form_pair")
        if form_pair == "1-2":
            await update.message.reply_text(
                "Введи вторую форму глагола (Past Simple):\n"
                "Например: went",
                reply_markup=ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)
            )
        else:
            await update.message.reply_text(
                "Введи третью форму глагола (Past Participle):\n"
                "Например: gone",
                reply_markup=ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)
            )
    
    return ADDING_WORD2


async def add_word2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle second word input."""
    text = update.message.text.strip()
    
    if text == "❌ Отмена":
        await update.message.reply_text(
            "Добавление слова отменено.",
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
            f"✅ Слово добавлено!\n\n"
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
            f"✅ Неправильный глагол добавлен!\n\n"
            f"📖 {word1} → {word2}\n"
            f"({form_label})",
            reply_markup=MAIN_MENU_KEYBOARD
        )
    
    return ConversationHandler.END


async def cancel_adding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel word adding."""
    await update.message.reply_text(
        "Добавление слова отменено.",
        reply_markup=MAIN_MENU_KEYBOARD
    )
    return ConversationHandler.END


def generate_quiz_question(word: dict, all_words: list) -> dict:
    """Generate a quiz question with options."""
    word_type = word["word_type"]
    
    if word_type == "translation":
        ask_english = random.choice([True, False])
        
        if ask_english:
            question = f"Как переводится слово: **{word['word1']}**?"
            correct_answer = word["word2"]
            wrong_pool = [w["word2"] for w in all_words if w["id"] != word["id"]]
        else:
            question = f"Как переводится: **{word['word2']}**?"
            correct_answer = word["word1"]
            wrong_pool = [w["word1"] for w in all_words if w["id"] != word["id"]]
    else:
        form_pair = word.get("word3", "1-2")
        
        if form_pair == "1-2":
            question = f"Какая вторая форма (Past Simple) глагола: **{word['word1']}**?"
            correct_answer = word["word2"]
            wrong_pool = [w["word2"] for w in all_words if w["id"] != word["id"] and w.get("word3") == "1-2"]
        else:
            question = f"Какая третья форма (Past Participle) глагола: **{word['word1']}**?"
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
            "У тебя пока нет добавленных слов! 📭\n"
            "Сначала добавь несколько слов через меню.",
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
            "У тебя пока нет добавленных слов! 📭\n"
            "Сначала добавь несколько слов через меню.",
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
    
    keyboard.append([InlineKeyboardButton("❌ Завершить тест", callback_data="quit_quiz")])
    
    progress = f"Вопрос {quiz_index + 1}/{context.user_data['quiz_total']}"
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
            "Произошла ошибка. Начни тест заново.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    selected_answer = question_data["options"][answer_index]
    correct_answer = question_data["correct_answer"]
    
    if selected_answer == correct_answer:
        context.user_data["quiz_score"] = context.user_data.get("quiz_score", 0) + 1
        result_text = "✅ Правильно!"
    else:
        result_text = f"❌ Неправильно!\nПравильный ответ: {correct_answer}"
    
    context.user_data["quiz_index"] = context.user_data.get("quiz_index", 0) + 1
    
    keyboard = [[InlineKeyboardButton("➡️ Следующий вопрос", callback_data="next_question")]]
    
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
            f"🏁 Тест завершён досрочно!\n\n"
            f"📊 Результат: {score}/{answered}\n"
            f"📈 Процент правильных: {percentage:.1f}%"
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
            f"{emoji} Тест завершён!\n\n"
            f"📊 Результат: {score}/{total}\n"
            f"📈 Процент правильных: {percentage:.1f}%"
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
            "Выбери следующее действие:",
            reply_markup=MAIN_MENU_KEYBOARD
        )
    else:
        await update.message.reply_text(
            result_text,
            reply_markup=MAIN_MENU_KEYBOARD
        )
    
    return ConversationHandler.END


async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu button presses."""
    text = update.message.text
    
    if text == "📚 Тест по всем словам":
        await start_quiz_all(update, context)
    elif text == "📝 Тест по 30 последним словам":
        await start_quiz_last30(update, context)
    elif text == "➕ Добавить слово":
        await add_word_start(update, context)


def main() -> None:
    """Run the bot."""
    db.init_db()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    add_word_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Добавить слово$"), add_word_start)
        ],
        states={
            ADDING_TYPE: [CallbackQueryHandler(add_word_type_chosen, pattern="^type_")],
            ADDING_VERB_FORMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_verb_forms_chosen)],
            ADDING_WORD1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_word1)],
            ADDING_WORD2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_word2)],
        },
        fallbacks=[CommandHandler("cancel", cancel_adding), CommandHandler("start", start)],
    )
    
    quiz_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📚 Тест по всем словам$"), start_quiz_all),
            MessageHandler(filters.Regex("^📝 Тест по 30 последним словам$"), start_quiz_last30),
        ],
        states={
            QUIZ_ANSWER: [
                CallbackQueryHandler(handle_quiz_answer, pattern="^answer_|^quit_quiz$"),
                CallbackQueryHandler(next_question, pattern="^next_question$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_adding), CommandHandler("start", start)],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(add_word_handler)
    application.add_handler(quiz_handler)
    
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
