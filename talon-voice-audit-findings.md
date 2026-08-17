# Talon Voice Skill Audit Findings

Generated 2026-08-15 for a follow-up agent to apply.

## Scope and validation

Audited every file under `/home/pi/.pi/agent/skills/talon-voice/`:

- `SKILL.md`
- `evals/evals.json`
- `references/debugging-and-operations.md`
- `references/python-framework.md`
- `references/source-index.md`
- `references/talon-files.md`
- `references/voice-coding.md`

Seven Luna agents audited one file each. Sources checked included the official Talon 0.4 documentation, current Talon Community `main` via GitHub, the Community Wiki, and the Agent Skills specification/evaluation guide.

Automated checks passed:

- `evals/evals.json` is valid JSON.
- All Python fenced snippets parse with `ast.parse`.
- All relative references exist.
- Markdown code fences are balanced.
- No hard 404s were found among the cited URLs.

A live Talon reload/parser test was not possible because Talon and its runtime stubs are not installed in this VM. The skill directory is mounted read-only, so this audit did not modify it.

## Required corrections

### `references/voice-coding.md`

1. Replace the language-mode command examples:

   ```text
   force <user.language_mode>
   clear language modes
   help context <name>
   ```

   with current Community syntax:

   ```text
   force {user.language_mode}
   clear language mode
   help context {user.help_contexts}
   ```

   Current Community defines `^force {user.language_mode}$` and `^clear language mode$`. The Wiki currently documents the plural form, so mention that commands are version-dependent and the installed fileset is authoritative.

2. Replace the operator guidance:

   ```text
   Use `op <...>` for language-specific operators and `is <...>` for comparison operators
   ```

   with concrete list-based grammar, for example:

   ```talon
   op {user.code_operators_math}
   is {user.code_operators_math_comparison}
   (bit | bitwise) {user.code_operators_bitwise}
   ```

   Tell readers to use `help operators` for the active version.

3. Name the filename action explicitly: Community requires the app-specific `win.filename` action, normally implemented in `@ctx.action_class("win")`.

4. Change “`snip {user.snippet}` selects a snippet” to “inserts a named snippet.”

5. Change “A snippet name may accept a substitution mapping” to “`user.insert_snippet_by_name` accepts an optional substitution mapping.”

6. In the settings example, replace undeclared `app: my_editor` with `app: vscode` (Community’s registered matcher), or explicitly label it as a placeholder that must be registered/replaced.

7. Change “Community command server extension” to “VS Code `command-server` extension.”

8. Make language architecture conditional: languages need a `.talon` file; add a `.py` file when language-specific actions, captures, lists, or settings are required. `lang/tags/*.py` declares shared contracts, but a language only implements/activates the contracts it uses (some have defaults).

### `references/talon-files.md`

1. Fix the context example’s undeclared matcher:

   ```talon
   app.name: My Editor
   ```

   Add a comment to replace `My Editor` with the observed application name, or show a corresponding `mod.apps.my_editor` declaration.

2. Replace “the body starts immediately and is always active” with:

   > The body starts immediately and has no app/OS/etc. requirements; unless a mode is specified, it is normally active only in command mode.

3. Correct the context matcher table:

   ```text
   app.exe       executable basename, e.g. firefox or firefox.exe
   app.exe_path  full executable path, e.g. /usr/lib/firefox/firefox
   ```

4. Mark the `insert default [<user.word>]` example as schematic and state that `user.word` must be declared in the loaded fileset.

5. Replace “declared and active in the same context” with:

   > Ensure the list/capture is declared somewhere in the loaded fileset and that an applicable list mapping or capture implementation is active.

6. Clarify that `repeat(n)` repeats the immediately preceding action line; it is not a general loop/block construct.

7. Add a short tags/settings example, noting that custom names must first be declared in Python:

   ```talon
   tag(): user.feature

   settings():
       user.some_setting = 1
   ```

8. Soften phrase-override wording. Do not claim that whitespace/punctuation are independently guaranteed identity rules; say to compare the effective upstream grammar, including grouping, optionals, captures, anchors, and other matching details.

### `references/python-framework.md`

1. The context override for `transform` currently has no module declaration. Add a default action to the first `Actions` class:

   ```python
   def transform(value: str) -> str:
       """Transform a value."""
       return value
   ```

2. Make the app matcher explicit in the example, for example near `mod = Module()`:

   ```python
   mod.apps.my_editor = "app.name: My Editor"
   ```

   State that the value must be replaced with the observed app name, or use a concrete matcher.

3. Make the `A Context can also provide` list example standalone by including:

   ```python
   from talon import Context, Module

   mod = Module()
   mod.list("project", desc="Project names")
   mod.apps.my_editor = "app.name: My Editor"
   ctx = Context()
   ```

4. Replace “The official stable surface includes” with “The official 0.4.0 documentation exposes these top-level API names; verify `registry`, `scope`, and `storage` against the installed build before relying on them.”

5. Clarify virtual environments:

   > A normal host/editor virtualenv does not change Talon’s embedded Python environment. Use Talon Home’s `.venv`/`pip` mechanism only when a runtime package is genuinely required and the user accepts that setup.

### `SKILL.md`

1. Fix the Windows path spelling to `%APPDATA%\Talon` rather than the visibly doubled `%APPDATA%\\Talon`.

2. In the design workflow, distinguish app matchers:

   - `app.exe` is an executable basename.
   - `app.exe_path` is a full executable path.

3. Limit the `user.` namespace advice to custom actions, captures, lists, tags, modes, and settings. `mod.apps` names are not `user.*` names.

4. Qualify the REPL helpers as build-dependent conveniences:

   > In the installed Talon REPL, use the available `sim`, `mimic`, `actions.list/find`, and `events.tail` helpers; if a helper is unavailable, use that build’s documented equivalent and the log.

5. Replace the gotcha “Without a header, the body is always active” with:

   > Without a header or dash, the body has no app/OS/etc. requirements; unless a mode is specified, it is normally active only in command mode.

6. Replace the phrase-override gotcha with a warning against near-duplicate rules and unstable precedence. Recommend comparing the effective upstream grammar and prefer an action override, new phrase, or isolated vendoring.

7. Correct the threading guidance. `cron` does not make blocking work asynchronous:

   > Use lifecycle callbacks only for short setup and `cron` only for short periodic callbacks. Put blocking polling/I/O in a thread/process or use a non-blocking design, and marshal results back safely.

8. In the minimal context example, replace undeclared `app: my_editor` with `app.name: My Editor` and label it as an observed-value placeholder.

### `references/debugging-and-operations.md`

1. Replace the visible Windows paths with single separators:

   ```text
   %APPDATA%\Talon
   %APPDATA%\Talon\user
   ```

2. Change the opening “canonical sources” wording to “primary Community references,” and remind readers that they are version-sensitive.

3. Change the process check to account for Linux tray limitations:

   > Confirm Talon is running using the process, log, or menu icon when available. On Linux, a missing tray icon may only mean AppIndicator/KStatusNotifierItem support is absent.

4. Qualify `wake up`/`go to sleep` as Community, non-Dragon checks. Dragon and other filesets may use different controls/phrases.

5. Qualify the engine statement as Talon 0.4-era/current Community guidance: W2L Conformer/Conformer D is the normal command-and-dictation engine; Webspeech/Vosk are beta dictation engines and cannot stand alone for commands. Tell users to verify the Speech Recognition menu for their build.

6. Qualify `help active`, `help context`, and `help search` as Community commands. For other filesets, use that fileset’s documentation or the REPL.

7. Say “use the Debug Window if available; otherwise use `ui.apps()` or the REPL.”

8. Start event tracing before execution:

   ```python
   events.tail()
   mimic("a harmless phrase")
   ```

   Explain that `mimic` tests grammar matching/action execution, not microphone or ASR recognition.

9. Describe `~/.talon/bin/repl` as a REPL client that requires a running Talon instance. Prefer deterministic examples such as:

   ```bash
   echo 'actions.speech.enable()' | ~/.talon/bin/repl
   ```

   rather than an unexplained stateful toggle.

10. For intermittent input, explain that `speech.timeout` primarily affects utterance segmentation at pauses. Mention enabling Speech Recognition → Save Recordings before diagnosing recordings.

11. Replace “Wayland support is limited/not supported” with “Talon does not support Wayland; select an X11 session.”

### `references/source-index.md`

1. Describe `https://talonvoice.com/docs/` as historical Talon 0.4.0 documentation and add the changelog link:

   `https://talonvoice.com/dl/latest/changelog.html`

2. Replace the unverifiable review-process paragraph with a dated, reproducible note, for example:

   > On 2026-08-15, `https://talon.wiki/sitemap.xml` listed 53 URLs. Treat this as a navigation snapshot, not a guarantee that every page remains current.

3. Link the Wiki repository when discussing repository Markdown:

   `https://github.com/TalonCommunity/Wiki`

4. Describe `/explorer` and `/search` as dynamic navigation/search utilities, not authoritative static technical sources.

5. When practical, record dates or commits for mutable Wiki/Community sources; continue directing users to the installed Talon build, fileset, log, and stubs as the final authority.

### `evals/evals.json`

The file is valid JSON and the `assertions` field is correct according to the Agent Skills evaluation guide. Do not rename it to `expectations`.

Recommended improvements:

1. Change string IDs to integers (`1` through `5`) for broader runner compatibility.
2. Strengthen `new-command` assertions to require the actual `key(ctrl-shift-p)` (or a confirmed platform equivalent), a concrete observed app/title matcher, placement outside `community`, and reload/log plus `sim`/`mimic` instructions.
3. Strengthen `action-and-capture` assertions to require a `user.<capture>` rule, a `user.<action>(direction)` call, and genuinely distinct north/south/east/west behavior.
4. For `phrase-override`, require inspection of the exact current Community rule and preservation of the Community checkout. Note that `touch` may directly call several actions, so an action override is only applicable if the behavior is delegated through an overrideable action.
5. For `nothing-happens`, require process, microphone, speech engine, fileset/reload log, context, and awake/mode checks. Require conditional REPL instructions and prohibit claiming live results without a running Talon instance.
6. For `voice-coding`, require language registration in `core/modes/code_languages.py`, activation of only supported tag contracts, exact current force/clear-language commands, extension/file-name detection testing, and `.py` only when Python declarations are needed.

## Final status

The skill is substantially sound, but it should not be considered fully audited-clean until the definite grammar/API/documentation errors above are corrected. Another agent can apply this file’s changes to the read-write source copy of the skill.
