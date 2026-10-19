<p align="center">
  <img src="assets/logo.png" width="220" alt="RP+ Translator Logo" />
</p>

<h1 align="center">RP+ Translator</h1>

<p align="center">
  <b>Next-Generation AI Translation & Dialogue Comprehension HUD for GTA Roleplay</b><br>
  <i>Empowering seamless cross-language roleplay across FiveM, SA-MP, RAGEMP, and Alt:V.</i>
</p>

<p align="center">
  <a href="https://github.com/marioamriansyah/RP-Translator/releases/latest"><img src="https://img.shields.io/github/v/release/marioamriansyah/RP-Translator?style=for-the-badge&color=0A84FF&label=Latest%20Release" alt="Latest Release"></a>
  <a href="https://github.com/marioamriansyah/RP-Translator/releases"><img src="https://img.shields.io/github/downloads/marioamriansyah/RP-Translator/total?style=for-the-badge&color=30D158&label=Downloads" alt="Downloads"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows Platform">
  <img src="https://img.shields.io/badge/Engine-Groq%20LPU%20AI-F55036?style=for-the-badge&logo=fastapi&logoColor=white" alt="Groq AI">
  <img src="https://img.shields.io/badge/License-MIT-gray?style=for-the-badge" alt="MIT License">
</p>

---

## Overview

**RP+ Translator** is an ultra-fast, professional dark-utility desktop application engineered specifically for GTA Roleplay (RP) communities. Playing in international English-speaking roleplay servers can be challenging when navigating street slangs, rapid police radio chatter, or regional crime syndicate dialects.

RP+ Translator bridges language barriers directly inside your game with **zero immersion break**:
- **Translate Your Thoughts (Indonesian to RP English Slang)**: Turn casual Indonesian thoughts into authentic GTA RP dialogues with 5 selectable persona styles (*LA Street, Cartel Mexico, Mafia Italy, British Formal, American Formal*).
- **Understand Other Players Instantly (English Slang to Indonesian)**: Press **`F1`** to translate and demystify complex English roleplay chat, idioms, and slang on the fly.
- **In-Game HUD / OSD Overlay**: Results float directly on your game screen with customizable transparency, repositioning, and auto-hide timers.
- **100% Standalone**: Packed with an integrated Tesseract OCR engine and trained bilingual data—no external command line or dependencies needed.

---

## Key Features

### 1. F1 RP Dialogue Comprehension (Arti RP Chat)
Never get lost in roleplay conversations again. When an international player sends a rapid chat filled with unfamiliar street slang, abbreviations, or idioms:
- Press **`F5`** or **`F1`** to instantly analyze incoming messages.
- The **F1 Meaning Engine** analyzes the context and translates the roleplay intent directly into clean, easily understood Indonesian.
- Displayed prominently in the dedicated **Purple Meaning Card** in the application and on your in-game OSD.

### 2. Dual-Zone High-DPI Screen OCR
- **`F4` (Input Bar)**: Dedicated to capturing what you are currently typing in the game chatbox. Automatically eliminates blinking text cursors (`|`, `_`) and RP command prefixes (`/me`, `/do`, `say:`).
- **`F5` (Chatlog History)**: Captures incoming multi-line dialogue boxes from other players. Automatically joins wrapped lines into a cohesive sentence without cutting off early context.
- **Visual Snip Box Overlays**: Easily reposition and resize capture areas directly on your screen using interactive handles.
- **Smart Snapshot Auto-Hide**: Guide overlays automatically conceal themselves for a split second during capture so borders never pollute OCR accuracy.

### 3. Draggable & Resizable In-Game OSD
- **Interactive Repositioning**: Click and drag the in-game OSD anywhere on your screen (e.g., above your minimap, near the radar, or top-center).
- **Real-Time Size Adjustments**: Adjust the width and height of the OSD dynamically to match your monitor resolution.
- **Custom Aesthetic**: Fine-tune font sizes, text accent colors, and background opacity to match your gaming aesthetic.
- **Multi-Monitor Coordinate Alignment**: Seamlessly supports multi-monitor rigs and secondary displays without coordinate skewing.

### 4. 5 Distinct Roleplay Personas
Choose from 5 carefully curated roleplay speech styles tailored for GTA storytelling:
- **LA Street Gangster**: West Coast slang, rhythmic, gritty, authentic street vernacular (*e.g., "Aight bet, pull up on 'em blood"*).
- **Cartel Mexico**: Bilingual Hispanic flair, gritty and authoritative (*e.g., "Tranquilo hermano, handle the shipment clean"*).
- **Mafia Italy**: Cosa Nostra respect, organized crime phrasing, formal yet intimidating (*e.g., "Capisce, we settle our debts with honor"*).
- **British Formal**: Articulate, upper-class British phrasing, polite and restrained.
- **American Formal**: Contemporary natural US English, ideal for Department of Justice, Police Department (LSPD), or EMS roleplay.

### 5. Dual-Tier Speed Engine (Local Slang + Groq AI)
- **0 ms Local Slang Library**: Over 1,000+ hand-crafted roleplay idioms and phrases mapped locally for instantaneous offline translation without API consumption.
- **Groq LPU Cloud AI**: Powered by ultra-fast models (`qwen/qwen3.8-27b` / `llama-3.3-70b-versatile`) with under-second inference times and strict GTA RP world filter preservation (LSPD, FIB, Sandy Shores, Vinewood, etc.).

### 6. Clean Pro Utility Architecture
- **Zero Emojis**: Purposefully designed without tacky emojis, keeping the interface minimal, tactical, and clean.
- **Silent Operation**: Windows system chimes and beeps are fully muted during hotkey execution for an undisturbed gaming experience.
- **Hardware-Level Polling**: Global hotkeys bypass exclusive DirectX window locks, ensuring your keys always register even in high-stress FiveM shootouts.

---

## Global Hotkey Reference

| Hotkey | Action | Description |
|:---:|:---|:---|
| <kbd>F1</kbd> | **RP Chat Comprehension** | Translates incoming player chat from English slang into Indonesian meaning. |
| <kbd>F4</kbd> | **Input Chat Translate** | Captures your typed chatline, translates to English RP slang, and prepares it for game entry. |
| <kbd>F5</kbd> | **Capture Chatlog** | Captures the entire incoming chatlog snip box for translation. |
| <kbd>Ctrl</kbd> + <kbd>1</kbd> | **Copy Option 1** | Copies translation variant 1 to your clipboard. |
| <kbd>Ctrl</kbd> + <kbd>2</kbd> | **Copy Option 2** | Copies translation variant 2 to your clipboard. |
| <kbd>Ctrl</kbd> + <kbd>3</kbd> | **Copy Option 3** | Copies translation variant 3 to your clipboard. |
| <kbd>Insert</kbd> | **Toggle App Window** | Minimizes or brings the main RP+ Translator window to the front. |
| <kbd>Page Up</kbd> / <kbd>Page Down</kbd> | **Scroll In-Game OSD** | Scrolls long dialogue history inside the floating game overlay. |

---

## Installation & Setup

### Method 1: Windows Setup Installer (Recommended for Players)

1. Head over to the [**Latest GitHub Releases**](https://github.com/marioamriansyah/RP-Translator/releases/latest).
2. Download **`RP_Plus_Translator_Setup.exe`**.
3. Run the installer wizard. It will automatically bundle:
   - Complete Tesseract OCR binary engine with English & Indonesian language sets.
   - Desktop and Start Menu shortcuts with official branding.
   - Default configuration files and slang dictionary.
4. Launch **RP+ Translator** from your Desktop.
5. On first launch, enter your free **Groq API Key** in the setup dialog (instructions below).

---

### Method 2: Running from Source (For Developers)

#### Prerequisites
- Windows 10 / 11 (64-bit)
- Python 3.10 or higher
- Git

#### Quick Start
```bash
# 1. Clone this repository
git clone https://github.com/marioamriansyah/RP-Translator.git
cd RP-Translator

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install required dependencies
pip install -r requirements.txt

# 4. Launch the application
python main.py
```

---

## Getting a Free Groq API Key

RP+ Translator uses Groq's high-speed LPU inference engine for conversational translations:

1. Visit the [Groq Cloud Console](https://console.groq.com/keys).
2. Sign in with your Google or GitHub account (100% Free).
3. Click **Create API Key**, name it `RP-Translator`, and copy the generated key (`gsk_...`).
4. Paste the key into the prompt when opening RP+ Translator, or click **Settings** &rarr; **API Key**.

---

## How It Works

```
                   +----------------------------------+
                   |       GTA Game Screen            |
                   |   (FiveM / SAMP / RAGEMP)        |
                   +-----------------+----------------+
                                     |
                                     | [F4 / F5 / F1 Hotkeys]
                                     v
                   +----------------------------------+
                   |  PyQt6 Native Win32 Screen Grab  |
                   |   (DirectX & High-DPI Support)   |
                   +-----------------+----------------+
                                     |
                                     v
                   +----------------------------------+
                   |    Tesseract OCR Engine          |
                   |    (Bilingual: Ind + Eng)        |
                   +-----------------+----------------+
                                     |
                                     v
                   +-----------------+----------------+
                   | Is it in Local Slang Library?    |
                   +--------+----------------+--------+
                            |                |
                     [YES]  |                | [NO]
                            v                v
                   +----------------+  +----------------------+
                   | Instant 0ms    |  | Groq Cloud AI Engine |
                   | Local Match    |  | (Persona Styling)    |
                   +--------+-------+  +----------+-----------+
                            |                     |
                            +----------+----------+
                                       |
                                       v
                   +----------------------------------+
                   |  Results Broadcast:              |
                   |  - Draggable In-Game OSD HUD     |
                   |  - Main App Result Cards         |
                   |  - Direct Auto-Typing to Game    |
                   +----------------------------------+
```

---

## Configuration & Tuning

All settings are stored in [`config.json`](config.json) and can be configured through the **Settings Dialog** in the UI:
- **Snip Box Adjustment**: Click `Snip Input` or `Snip Chat` to visually click and drag bounding boxes around your game's chatbox.
- **OSD Customization**: Toggle OSD on/off, change background darkness, text color, font sizes, and duration timer.
- **Model Selection**: Switch between `qwen/qwen3.8-27b`, `llama-3.3-70b-versatile`, or other Groq-supported endpoints.

---

## Safety & Fair Play Disclaimer

- **Anti-Cheat Safe**: RP+ Translator operates strictly as an external desktop accessibility tool via standard Windows Desktop Duplication and GDI/DirectX screenshot APIs. It **never** injects code, hooks game memory, or modifies game executables (`GTA5.exe`, `FiveM.exe`, `gta_sa.exe`).
- **Optimal Display Mode**: Run your game in **Borderless Windowed** or **Windowed Mode** so the floating OSD HUD overlay renders seamlessly above your game.

---

## Contributing

Contributions, slang additions, and bug reports are warmly welcome!
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/NewRPFeature`).
3. Commit your Changes (`git commit -m 'feat: Add new RP feature'`).
4. Push to the Branch (`git push origin feature/NewRPFeature`).
5. Open a Pull Request.

---

## License

Distributed under the **MIT License**. See `LICENSE` for more information.

<p align="center">
  Built with dedication for the GTA Roleplay Community.<br>
  <b>RP+ Translator &copy; 2026</b>
</p>
