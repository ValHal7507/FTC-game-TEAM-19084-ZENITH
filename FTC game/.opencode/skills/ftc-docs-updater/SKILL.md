---
name: ftc-docs-updater
description: >
  Auto-updates CONTEXT.md (English) and CONTROLS.md (Romanian) for the FTC DECODE Match Simulator project.
  Use this skill whenever the user says "update docs", "update documentation", "document changes",
  "sync docs", "refresh docs", "update CONTEXT.md", "update CONTROLS.md", or any variation of
  "update", "document", "sync", "refresh" in the context of project documentation. Also trigger
  when the user asks to "document what changed" or "what's new" after making code changes.
---

# FTC Docs Updater

Automatically regenerates `CONTEXT.md` (English, technical) and `CONTROLS.md` (Romanian, user-facing) by reading all source files in the project.

## Workflow

### Step 1: Identify the project root

The project root is the directory containing `main.py`. From the skill location, it is:
```
C:\Users\val3nt_n\Desktop\Coding\Python\FTC-game-TEAM-19084-ZENITH\FTC game\
```

### Step 2: Read ALL source files

Read every `.py` file in the project root. These are the files that define the project:

- `main.py`
- `config.py`
- `game_state.py`
- `drawing.py`
- `drawing_1v1.py`
- `game_logic.py`
- `game_logic_p2.py`
- `input_handler.py`
- `input_handler_p2.py`
- `menu.py`
- `mode_solo.py`
- `mode_1v1.py`
- `ai_controller.py`

Also read the existing `CONTEXT.md` and `CONTROLS.md` to understand the current documentation structure and format.

### Step 3: Update CONTEXT.md (English)

Regenerate `CONTEXT.md` to accurately reflect the current source code. Follow this structure exactly:

1. **Title and intro** — "FTC DECODE Match Simulator — Project Context"
2. **Project Structure** — file tree with one-line descriptions
3. **Module Breakdown** — one section per `.py` file, documenting:
   - All public functions/classes with their signatures and behavior
   - All module-level constants and their values
   - Key internal mechanics (physics, threading, caching, etc.)
   - CONFIG dict entries with current values
   - Color palette entries
4. **Game Flow** — Solo, 1v1 mode walkthroughs
5. **Threading Architecture** — ASCII diagram of main vs physics thread
6. **Key Design Decisions** — architectural choices and rationale

Rules for CONTEXT.md:
- Write in **English**
- Use Markdown tables for structured data (CONFIG values, functions, colors)
- Include actual values from source code, not placeholders
- Document every public function and class field
- Keep the existing format — match the style of the current CONTEXT.md
- If a new file exists that is not in the current CONTEXT.md, add a section for it
- If a file was removed, remove its section

### Step 4: Update CONTROLS.md (Romanian)

Regenerate `CONTROLS.md` to accurately reflect the current input system. Follow this structure exactly:

1. **Title** — "Ghid de Control — FTC DECODE Match Simulator"
2. **Controlere acceptate** — supported gamepads list
3. **Moduri de deplasare** — drive mode table (Field vs Robot)
4. **Control cu tastatura** — keyboard controls for P1 (and P2 if applicable)
5. **Control cu gamepad** — gamepad controls for P1
6. **Gameplay — Cum se joaca** — gameplay guide: objective, preparation, collection, launching, ramp, gate, parking, endgame, pause/reset, match end screen, options screen
7. **Sistemul de punctaj** — scoring table
8. **Moduri de joc** — Solo, 1v1 descriptions

Rules for CONTROLS.md:
- Write in **Romanian** — all text, headings, table content
- Keep the same Markdown structure and formatting as the current file
- Document every keyboard key and gamepad button binding
- Include both P1 and P2 keyboard controls
- Include gameplay tips (deadzone info, edge detection, etc.)
- Match the existing tone (technical but accessible)
- If new controls or features were added, document them
- If controls were removed, remove those sections

### Step 5: Validate and summarize

After writing both files:

1. Read back both `CONTEXT.md` and `CONTROLS.md`
2. Compare against source code to verify accuracy
3. Print a summary of changes:
   - What sections were added/removed/updated
   - Any discrepancies found between docs and code
   - Whether both files are consistent with each other

## Important Notes

- **CONTEXT.md = English**, **CONTROLS.md = Romanian** — never swap languages
- Read source files before writing — do not rely on memory or assumptions
- Preserve the existing Markdown format and section structure
- If source code changed, update docs to match — do not carry over outdated info
- The CONTROLS.md user-facing guide should be clear enough for a non-programmer to understand
