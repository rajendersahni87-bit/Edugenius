"""
EduGenius Hackathon Presentation Generator
Generates a professional .pptx file for the hackathon demo.
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# --- COLOR PALETTE ---
INDIGO = RGBColor(99, 102, 241)       # #6366F1
PURPLE = RGBColor(139, 92, 246)       # #8B5CF6
DARK = RGBColor(30, 41, 59)           # #1E293B
MUTED = RGBColor(100, 116, 139)       # #64748B
WHITE = RGBColor(255, 255, 255)
LIGHT_BG = RGBColor(248, 250, 252)    # #F8FAFC
GREEN = RGBColor(16, 185, 129)        # #10B981
ORANGE = RGBColor(245, 158, 11)       # #F59E0B
RED = RGBColor(239, 68, 68)           # #EF4444
BLUE = RGBColor(59, 130, 246)         # #3B82F6

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def add_gradient_bg(slide, color1=INDIGO, color2=PURPLE):
    """Add a solid dark background (gradient not natively supported easily)."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = DARK

def add_light_bg(slide):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = WHITE

def add_indigo_bg(slide):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = INDIGO

def add_textbox(slide, left, top, width, height, text, font_size=18, color=DARK, bold=False, alignment=PP_ALIGN.LEFT, font_name="Calibri"):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox

def add_bullet_points(slide, left, top, width, height, items, font_size=16, color=DARK, font_name="Calibri"):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = item
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = font_name
        p.space_after = Pt(8)
        p.level = 0
    return txBox

def add_rounded_rect(slide, left, top, width, height, fill_color=INDIGO):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    return shape

def add_card(slide, left, top, width, height, title, content, icon="", card_color=INDIGO):
    """Add a styled card with title and content."""
    rect = add_rounded_rect(slide, left, top, width, height, card_color)
    # Title
    add_textbox(slide, left + 0.2, top + 0.15, width - 0.4, 0.5,
                f"{icon}  {title}" if icon else title,
                font_size=16, color=WHITE, bold=True)
    # Content
    add_textbox(slide, left + 0.2, top + 0.65, width - 0.4, height - 0.8,
                content, font_size=12, color=RGBColor(226, 232, 240))


# =====================================================
# SLIDE 1: TITLE SLIDE
# =====================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
add_gradient_bg(slide)

# Title
add_textbox(slide, 1, 1.5, 11, 1.2, "EduGenius", font_size=60, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

# Tagline
add_textbox(slide, 1, 2.8, 11, 0.8,
            "AI-Powered Education Platform",
            font_size=32, color=RGBColor(167, 139, 250), bold=False, alignment=PP_ALIGN.CENTER)

# Subtitle
add_textbox(slide, 2, 3.8, 9, 0.6,
            "Personalized Learning  \u2022  Smart Planning  \u2022  Progress Analytics",
            font_size=18, color=RGBColor(148, 163, 184), alignment=PP_ALIGN.CENTER)

# Track info
add_rounded_rect(slide, 4.5, 5.2, 4.3, 0.6, PURPLE)
add_textbox(slide, 4.5, 5.25, 4.3, 0.5,
            "Track 4: Education", font_size=18, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

# Team
add_textbox(slide, 1, 6.3, 11, 0.5,
            "Hackathon 2024  |  Team EduGenius",
            font_size=14, color=MUTED, alignment=PP_ALIGN.CENTER)


# =====================================================
# SLIDE 2: THE PROBLEM
# =====================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_light_bg(slide)

add_textbox(slide, 0.8, 0.4, 5, 0.6, "The Problem", font_size=36, color=INDIGO, bold=True)
add_textbox(slide, 0.8, 1.0, 11, 0.4, "Why current education systems struggle", font_size=16, color=MUTED)

# Problem cards - Row 1
add_card(slide, 0.8, 1.8, 3.6, 2.2, "One-Size-Fits-All", "Students learn at different paces, yet content delivery is uniform. No personalization based on strengths or weaknesses.", "\u274c", RED)
add_card(slide, 4.8, 1.8, 3.6, 2.2, "Limited Teacher Time", "Teachers can't provide 1-on-1 attention to every student. Doubt resolution is delayed and inefficient.", "\u23f0", ORANGE)
add_card(slide, 8.8, 1.8, 3.6, 2.2, "No Smart Planning", "Students lack structured study plans. They don't know what to study, when, or how to prioritize weak areas.", "[!]", RGBColor(107, 114, 128))

# Bottom stat
add_rounded_rect(slide, 0.8, 4.5, 11.7, 2.2, DARK)
add_textbox(slide, 1.3, 4.7, 10, 0.5, "The Impact", font_size=22, color=WHITE, bold=True)
add_bullet_points(slide, 1.3, 5.3, 10, 1.2, [
    "\u2022  65% of students say they don't have effective study strategies",
    "\u2022  Only 30% of students receive personalized feedback regularly",
    "\u2022  Students waste 40% of study time on already-mastered topics",
], font_size=15, color=RGBColor(203, 213, 225))


# =====================================================
# SLIDE 3: OUR SOLUTION
# =====================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_light_bg(slide)

add_textbox(slide, 0.8, 0.4, 5, 0.6, "Our Solution", font_size=36, color=INDIGO, bold=True)
add_textbox(slide, 0.8, 1.0, 11, 0.4, "3 integrated AI modules in one platform", font_size=16, color=MUTED)

# Three pillars
add_card(slide, 0.8, 1.8, 3.6, 4.5, "AI Tutor", "RAG-powered conversational tutor that answers questions from YOUR study materials.\n\n\u2713 Socratic Mode (guiding questions)\n\u2713 Direct Mode (clear answers)\n\u2713 Source citations from PDFs\n\u2713 Conversation memory", "", INDIGO)
add_card(slide, 4.8, 1.8, 3.6, 4.5, "Smart Planner", "AI generates personalized study schedules based on your goals and weak areas.\n\n\u2713 Deadline-aware scheduling\n\u2713 Priority-based tasks\n\u2713 Weak topic focus\n\u2713 Adaptive rescheduling", "", PURPLE)
add_card(slide, 8.8, 1.8, 3.6, 4.5, "Progress Dashboard", "Visual analytics that track your learning journey and identify gaps.\n\n\u2713 Study time tracking\n\u2713 Quiz score trends\n\u2713 Subject-wise progress\n\u2713 AI-generated quizzes", "", GREEN)


# =====================================================
# SLIDE 4: SYSTEM ARCHITECTURE
# =====================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_light_bg(slide)

add_textbox(slide, 0.8, 0.4, 8, 0.6, "System Architecture", font_size=36, color=INDIGO, bold=True)

# Architecture layers - visual boxes
# Frontend Layer
add_rounded_rect(slide, 0.8, 1.4, 11.7, 1.2, BLUE)
add_textbox(slide, 1.0, 1.5, 11, 0.4, "Frontend  \u2014  Streamlit", font_size=18, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 1.0, 1.9, 11, 0.4,
            "Dashboard  |  AI Tutor Chat  |  Study Planner  |  Quiz  |  Document Upload",
            font_size=13, color=RGBColor(191, 219, 254), alignment=PP_ALIGN.CENTER)

# Arrow
add_textbox(slide, 6, 2.6, 1, 0.4, "\u2b07", font_size=24, color=MUTED, alignment=PP_ALIGN.CENTER)

# Backend Layer
add_rounded_rect(slide, 0.8, 3.0, 11.7, 1.2, INDIGO)
add_textbox(slide, 1.0, 3.1, 11, 0.4, "Backend  \u2014  FastAPI (Python)", font_size=18, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 1.0, 3.5, 11, 0.4,
            "REST API  |  JWT Auth  |  RAG Engine  |  Planner AI  |  Progress Engine",
            font_size=13, color=RGBColor(199, 210, 254), alignment=PP_ALIGN.CENTER)

# Arrow
add_textbox(slide, 6, 4.2, 1, 0.4, "\u2b07", font_size=24, color=MUTED, alignment=PP_ALIGN.CENTER)

# AI Layer
add_rounded_rect(slide, 0.8, 4.6, 5.6, 1.2, PURPLE)
add_textbox(slide, 1.0, 4.7, 5.2, 0.4, "AI / ML Layer", font_size=18, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 1.0, 5.1, 5.2, 0.4, "Gemini 2.0 Flash  |  LangChain  |  Embeddings",
            font_size=13, color=RGBColor(221, 214, 254), alignment=PP_ALIGN.CENTER)

# Data Layer
add_rounded_rect(slide, 6.9, 4.6, 5.6, 1.2, DARK)
add_textbox(slide, 7.1, 4.7, 5.2, 0.4, "Data Layer", font_size=18, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 7.1, 5.1, 5.2, 0.4, "SQLite (10 tables)  |  ChromaDB (Vectors)  |  File Storage",
            font_size=13, color=RGBColor(203, 213, 225), alignment=PP_ALIGN.CENTER)

# Tech stack badges
add_textbox(slide, 0.8, 6.2, 11.7, 0.5,
            "Python  \u2022  FastAPI  \u2022  Streamlit  \u2022  LangChain  \u2022  ChromaDB  \u2022  Gemini AI  \u2022  SQLAlchemy  \u2022  Plotly",
            font_size=14, color=MUTED, alignment=PP_ALIGN.CENTER)


# =====================================================
# SLIDE 5: RAG PIPELINE
# =====================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_light_bg(slide)

add_textbox(slide, 0.8, 0.4, 8, 0.6, "RAG Pipeline", font_size=36, color=INDIGO, bold=True)
add_textbox(slide, 0.8, 1.0, 11, 0.4, "How the AI Tutor generates grounded, accurate answers", font_size=16, color=MUTED)

# Step 1
add_rounded_rect(slide, 0.8, 1.8, 2.7, 2.5, BLUE)
add_textbox(slide, 1.0, 1.9, 2.3, 0.4, "1. Ingest", font_size=20, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 1.0, 2.4, 2.3, 1.5,
            "Upload PDF\n\u2193\nExtract Text\n\u2193\nSemantic Chunking\n(800 tokens, 200 overlap)",
            font_size=12, color=RGBColor(191, 219, 254), alignment=PP_ALIGN.CENTER)

# Arrow
add_textbox(slide, 3.5, 2.6, 0.5, 0.5, "\u27a1", font_size=28, color=INDIGO, alignment=PP_ALIGN.CENTER)

# Step 2
add_rounded_rect(slide, 4.0, 1.8, 2.7, 2.5, INDIGO)
add_textbox(slide, 4.2, 1.9, 2.3, 0.4, "2. Embed", font_size=20, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 4.2, 2.4, 2.3, 1.5,
            "Chunks\n\u2193\nall-MiniLM-L6-v2\n\u2193\nVector Embeddings\n\u2193\nStore in ChromaDB",
            font_size=12, color=RGBColor(199, 210, 254), alignment=PP_ALIGN.CENTER)

# Arrow
add_textbox(slide, 6.7, 2.6, 0.5, 0.5, "\u27a1", font_size=28, color=INDIGO, alignment=PP_ALIGN.CENTER)

# Step 3
add_rounded_rect(slide, 7.2, 1.8, 2.7, 2.5, PURPLE)
add_textbox(slide, 7.4, 1.9, 2.3, 0.4, "3. Retrieve", font_size=20, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 7.4, 2.4, 2.3, 1.5,
            "Student Question\n\u2193\nEmbed Query\n\u2193\nCosine Similarity\n\u2193\nTop-5 Chunks",
            font_size=12, color=RGBColor(221, 214, 254), alignment=PP_ALIGN.CENTER)

# Arrow
add_textbox(slide, 9.9, 2.6, 0.5, 0.5, "\u27a1", font_size=28, color=INDIGO, alignment=PP_ALIGN.CENTER)

# Step 4
add_rounded_rect(slide, 10.4, 1.8, 2.1, 2.5, GREEN)
add_textbox(slide, 10.5, 1.9, 1.9, 0.4, "4. Generate", font_size=20, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 10.5, 2.4, 1.9, 1.5,
            "Context +\nChat History\n\u2193\nGemini LLM\n\u2193\nGrounded Answer",
            font_size=12, color=RGBColor(187, 247, 208), alignment=PP_ALIGN.CENTER)

# Key Config Box
add_rounded_rect(slide, 0.8, 4.8, 11.7, 1.8, RGBColor(241, 245, 249))
add_textbox(slide, 1.3, 4.9, 10, 0.4, "RAG Configuration", font_size=18, color=DARK, bold=True)
add_bullet_points(slide, 1.3, 5.4, 5, 1.0, [
    "\u2022  Chunk Size: 800 tokens (200 overlap)",
    "\u2022  Embedding: all-MiniLM-L6-v2 (local, free)",
    "\u2022  Vector DB: ChromaDB (persistent)",
], font_size=14, color=DARK)
add_bullet_points(slide, 7.0, 5.4, 5, 1.0, [
    "\u2022  Similarity: Cosine (Top-5 retrieval)",
    "\u2022  LLM: Gemini 2.0 Flash (free tier)",
    "\u2022  Modes: Socratic + Direct teaching",
], font_size=14, color=DARK)


# =====================================================
# SLIDE 6: DATABASE SCHEMA
# =====================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_light_bg(slide)

add_textbox(slide, 0.8, 0.4, 8, 0.6, "Database Schema", font_size=36, color=INDIGO, bold=True)
add_textbox(slide, 0.8, 1.0, 11, 0.4, "10 normalized tables powering the platform", font_size=16, color=MUTED)

tables = [
    ("Users", "id, name, email,\npassword_hash, role", INDIGO),
    ("Subjects", "id, name, description,\nuser_id (FK)", PURPLE),
    ("Documents", "id, subject_id, filename,\nfile_path, chunk_count", BLUE),
    ("Study Plans", "id, user_id, subject_id,\ntitle, schedule (JSON)", GREEN),
    ("Study Tasks", "id, plan_id, title,\npriority, status, due_date", ORANGE),
    ("Study Sessions", "id, user_id, task_id,\nstart/end, focus_score", RGBColor(107, 114, 128)),
    ("Quizzes", "id, subject_id, title,\nquestions (JSON)", RED),
    ("Quiz Results", "id, user_id, quiz_id,\nscore, answers (JSON)", RGBColor(236, 72, 153)),
    ("Chat History", "id, user_id, role,\nmessage, sources (JSON)", RGBColor(14, 165, 233)),
    ("Progress", "id, user_id, completion%,\navg_score, study_mins", RGBColor(168, 85, 247)),
]

for i, (name, fields, color) in enumerate(tables):
    col = i % 5
    row = i // 5
    x = 0.8 + col * 2.45
    y = 1.6 + row * 2.6
    add_card(slide, x, y, 2.2, 2.0, name, fields, "", color)


# =====================================================
# SLIDE 7: KEY FEATURES
# =====================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_light_bg(slide)

add_textbox(slide, 0.8, 0.4, 8, 0.6, "Key Features", font_size=36, color=INDIGO, bold=True)

features = [
    ("", "Socratic Teaching", "AI asks guiding questions\ninstead of giving answers", INDIGO),
    ("", "RAG from YOUR Notes", "Answers grounded in your\nuploaded study materials", PURPLE),
    ("", "AI Study Plans", "Personalized schedules\nbased on deadlines & gaps", GREEN),
    ("", "Auto Quizzes", "AI generates MCQs from\nyour content + auto-grades", BLUE),
    ("", "Progress Analytics", "Track study hours, scores,\nand completion rates", ORANGE),
    ("", "Secure Auth", "JWT-based authentication\nwith bcrypt passwords", DARK),
]

for i, (icon, title, desc, color) in enumerate(features):
    col = i % 3
    row = i // 3
    x = 0.8 + col * 4.1
    y = 1.4 + row * 2.8
    
    add_rounded_rect(slide, x, y, 3.7, 2.3, color)
    add_textbox(slide, x + 0.3, y + 0.2, 3.1, 0.5, f"{icon}  {title}", font_size=20, color=WHITE, bold=True)
    add_textbox(slide, x + 0.3, y + 0.85, 3.1, 1.2, desc, font_size=14, color=RGBColor(226, 232, 240))


# =====================================================
# SLIDE 8: DEMO FLOW
# =====================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_light_bg(slide)

add_textbox(slide, 0.8, 0.4, 8, 0.6, "Demo Walkthrough", font_size=36, color=INDIGO, bold=True)

steps = [
    ("1", "Register", "Create account"),
    ("2", "Add Subject", "e.g. Data Structures"),
    ("3", "Upload PDF", "Study materials"),
    ("4", "Chat with AI", "Ask questions"),
    ("5", "Get Study Plan", "AI-generated schedule"),
    ("6", "Take Quiz", "Auto-generated MCQs"),
    ("7", "View Dashboard", "Track progress"),
]

for i, (num, title, desc) in enumerate(steps):
    x = 0.5 + i * 1.8
    # Circle with number
    add_rounded_rect(slide, x + 0.3, 1.5, 1.0, 1.0, INDIGO if i % 2 == 0 else PURPLE)
    add_textbox(slide, x + 0.3, 1.6, 1.0, 0.8, num, font_size=28, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
    # Title
    add_textbox(slide, x, 2.7, 1.6, 0.4, title, font_size=14, color=DARK, bold=True, alignment=PP_ALIGN.CENTER)
    # Description
    add_textbox(slide, x, 3.1, 1.6, 0.4, desc, font_size=11, color=MUTED, alignment=PP_ALIGN.CENTER)
    # Arrow (except last)
    if i < len(steps) - 1:
        add_textbox(slide, x + 1.5, 1.7, 0.5, 0.5, "\u27a1", font_size=20, color=MUTED, alignment=PP_ALIGN.CENTER)

# Live Demo banner
add_rounded_rect(slide, 2.5, 4.2, 8.3, 2.5, DARK)
add_textbox(slide, 3.0, 4.4, 7.3, 0.5, "  Live Demo", font_size=28, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 3.0, 5.1, 7.3, 0.4, "Backend: http://localhost:8000/docs", font_size=16, color=RGBColor(129, 140, 248), alignment=PP_ALIGN.CENTER)
add_textbox(slide, 3.0, 5.6, 7.3, 0.4, "Frontend: http://localhost:8501", font_size=16, color=RGBColor(129, 140, 248), alignment=PP_ALIGN.CENTER)
add_textbox(slide, 3.0, 6.1, 7.3, 0.4, "API Docs: http://localhost:8000/docs (Swagger UI)", font_size=14, color=MUTED, alignment=PP_ALIGN.CENTER)


# =====================================================
# SLIDE 9: TECH STACK
# =====================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_light_bg(slide)

add_textbox(slide, 0.8, 0.4, 8, 0.6, "Tech Stack", font_size=36, color=INDIGO, bold=True)

stack = [
    ("Frontend", "Streamlit + Plotly", "Rapid UI, interactive charts,\nresponsive dashboard", BLUE),
    ("Backend", "FastAPI (Python)", "Async REST API, auto-docs,\ntype-safe validation", INDIGO),
    ("AI / LLM", "Google Gemini 2.0 Flash", "Free tier, fast inference,\nJSON mode for structured output", PURPLE),
    ("RAG", "LangChain + ChromaDB", "Document chunking, embeddings,\nsemantic search", GREEN),
    ("Database", "SQLite + SQLAlchemy", "10-table schema, ORM,\nzero-config for hackathon", ORANGE),
    ("Auth", "JWT + bcrypt", "Stateless tokens, secure\npassword hashing", DARK),
]

for i, (layer, tech, desc, color) in enumerate(stack):
    col = i % 3
    row = i // 3
    x = 0.8 + col * 4.1
    y = 1.3 + row * 2.8
    add_card(slide, x, y, 3.7, 2.3, f"{layer}: {tech}", desc, "", color)


# =====================================================
# SLIDE 10: FUTURE SCOPE
# =====================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_light_bg(slide)

add_textbox(slide, 0.8, 0.4, 8, 0.6, "Future Roadmap", font_size=36, color=INDIGO, bold=True)
add_textbox(slide, 0.8, 1.0, 11, 0.4, "What's next for EduGenius", font_size=16, color=MUTED)

roadmap = [
    ("Phase 2", "Multi-modal Learning", "Support for images, diagrams,\nand video content in RAG", BLUE),
    ("Phase 2", "Collaborative Study", "Study groups, shared notes,\npeer Q&A forums", INDIGO),
    ("Phase 3", "Voice Tutoring", "Speech-to-text + text-to-speech\nfor conversational learning", PURPLE),
    ("Phase 3", "Teacher Dashboard", "Class-wide analytics, auto\nassignment grading", GREEN),
    ("Phase 4", "Mobile App", "React Native app with\noffline study mode", ORANGE),
    ("Phase 4", "Gamification", "XP points, streaks, badges,\nleaderboards for engagement", RED),
]

for i, (phase, title, desc, color) in enumerate(roadmap):
    col = i % 3
    row = i // 3
    x = 0.8 + col * 4.1
    y = 1.6 + row * 2.6
    add_card(slide, x, y, 3.7, 2.1, f"{title}", f"{phase}\n{desc}", "", color)


# =====================================================
# SLIDE 11: THANK YOU
# =====================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_gradient_bg(slide)

add_textbox(slide, 1, 1.5, 11, 1.0, "Thank You!", font_size=54, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 1, 2.8, 11, 0.8,
            "EduGenius  \u2014  Learn Smarter with AI",
            font_size=28, color=RGBColor(167, 139, 250), alignment=PP_ALIGN.CENTER)

# Contact info box
add_rounded_rect(slide, 3.5, 4.0, 6.3, 2.2, RGBColor(49, 46, 129))
add_textbox(slide, 3.8, 4.2, 5.7, 0.4, "Try It Now", font_size=22, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 3.8, 4.7, 5.7, 0.4, "Backend:  localhost:8000/docs", font_size=16, color=RGBColor(165, 180, 252), alignment=PP_ALIGN.CENTER)
add_textbox(slide, 3.8, 5.2, 5.7, 0.4, "Frontend:  localhost:8501", font_size=16, color=RGBColor(165, 180, 252), alignment=PP_ALIGN.CENTER)
add_textbox(slide, 3.8, 5.7, 5.7, 0.4, "GitHub:  github.com/edugenius", font_size=14, color=MUTED, alignment=PP_ALIGN.CENTER)

add_textbox(slide, 1, 6.5, 11, 0.4, "Built with \u2764\ufe0f for Hackathon 2024  |  Track 4: Education",
            font_size=14, color=MUTED, alignment=PP_ALIGN.CENTER)


# =====================================================
# SAVE
# =====================================================
output_path = "EduGenius_Hackathon_Presentation.pptx"
prs.save(output_path)
print(f"Presentation saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
