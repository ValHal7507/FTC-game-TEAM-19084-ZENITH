---
name: deploy-ftc-game
description: Build and deploy the FTC DECODE Match Simulator. Use this skill whenever the user says "deploy the code", "deploy", "make the game", "build the game", "build the exe", "update", "release", "build and deploy", "ship it", "push update", "create exe", "make exe", or any similar phrase indicating they want to build, compile, or deploy the game. This skill handles the full pipeline: PyInstaller build, exe replacement, cleanup, and documentation sync.
---

# Deploy FTC DECODE Match Simulator

Automates the full deployment pipeline for the FTC DECODE game.

## Workflow

Execute these steps in order. Stop and report if any step fails.

### Step 1: Build and deploy the executable

Run the build script from the workspace root (`FTC-game-TEAM-19084-ZENITH/`):

```powershell
powershell -ExecutionPolicy Bypass -File ".opencode\deploy-ftc-game\scripts\build.ps1"
```

This script handles:
- Running PyInstaller with the `.spec` file
- Copying the exe to `EXECUTABLE/FTC_DECODE_Simulator.exe`
- Cleaning up `build/` and `dist/` folders

If the script reports an error, stop and report it.

### Step 2: Update CONTEXT.md

Read `CONTEXT.md` and compare it against the current source code. Check:

- All file paths in the project structure section still exist
- CONFIG dict values match `config.py`
- All functions listed in each module actually exist in the source
- Any new functions, classes, or features added since last update are documented
- Threading architecture matches actual implementation
- Game flow steps are accurate

If anything is outdated or missing, update CONTEXT.md to match the current codebase. Be precise — every listed function, CONFIG key, and color constant must correspond to actual code.

### Step 3: Update CONTROLS.md

Read `CONTROLS.md` and compare it against `input_handler.py` and `game_state.py`. Check:

- All keyboard shortcuts match the actual key bindings
- All gamepad buttons match the actual gamepad handling
- Drive mode descriptions are accurate
- Gameplay instructions match current game logic
- Scoring rules match the actual point values in `game_logic.py`

If anything is outdated, update CONTROLS.md to match.

### Step 4: Final verification

After updating both docs, re-read them and verify:

1. Every CONFIG key mentioned in CONTEXT.md exists in `config.py`
2. Every function documented in CONTEXT.md exists in its module
3. Every control in CONTROLS.md matches `input_handler.py`
4. No stale references to removed or renamed features

Report what was built, what was updated, and any notable changes.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/build.ps1` | Build exe, deploy to EXECUTABLE/, clean up artifacts |
| `scripts/cleanup.ps1` | Remove build/ and dist/ folders only |

## Key Paths

| Item | Path |
|---|---|
| PyInstaller spec | `FTC game/FTC_DECODE_Simulator.spec` |
| Source entry point | `FTC game/main.py` |
| Built exe (output) | `dist/FTC_DECODE_Simulator.exe` |
| Deployed exe | `EXECUTABLE/FTC_DECODE_Simulator.exe` |
| Context doc | `FTC game/CONTEXT.md` |
| Controls doc | `FTC game/CONTROLS.md` |

All paths are relative to the workspace root (`FTC-game-TEAM-19084-ZENITH/`).
