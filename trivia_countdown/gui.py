"""Tkinter desktop interface for Trivia Countdown."""

from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
from queue import Empty, Queue
import shlex
import sys
from threading import Thread
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from PIL import Image, ImageTk

from .app import (
    ProgressEvent,
    RenderOptions,
    RenderRequest,
    default_output_path,
    load_questions,
    prepare_render,
    run_render,
)
from .lib.cancellation import CancellationToken, RenderCancelled
from .lib.models import TriviaQuestion
from .lib.overlays import render_question_image
from .lib.progress import format_duration
from .lib.video import extract_video_still, get_video_dimensions, get_video_duration, require_executable
from .resources import is_frozen, resource_path


def quote_cli_argument(value: str) -> str:
    if sys.platform == "win32":
        return "'" + value.replace("'", "''") + "'"
    return shlex.quote(value)


class QuestionTable(ttk.Frame):
    """Scrollable question grid with an individually highlighted correct answer."""

    headings = ("#", "Question", "Answer 1", "Answer 2", "Answer 3", "Answer 4", "Correct")
    widths = (5, 40, 22, 22, 22, 22, 9)

    def __init__(self, parent: tk.Misc, on_select: Callable[[int], None]) -> None:
        super().__init__(parent)
        self._on_select = on_select
        self._selected_index: Optional[int] = None
        self._row_widgets: list[list[tk.Label]] = []
        self._row_colors: list[list[tuple[str, str]]] = []
        self._canvas = tk.Canvas(self, highlightthickness=0)
        vertical_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        horizontal_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)
        self._content = tk.Frame(self._canvas)
        self._window = self._canvas.create_window((0, 0), window=self._content, anchor="nw")
        self._content.bind("<Configure>", self._update_scroll_region)
        self._canvas.bind("<Configure>", self._resize_content)
        self._canvas.bind("<Enter>", self._enable_mousewheel)
        self._canvas.bind("<Leave>", self._disable_mousewheel)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def _update_scroll_region(self, _event: tk.Event) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _resize_content(self, event: tk.Event) -> None:
        self._canvas.itemconfigure(self._window, width=max(event.width, self._content.winfo_reqwidth()))

    def _enable_mousewheel(self, _event: tk.Event) -> None:
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _disable_mousewheel(self, _event: tk.Event) -> None:
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event: tk.Event) -> str:
        if getattr(event, "num", None) == 4:
            direction = -1
        elif getattr(event, "num", None) == 5:
            direction = 1
        else:
            direction = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(direction, "units")
        return "break"

    def set_questions(self, questions: list[TriviaQuestion]) -> None:
        for child in self._content.winfo_children():
            child.destroy()
        self._row_widgets = []
        self._row_colors = []
        for column, (heading, width) in enumerate(zip(self.headings, self.widths)):
            label = tk.Label(
                self._content,
                text=heading,
                anchor="w",
                font=("TkDefaultFont", 11, "bold"),
                background="#0b2252",
                foreground="#ffffff",
                padx=6,
                pady=5,
                width=width,
            )
            label.grid(row=0, column=column, sticky="nsew", padx=1, pady=1)
        for row, question in enumerate(questions, start=1):
            values = (str(row), question.question, *question.answers, str(question.correct_answer))
            row_widgets: list[tk.Label] = []
            row_colors: list[tuple[str, str]] = []
            for column, (value, width) in enumerate(zip(values, self.widths)):
                is_correct = 2 <= column <= 5 and column - 1 == question.correct_answer
                background = "#ffe024" if is_correct else "#ffffff"
                foreground = "#181818" if is_correct else "#101820"
                label = tk.Label(
                    self._content,
                    text=value,
                    anchor="w",
                    justify="left",
                    wraplength=width * 7,
                    background=background,
                    foreground=foreground,
                    padx=6,
                    pady=5,
                    width=width,
                    cursor="hand2",
                )
                label.grid(row=row, column=column, sticky="nsew", padx=1, pady=1)
                label.bind("<Button-1>", lambda _event, index=row - 1: self.select(index))
                row_widgets.append(label)
                row_colors.append((background, foreground))
            self._row_widgets.append(row_widgets)
            self._row_colors.append(row_colors)
        self._selected_index = None

    def select(self, index: int) -> None:
        for row_widgets, row_colors in zip(self._row_widgets, self._row_colors):
            for label, (background, foreground) in zip(row_widgets, row_colors):
                label.configure(background=background, foreground=foreground, highlightthickness=0)
        for label in self._row_widgets[index]:
            label.configure(background="#d9f2df", foreground="#123b23", highlightthickness=0)
        self._selected_index = index
        self._on_select(index)


class TriviaCountdownApp(ttk.Frame):
    """The main window and worker-thread coordinator."""

    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root, padding=12)
        self.root = root
        self.root.title("Trivia Countdown")
        self.root.geometry("1440x810")
        self.root.minsize(1152, 648)
        with Image.open(resource_path("assets", "app_icon.png")) as icon:
            self._app_icon = ImageTk.PhotoImage(icon)
        self.root.iconphoto(True, self._app_icon)
        self.pack(fill="both", expand=True)
        self._events: Queue[tuple[str, object]] = Queue()
        self._preview_generation = 0
        self._preview_photo: Optional[ImageTk.PhotoImage] = None
        self._preview_image: Optional[Image.Image] = None
        self._questions: list[TriviaQuestion] = []
        self._selected_question = 0
        self._output_is_automatic = True
        self._render_token: Optional[CancellationToken] = None
        self._phase_started: dict[str, float] = {}

        self.video_path = tk.StringVar()
        self.trivia_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.reveal_answer = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Choose a source video and trivia CSV to begin.")
        self.preview_text = tk.StringVar(value="Preview appears after both inputs are selected.")
        self.question_status = tk.StringVar(value="Select a row to update the preview.")
        self.include_default_parameters = tk.BooleanVar(value=True)
        self.cli_status = tk.StringVar(value="")
        self.overlay_progress_text = tk.StringVar(value="0%")
        self.video_progress_text = tk.StringVar(value="0%")
        self.overlay_progress_value = tk.DoubleVar(value=0.0)
        self.video_progress_value = tk.DoubleVar(value=0.0)

        self._build_variables()
        self._build_interface()
        self.output_path.trace_add("write", self._output_changed)
        self.video_path.trace_add("write", self._video_changed)
        self.trivia_path.trace_add("write", self._refresh_cli_command)
        self.root.after(100, self._poll_events)

    def _build_variables(self) -> None:
        defaults = RenderOptions()
        self.randomize = tk.BooleanVar(value=defaults.randomize)
        self.keep_overlays = tk.BooleanVar(value=False)
        self.seed = tk.StringVar(value="")
        self.overlay_directory = tk.StringVar(value="")
        self.option_values = {
            "question_duration": tk.StringVar(value=str(defaults.question_duration)),
            "answer_duration": tk.StringVar(value=str(defaults.answer_duration)),
            "answer_flash_duration": tk.StringVar(value=str(defaults.answer_flash_duration)),
            "answer_flash_interval": tk.StringVar(value=str(defaults.answer_flash_interval)),
            "start_delay": tk.StringVar(value=str(defaults.start_delay)),
            "end_early": tk.StringVar(value=str(defaults.end_early)),
            "fade_in_time": tk.StringVar(value=str(defaults.fade_in_time)),
            "fade_out_time": tk.StringVar(value=str(defaults.fade_out_time)),
            "mid_question_fade": tk.StringVar(value=str(defaults.mid_question_fade)),
        }

    def _build_interface(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self.main_tab = ttk.Frame(self.notebook, padding=12)
        self.advanced_tab = ttk.Frame(self.notebook, padding=12)
        self.questions_tab = ttk.Frame(self.notebook, padding=12)
        self.cli_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.main_tab, text="Main")
        self.notebook.add(self.advanced_tab, text="Advanced")
        self.notebook.add(self.questions_tab, text="Questions")
        if not is_frozen():
            self.notebook.add(self.cli_tab, text="CLI")
        self.notebook.bind("<<NotebookTabChanged>>", self._tab_changed)
        self._build_main_tab()
        self._build_advanced_tab()
        self._build_questions_tab()
        self._build_cli_tab()

    def _build_main_tab(self) -> None:
        self.main_tab.columnconfigure(1, weight=1)
        self.main_tab.rowconfigure(0, weight=1)
        controls = ttk.LabelFrame(self.main_tab, text="Video and Output", padding=12)
        controls.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        preview = ttk.LabelFrame(self.main_tab, text="Question Preview", padding=8)
        preview.grid(row=0, column=1, sticky="nsew")
        preview.columnconfigure(0, weight=1)
        preview.rowconfigure(0, weight=1)
        preview.bind("<Configure>", self._resize_preview)

        self._path_row(controls, 0, "Source video", self.video_path, self._choose_video, "Video...")
        self._path_row(controls, 2, "Trivia CSV", self.trivia_path, self._choose_trivia, "Trivia...")
        self._path_row(controls, 4, "Output MP4", self.output_path, self._choose_output, "Output...")
        self.create_button = ttk.Button(controls, text="Create Video", command=self._begin_render)
        self.create_button.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self.cancel_button = ttk.Button(controls, text="Cancel Render", command=self._cancel_render, state="disabled")
        self.cancel_button.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Label(controls, textvariable=self.status_text, wraplength=290, justify="left").grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=(12, 0)
        )

        self.preview_label = ttk.Label(preview, anchor="center", justify="center")
        self.preview_label.grid(row=0, column=0, sticky="nsew")
        self.reveal_preview_check = ttk.Checkbutton(
            preview,
            text="Show answer reveal in preview",
            variable=self.reveal_answer,
            command=self._start_preview,
        )
        self.reveal_preview_check.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.reveal_preview_check.grid_remove()
        ttk.Label(preview, textvariable=self.preview_text, anchor="center").grid(row=2, column=0, sticky="ew", pady=(4, 0))

        progress = ttk.LabelFrame(self.main_tab, text="Render Progress", padding=10)
        progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        progress.columnconfigure(1, weight=1)
        ttk.Label(progress, text="Generating overlays", width=22).grid(row=0, column=0, sticky="w")
        ttk.Progressbar(progress, maximum=100, variable=self.overlay_progress_value).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        ttk.Label(progress, textvariable=self.overlay_progress_text, width=27).grid(row=0, column=2, sticky="e")
        ttk.Label(progress, text="Composing video", width=22).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Progressbar(progress, maximum=100, variable=self.video_progress_value).grid(
            row=1, column=1, sticky="ew", padx=8, pady=(6, 0)
        )
        ttk.Label(progress, textvariable=self.video_progress_text, width=27).grid(
            row=1, column=2, sticky="e", pady=(6, 0)
        )

    def _path_row(
        self,
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        variable: tk.StringVar,
        command: Callable[[], None],
        button: str,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=variable, width=38).grid(row=row + 1, column=0, sticky="ew", pady=(2, 7))
        ttk.Button(parent, text=button, command=command).grid(row=row + 1, column=1, sticky="e", padx=(6, 0), pady=(2, 7))

    def _build_advanced_tab(self) -> None:
        self.advanced_tab.columnconfigure(0, weight=1)
        self.advanced_tab.columnconfigure(1, weight=1)
        question_order = ttk.LabelFrame(self.advanced_tab, text="Question Order", padding=10)
        question_order.grid(row=0, column=0, sticky="new", padx=(0, 8), pady=(0, 8))
        ttk.Checkbutton(
            question_order,
            text="Randomize question order",
            variable=self.randomize,
            command=self._questions_changed,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(question_order, text="Random seed (optional)").grid(row=1, column=0, sticky="w")
        seed_entry = ttk.Entry(question_order, textvariable=self.seed, width=18)
        seed_entry.grid(row=1, column=1, sticky="w", pady=4)
        seed_entry.bind("<FocusOut>", lambda _event: self._questions_changed())

        overlay_output = ttk.LabelFrame(self.advanced_tab, text="Overlay Output", padding=10)
        overlay_output.grid(row=1, column=0, sticky="new", padx=(0, 8))
        ttk.Checkbutton(
            overlay_output,
            text="Keep generated overlay PNGs",
            variable=self.keep_overlays,
            command=self._update_overlay_directory_state,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(overlay_output, text="PNG directory (optional)").grid(row=1, column=0, sticky="w")
        self.overlay_directory_entry = ttk.Entry(overlay_output, textvariable=self.overlay_directory, width=18)
        self.overlay_directory_entry.grid(row=1, column=1, sticky="w", padx=(8, 6))
        self.overlay_directory_button = ttk.Button(overlay_output, text="Browse...", command=self._choose_overlay_directory)
        self.overlay_directory_button.grid(row=1, column=2, sticky="w")
        self._update_overlay_directory_state()

        timing = ttk.LabelFrame(self.advanced_tab, text="Timing", padding=10)
        timing.grid(row=0, column=1, sticky="new", pady=(0, 8))
        timing_fields = (
            ("question_duration", "Question duration (seconds)"),
            ("answer_duration", "Answer highlight duration (seconds)"),
            ("start_delay", "Start delay (seconds)"),
            ("end_early", "End early (seconds)"),
        )
        for row, (name, label) in enumerate(timing_fields):
            self._option_row(timing, row, name, label)

        effects = ttk.LabelFrame(self.advanced_tab, text="Reveal and Transition Effects", padding=10)
        effects.grid(row=1, column=1, sticky="new")
        effect_fields = (
            ("answer_flash_duration", "Answer flash duration (seconds)"),
            ("answer_flash_interval", "Answer flash interval (seconds)"),
            ("fade_in_time", "First panel fade in (seconds)"),
            ("fade_out_time", "Last panel fade out (seconds)"),
            ("mid_question_fade", "Question transition fade (seconds)"),
        )
        for row, (name, label) in enumerate(effect_fields):
            self._option_row(effects, row, name, label)
        ttk.Button(self.advanced_tab, text="Reset Defaults", command=self._reset_defaults).grid(
            row=2, column=0, sticky="w", pady=(8, 0)
        )

    def _option_row(self, parent: ttk.LabelFrame, row: int, name: str, label: str) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=self.option_values[name], width=18)
        entry.grid(row=row, column=1, sticky="w", padx=(8, 0), pady=4)
        entry.bind("<FocusOut>", lambda _event: self._options_changed())

    def _build_questions_tab(self) -> None:
        self.questions_tab.rowconfigure(1, weight=1)
        self.questions_tab.columnconfigure(0, weight=1)
        ttk.Label(
            self.questions_tab,
            text="Select a question to update the preview. The highlighted answer is the CSV's correct answer.",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.question_table = QuestionTable(self.questions_tab, self._question_selected)
        self.question_table.grid(row=1, column=0, sticky="nsew")
        ttk.Label(self.questions_tab, textvariable=self.question_status, anchor="w").grid(
            row=2, column=0, sticky="ew", pady=(8, 0)
        )

    def _build_cli_tab(self) -> None:
        self.cli_tab.rowconfigure(2, weight=1)
        self.cli_tab.columnconfigure(0, weight=1)
        ttk.Label(
            self.cli_tab,
            text="Command line equivalent of the current GUI selections:",
        ).grid(row=0, column=0, sticky="w")
        controls = ttk.Frame(self.cli_tab)
        controls.grid(row=1, column=0, sticky="ew", pady=(8, 8))
        controls.columnconfigure(0, weight=1)
        ttk.Checkbutton(
            controls,
            text="Include parameters using default values",
            variable=self.include_default_parameters,
            command=self._refresh_cli_command,
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(controls, text="📋", width=3, command=self._copy_cli_command).grid(row=0, column=1, sticky="e")
        self.cli_command_text = tk.Text(self.cli_tab, height=8, wrap="word", font=("TkFixedFont", 11))
        self.cli_command_text.grid(row=2, column=0, sticky="nsew")
        self.cli_command_text.configure(state="disabled")
        ttk.Label(self.cli_tab, textvariable=self.cli_status, anchor="w").grid(row=3, column=0, sticky="ew", pady=(8, 0))
        self._refresh_cli_command()

    def _tab_changed(self, _event: tk.Event) -> None:
        if self.notebook.select() == str(self.cli_tab):
            self._refresh_cli_command()

    def _choose_video(self) -> None:
        path = filedialog.askopenfilename(title="Choose a source video")
        if path:
            self._output_is_automatic = True
            self.video_path.set(path)
            self._start_preview()

    def _choose_trivia(self) -> None:
        path = filedialog.askopenfilename(title="Choose trivia CSV", filetypes=(("CSV files", "*.csv"), ("All files", "*")))
        if path:
            self.trivia_path.set(path)
            self._questions_changed()

    def _choose_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Choose output MP4",
            defaultextension=".mp4",
            filetypes=(("MP4 video", "*.mp4"),),
        )
        if path:
            self._output_is_automatic = False
            self.output_path.set(path)

    def _output_changed(self, *_args: object) -> None:
        expected = default_output_path(Path(self.video_path.get())) if self.video_path.get() else None
        if expected and self.output_path.get() != str(expected):
            self._output_is_automatic = False
        self._refresh_cli_command()

    def _video_changed(self, *_args: object) -> None:
        if self.video_path.get() and self._output_is_automatic:
            self.output_path.set(str(default_output_path(Path(self.video_path.get()))))
        if self.video_path.get():
            self.reveal_preview_check.grid()
        else:
            self.reveal_preview_check.grid_remove()
        self._refresh_cli_command()

    def _update_overlay_directory_state(self) -> None:
        state = "normal" if self.keep_overlays.get() else "disabled"
        self.overlay_directory_entry.configure(state=state)
        self.overlay_directory_button.configure(state=state)
        self._refresh_cli_command()

    def _choose_overlay_directory(self) -> None:
        path = filedialog.askdirectory(title="Choose overlay PNG directory")
        if path:
            self.overlay_directory.set(path)
            self.keep_overlays.set(True)
            self._update_overlay_directory_state()

    def _options_changed(self) -> None:
        self._start_preview()
        self._refresh_cli_command()

    def _refresh_cli_command(self, *_args: object) -> None:
        if not hasattr(self, "cli_command_text"):
            return
        command = self._build_cli_command()
        self.cli_command_text.configure(state="normal")
        self.cli_command_text.delete("1.0", "end")
        self.cli_command_text.insert("1.0", command)
        self.cli_command_text.configure(state="disabled")

    def _build_cli_command(self) -> str:
        video_path = self.video_path.get().strip()
        trivia_path = self.trivia_path.get().strip()
        output_path = self.output_path.get().strip()
        if not video_path or not trivia_path or not output_path:
            return "Choose a source video, trivia CSV, and output path to generate the command."
        try:
            options = self._render_options()
        except ValueError as exc:
            return f"Fix Advanced options to generate the command: {exc}"

        command = [
            "uv",
            "run",
            "python",
            "make_trivia_countdown.py",
            video_path,
            trivia_path,
            "--output",
            output_path,
        ]
        defaults = RenderOptions()
        if options.randomize:
            command.append("--random")
        if options.seed is not None:
            command.extend(("--seed", str(options.seed)))
        for option_name, attribute in (
            ("--duration", "question_duration"),
            ("--answer-duration", "answer_duration"),
            ("--answer-flash-duration", "answer_flash_duration"),
            ("--answer-flash-interval", "answer_flash_interval"),
            ("--start-delay", "start_delay"),
            ("--end-early", "end_early"),
            ("--fade-in-time", "fade_in_time"),
            ("--fade-out-time", "fade_out_time"),
            ("--mid-question-fade", "mid_question_fade"),
        ):
            value = getattr(options, attribute)
            if self.include_default_parameters.get() or value != getattr(defaults, attribute):
                command.extend((option_name, f"{value:g}"))
        if options.overlay_dir is not None:
            command.extend(("--overlay-dir", str(options.overlay_dir)))
        return " ".join(quote_cli_argument(part) for part in command)

    def _copy_cli_command(self) -> None:
        command = self._build_cli_command()
        if command.startswith("Choose ") or command.startswith("Fix "):
            self.cli_status.set(command)
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(command)
        self.root.update()
        self.cli_status.set("Command copied to the clipboard.")

    def _default_overlay_directory(self) -> Path:
        output_text = self.output_path.get().strip()
        if output_text:
            output_file = Path(output_text)
            return output_file.with_name(f"{output_file.stem}_overlays")
        return Path("rendered_overlays")

    def _render_options(self) -> RenderOptions:
        try:
            seed_text = self.seed.get().strip()
            values = {name: float(variable.get().strip()) for name, variable in self.option_values.items()}
            overlay_directory = self.overlay_directory.get().strip()
            return RenderOptions(
                randomize=self.randomize.get(),
                seed=int(seed_text) if seed_text else None,
                overlay_dir=(
                    Path(overlay_directory) if overlay_directory else self._default_overlay_directory()
                )
                if self.keep_overlays.get()
                else None,
                **values,
            )
        except ValueError as exc:
            raise ValueError("Advanced options must contain valid numbers and an optional integer seed") from exc

    def _questions_changed(self) -> None:
        if not self.trivia_path.get():
            self._refresh_cli_command()
            return
        try:
            self._questions = load_questions(Path(self.trivia_path.get()), self._render_options())
        except (OSError, ValueError) as exc:
            self._questions = []
            self.question_table.set_questions([])
            self.status_text.set(f"Trivia CSV error: {exc}")
            self._refresh_cli_command()
            return
        self._selected_question = 0
        self.question_table.set_questions(self._questions)
        self.status_text.set(f"Loaded {len(self._questions)} trivia question(s).")
        self.question_status.set("Select a row to update the preview.")
        self._start_preview()
        self._refresh_cli_command()

    def _question_selected(self, index: int) -> None:
        self._selected_question = index
        self.question_status.set(f"Preview updated to show question {index + 1}.")
        self._start_preview()

    def _reset_defaults(self) -> None:
        defaults = RenderOptions()
        self.randomize.set(defaults.randomize)
        self.keep_overlays.set(False)
        self.seed.set("")
        self.overlay_directory.set("")
        for name, variable in self.option_values.items():
            value = getattr(defaults, name)
            variable.set("" if value is None else str(value))
        self._update_overlay_directory_state()
        self._questions_changed()

    def _start_preview(self) -> None:
        if not self.video_path.get() or not self._questions:
            return
        try:
            options = self._render_options()
        except ValueError as exc:
            self.preview_text.set(str(exc))
            return
        if self._selected_question >= len(self._questions):
            return
        selected_index = self._selected_question
        self._preview_generation += 1
        generation = self._preview_generation
        video_file = Path(self.video_path.get())
        question = self._questions[selected_index]
        reveal_answer = self.reveal_answer.get()
        self.preview_text.set("Rendering preview...")

        def build_preview() -> None:
            try:
                require_executable("ffmpeg")
                dimensions = get_video_dimensions(video_file)
                duration = get_video_duration(video_file)
                timestamp = min(
                    max(0.0, options.start_delay + selected_index * (options.question_duration + options.answer_duration)),
                    max(0.0, duration - 0.05),
                )
                frame = extract_video_still(video_file, timestamp)
                overlay = render_question_image(question, dimensions, reveal_answer=reveal_answer)
                if frame.size != overlay.size:
                    frame = frame.resize(overlay.size, Image.Resampling.LANCZOS)
                self._events.put(("preview", (generation, Image.alpha_composite(frame, overlay), timestamp)))
            except (OSError, RuntimeError, ValueError) as exc:
                self._events.put(("preview_error", (generation, str(exc))))

        Thread(target=build_preview, daemon=True).start()

    def _begin_render(self) -> None:
        try:
            options = self._render_options()
            request = RenderRequest(
                Path(self.video_path.get().strip()),
                Path(self.trivia_path.get().strip()),
                Path(self.output_path.get().strip()),
                options,
            )
            if not request.video_file.name or not request.trivia_file.name or not request.output_file.name:
                raise ValueError("Choose a source video, trivia CSV, and output path")
        except ValueError as exc:
            messagebox.showerror("Cannot create video", str(exc), parent=self.root)
            return
        if request.output_file.exists() and not messagebox.askyesno(
            "Replace existing output?",
            f"{request.output_file.name} already exists. Replace it after this render succeeds?",
            parent=self.root,
        ):
            return

        self._render_token = CancellationToken()
        self.create_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self._phase_started.clear()
        self.overlay_progress_value.set(0.0)
        self.video_progress_value.set(0.0)
        self.overlay_progress_text.set("0%")
        self.video_progress_text.set("0%")
        self.status_text.set("Validating inputs and preparing render...")

        def render() -> None:
            try:
                prepared = prepare_render(request)

                def report(event: ProgressEvent) -> None:
                    self._events.put(("progress", event))

                result = run_render(prepared, progress_callback=report, cancellation_token=self._render_token)
                self._events.put(("render_complete", (prepared, result)))
            except RenderCancelled:
                self._events.put(("render_cancelled", None))
            except (OSError, RuntimeError, ValueError) as exc:
                self._events.put(("render_error", str(exc)))

        Thread(target=render, daemon=True).start()

    def _cancel_render(self) -> None:
        if self._render_token:
            self._render_token.cancel()
            self.cancel_button.configure(state="disabled")
            self.status_text.set("Cancelling render...")

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self._events.get_nowait()
                if kind == "preview":
                    generation, image, timestamp = payload  # type: ignore[misc]
                    if generation == self._preview_generation:
                        self._show_preview(image, timestamp)
                elif kind == "preview_error":
                    generation, message = payload  # type: ignore[misc]
                    if generation == self._preview_generation:
                        self.preview_text.set(f"Preview unavailable: {message}")
                elif kind == "progress":
                    self._update_progress(payload)  # type: ignore[arg-type]
                elif kind == "render_complete":
                    prepared, result = payload  # type: ignore[misc]
                    self._finish_render(
                        f"Created {prepared.request.output_file.name} using {len(prepared.questions)} question(s). "
                        f"Render time: {result.timings.overlay_seconds + result.timings.compose_seconds:.1f}s"
                    )
                elif kind == "render_cancelled":
                    self._finish_render("Render cancelled. Existing output was left unchanged.")
                elif kind == "render_error":
                    self._finish_render(f"Render failed: {payload}")
                    messagebox.showerror("Render failed", str(payload), parent=self.root)
        except Empty:
            pass
        self.root.after(100, self._poll_events)

    def _show_preview(self, image: Image.Image, timestamp: float) -> None:
        self._preview_image = image
        self._display_preview()
        self.preview_text.set(f"Question {self._selected_question + 1} at {timestamp:.1f}s")

    def _resize_preview(self, _event: tk.Event) -> None:
        self._display_preview()

    def _display_preview(self) -> None:
        if self._preview_image is None:
            return
        max_width = max(1, self.preview_label.winfo_width() - 10)
        max_height = max(1, self.preview_label.winfo_height() - 10)
        if max_width == 1 or max_height == 1:
            return
        image = self._preview_image
        scale = min(max_width / image.width, max_height / image.height, 1.0)
        if scale < 1.0:
            image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
        self._preview_photo = ImageTk.PhotoImage(image)
        self.preview_label.configure(image=self._preview_photo, text="")

    def _update_progress(self, event: ProgressEvent) -> None:
        fraction = min(1.0, max(0.0, event.fraction))
        now = time.monotonic()
        elapsed = now - self._phase_started.setdefault(event.phase, now)
        if fraction >= 1:
            progress_text = "100%  Complete"
        elif fraction > 0:
            remaining = elapsed * (1 - fraction) / fraction
            progress_text = f"{fraction * 100:.0f}%  {format_duration(remaining)} remaining"
        else:
            progress_text = "0%  Calculating"
        if event.phase == "Rendering overlays":
            self.overlay_progress_value.set(fraction * 100)
            self.overlay_progress_text.set(progress_text)
        else:
            self.video_progress_value.set(fraction * 100)
            self.video_progress_text.set(progress_text)
        self.status_text.set(f"{event.phase}: {event.detail}")

    def _finish_render(self, message: str) -> None:
        self._render_token = None
        self.create_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.status_text.set(message)
        if message.startswith("Created"):
            self.video_progress_value.set(100.0)
            self.video_progress_text.set("100%  Complete")


def main() -> int:
    root = tk.Tk()
    TriviaCountdownApp(root)
    if os.environ.get("TRIVIA_COUNTDOWN_SMOKE_TEST") == "1":
        root.update_idletasks()
        root.destroy()
        return 0
    root.mainloop()
    return 0
