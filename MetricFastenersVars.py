# MetricFastenersVars.py
# Fusion 360 script — inserts metric fastener user parameters from a CSV file.
# The CSV must live in the same folder as this script.
#
# Supported sizes are auto-detected from the CSV (e.g. M3, M4, M5, M6, M8, M10).
# A dialog lets you pick which sizes to insert; existing parameters are skipped.

import adsk.core
import adsk.fusion
import os
import csv
import re
import traceback

# ---------------------------------------------------------------------------
# Module-level state (scripts are single-file; globals keep handlers alive)
# ---------------------------------------------------------------------------
_app: adsk.core.Application = None
_ui: adsk.core.UserInterface = None
_handlers = []           # Keep event handlers from being garbage-collected
_params_by_size = {}     # { 'm3': [{name, unit, expression}, ...], ... }
_sizes = []              # Ordered list of size keys: ['m3', 'm4', ...]

CSV_FILENAME = 'MetricFasteners.csv'
CMD_ID       = 'WS_MetricFastenersInsert'


# ---------------------------------------------------------------------------
# Helper — load and group CSV rows by size prefix (m3, m4, …)
# ---------------------------------------------------------------------------
def _load_csv(csv_path: str) -> tuple[dict, list]:
    params_by_size = {}
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['Name'].strip()
            match = re.match(r'^(m\d+)', name, re.IGNORECASE)
            if not match:
                continue
            size_key = match.group(1).lower()  # 'm3', 'm4', …
            params_by_size.setdefault(size_key, []).append({
                'name':       name,
                'unit':       row['Unit'].strip(),
                'expression': row['Expression'].strip(),
            })

    # Sort sizes numerically (m3 < m4 < m8 < m10, not lexicographic)
    sizes = sorted(params_by_size.keys(), key=lambda s: int(s[1:]))
    return params_by_size, sizes


# ---------------------------------------------------------------------------
# Event handler — build the command dialog
# ---------------------------------------------------------------------------
class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        try:
            cmd    = args.command
            inputs = cmd.commandInputs

            # "Select All" toggle at the top
            inputs.addBoolValueInput('selectAll', 'Select All Sizes', True, '', True)

            # One checkbox per size group
            for size in _sizes:
                label = size.upper()  # M3, M4, …
                inputs.addBoolValueInput(f'size_{size}', label, True, '', True)

            # Wire up remaining handlers
            on_execute = CommandExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)

            on_changed = InputChangedHandler()
            cmd.inputChanged.add(on_changed)
            _handlers.append(on_changed)

            on_destroy = CommandDestroyHandler()
            cmd.destroy.add(on_destroy)
            _handlers.append(on_destroy)

        except Exception:
            _ui.messageBox(f'Error building dialog:\n{traceback.format_exc()}')


# ---------------------------------------------------------------------------
# Event handler — "Select All" drives individual checkboxes
# ---------------------------------------------------------------------------
class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args: adsk.core.InputChangedEventArgs):
        try:
            changed = args.input
            inputs  = args.inputs

            if changed.id == 'selectAll':
                new_val = adsk.core.BoolValueCommandInput.cast(changed).value
                for size in _sizes:
                    cb = adsk.core.BoolValueCommandInput.cast(
                        inputs.itemById(f'size_{size}')
                    )
                    if cb:
                        cb.value = new_val

        except Exception:
            _ui.messageBox(f'Error in input changed:\n{traceback.format_exc()}')


# ---------------------------------------------------------------------------
# Event handler — create the parameters when OK is clicked
# ---------------------------------------------------------------------------
class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            inputs = args.command.commandInputs
            design = adsk.fusion.Design.cast(_app.activeProduct)
            user_params = design.userParameters

            # Collect checked sizes
            selected_sizes = [
                size for size in _sizes
                if adsk.core.BoolValueCommandInput.cast(
                    inputs.itemById(f'size_{size}')
                ).value
            ]

            if not selected_sizes:
                _ui.messageBox('No sizes selected — nothing was created.')
                return

            created = []
            skipped = []
            errors  = []

            for size in selected_sizes:
                for param in _params_by_size[size]:
                    name = param['name']
                    unit = param['unit']
                    expr = param['expression']

                    # Skip if the parameter already exists
                    if user_params.itemByName(name):
                        skipped.append(name)
                        continue

                    try:
                        val_input = adsk.core.ValueInput.createByString(expr)
                        user_params.add(name, val_input, unit, 'Metric Fasteners')
                        created.append(name)
                    except Exception as e:
                        errors.append(f'  {name}: {e}')

            # ── Summary ────────────────────────────────────────────────────
            size_labels = ', '.join(s.upper() for s in selected_sizes)
            lines = [
                f'Sizes selected : {size_labels}',
                f'Created        : {len(created)}',
                f'Skipped (exist): {len(skipped)}',
            ]
            if errors:
                lines.append(f'Errors         : {len(errors)}')
                lines.extend(errors)
            else:
                lines.append('\nAll parameters created successfully.')

            _ui.messageBox('\n'.join(lines), 'Metric Fasteners — Done')

        except Exception:
            _ui.messageBox(f'Error creating parameters:\n{traceback.format_exc()}')


# ---------------------------------------------------------------------------
# Event handler — terminate the script when the dialog closes
# ---------------------------------------------------------------------------
class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def notify(self, args: adsk.core.CommandEventArgs):
        adsk.terminate()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def run(context):
    global _app, _ui, _params_by_size, _sizes, _handlers
    _handlers = []

    _app = adsk.core.Application.get()
    _ui  = _app.userInterface

    try:
        # Must have an active Fusion design
        design = adsk.fusion.Design.cast(_app.activeProduct)
        if not design:
            _ui.messageBox(
                'No active Fusion 360 design found.\n'
                'Open or create a design before running this script.'
            )
            return

        # Locate CSV next to this script
        script_dir = os.path.dirname(os.path.realpath(__file__))
        csv_path   = os.path.join(script_dir, CSV_FILENAME)

        if not os.path.exists(csv_path):
            _ui.messageBox(
                f'CSV file not found:\n{csv_path}\n\n'
                f'Make sure "{CSV_FILENAME}" is in the same folder as this script.'
            )
            return

        # Parse CSV
        _params_by_size, _sizes = _load_csv(csv_path)

        if not _sizes:
            _ui.messageBox(f'No valid parameter rows found in {CSV_FILENAME}.')
            return

        # Clean up any leftover command definition from a previous run
        existing = _ui.commandDefinitions.itemById(CMD_ID)
        if existing:
            existing.deleteMe()

        # Create command and show dialog
        cmd_def = _ui.commandDefinitions.addButtonDefinition(
            CMD_ID,
            'Insert Metric Fastener Parameters',
            f'Creates Fusion 360 user parameters from {CSV_FILENAME}',
        )

        on_created = CommandCreatedHandler()
        cmd_def.commandCreated.add(on_created)
        _handlers.append(on_created)

        cmd_def.execute()

        # Keep the script alive until the dialog is dismissed
        adsk.autoTerminate(False)

    except Exception:
        if _ui:
            _ui.messageBox(f'Unexpected error:\n{traceback.format_exc()}')
