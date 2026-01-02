# Scratchpad Quick Start

## For Users

### Initial Setup
1. Copy this entire `generic/` folder to `.claude/scratchpad/` in your project root
2. Add the scratchpad instructions from README.md to your project's `CLAUDE.md` file
3. Fill in `context.md` with your project's basic information
4. Let Claude manage the other files automatically

### What Each File Does

- **context.md** - Project overview and conventions (you fill this in once)
- **TODO.md** - Current tasks (Claude updates after each task)
- **research-notes.md** - Research findings (Claude appends discoveries)
- **decisions.md** - Architecture decisions (Claude logs important choices)
- **blockers.md** - Current blockers (Claude tracks obstacles)
- **findings.md** - Notable discoveries (Claude captures insights)
- **patterns.md** - Codebase patterns (Claude documents patterns found)
- **session-notes.md** - Session summaries (Claude logs what happened)

### Best Practices
- Check `TODO.md` to see current progress
- Review `decisions.md` to understand why choices were made
- Read `patterns.md` to learn codebase conventions
- Use `session-notes.md` to catch up after time away

---

## For Claude

### On First Interaction with New Project
1. Read `context.md` to understand project basics
2. Check if `patterns.md` exists and read it
3. Review `TODO.md` for current state
4. Read latest entry in `session-notes.md` for recent context

### During Work
- **After each task:** Rewrite `TODO.md` to reflect current state
- **When discovering something:** Append to `research-notes.md`
- **When making architectural choice:** Log in `decisions.md`
- **When blocked:** Add to `blockers.md`, remove when resolved
- **When finding important pattern:** Document in `patterns.md`
- **Notable discoveries:** Add to `findings.md`

### At End of Session
- Update `session-notes.md` with session summary
- Clean up completed items from `TODO.md`
- Clear resolved blockers from `blockers.md`

### Token Management Rules
- Keep each file under 500 tokens
- Offload large outputs to files, keep only references in chat
- Archive old entries when files grow too large
- Rewrite rather than append when approaching limit
- Keep only decision-critical info in chat context

### File Size Guidelines
- `TODO.md`: ~300 tokens (rewrite frequently)
- `research-notes.md`: ~500 tokens (archive monthly)
- `decisions.md`: ~500 tokens (archive quarterly)
- `blockers.md`: ~200 tokens (keep only active)
- `findings.md`: ~400 tokens (archive when full)
- `context.md`: ~400 tokens (stable, rarely changes)
- `patterns.md`: ~500 tokens (grows slowly)
- `session-notes.md`: ~600 tokens (keep last 3 sessions)

## Example Workflow

### User asks: "Add user authentication"

1. **Check context:** Read `context.md` for project stack
2. **Check patterns:** Read `patterns.md` for auth patterns
3. **Update TODO:** Add auth tasks to `TODO.md`
4. **Research:** If needed, append findings to `research-notes.md`
5. **Decide approach:** Log decision in `decisions.md`
6. **Track blockers:** If stuck, add to `blockers.md`
7. **Document pattern:** Add auth pattern to `patterns.md`
8. **Complete task:** Update `TODO.md`, add to `session-notes.md`

## Tips

### For Users
- Don't edit the scratchpad files manually - let Claude manage them
- Do fill in `context.md` with your project specifics
- Do review the files to understand what Claude is thinking
- Don't commit these files (they're in .gitignore)

### For Claude
- Prioritize keeping files small and current over completeness
- Remove stale information aggressively
- Use file references instead of copying large code blocks
- When in doubt, offload to a file rather than keeping in chat
