#!/usr/bin/env python3
import sys
import os
import copy
import datetime
import threading
import io

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QTextEdit,
    QGroupBox, QGridLayout, QFrame, QSplitter, QFileDialog,
    QSpinBox, QDoubleSpinBox, QSlider, QStackedWidget, QScrollArea,
    QProgressBar, QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCursor, QIcon, QFontDatabase

# ─────────────────────────────────────────────
# COLOURS & STYLES
# ─────────────────────────────────────────────
BG_DARK     = "#0e1117"
BG_PANEL    = "#161b22"
BG_CARD     = "#1c2230"
BG_HOVER    = "#21293a"
ACCENT      = "#3b82f6"
ACCENT_DIM  = "#1d4ed8"
GREEN       = "#22c55e"
AMBER       = "#f59e0b"
RED_C       = "#ef4444"
TEXT_PRI    = "#e2e8f0"
TEXT_SEC    = "#94a3b8"
TEXT_MUT    = "#475569"
BORDER      = "#2d3748"

STYLE_MAIN = f"""
QMainWindow, QWidget {{ background: {BG_DARK}; color: {TEXT_PRI}; }}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: 600;
    color: {TEXT_SEC};
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; }}
QListWidget {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    outline: none;
    color: {TEXT_PRI};
    font-size: 13px;
}}
QListWidget::item {{ padding: 8px 12px; border-radius: 4px; }}
QListWidget::item:hover {{ background: {BG_HOVER}; }}
QListWidget::item:selected {{
    background: {ACCENT};
    color: white;
}}
QTextEdit {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    color: #a8c4e0;
    font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
    font-size: 12px;
    selection-background-color: {ACCENT_DIM};
}}
QPushButton {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    color: {TEXT_PRI};
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{ background: {BG_HOVER}; border-color: {ACCENT}; }}
QPushButton:pressed {{ background: {ACCENT_DIM}; }}
QPushButton:disabled {{ color: {TEXT_MUT}; border-color: {BG_CARD}; }}
QSpinBox, QDoubleSpinBox {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 5px;
    color: {TEXT_PRI};
    padding: 4px 8px;
    font-size: 13px;
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: {BG_HOVER}; border: none; width: 18px;
}}
QComboBox {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 5px;
    color: {TEXT_PRI};
    padding: 5px 10px;
    font-size: 13px;
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    color: {TEXT_PRI};
    selection-background-color: {ACCENT};
}}
QProgressBar {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 3px; }}
QScrollBar:vertical {{
    background: {BG_PANEL}; width: 6px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 3px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QSplitter::handle {{ background: {BORDER}; }}
QFrame[frameShape="4"] {{ color: {BORDER}; }}
QLabel {{ color: {TEXT_PRI}; }}
"""

ACCENT_BTN_STYLE = f"""
QPushButton {{
    background: {ACCENT};
    border: none;
    border-radius: 6px;
    color: white;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
QPushButton:hover {{ background: {ACCENT_DIM}; }}
QPushButton:pressed {{ background: #1e40af; }}
QPushButton:disabled {{
    background: {TEXT_MUT};
    color: {BG_DARK};
}}
"""

DANGER_BTN_STYLE = f"""
QPushButton {{
    background: transparent;
    border: 1px solid {RED_C};
    border-radius: 6px;
    color: {RED_C};
    padding: 8px 16px;
    font-size: 13px;
}}
QPushButton:hover {{ background: rgba(239,68,68,0.12); }}
QPushButton:pressed {{ background: rgba(239,68,68,0.25); }}
"""


# ─────────────────────────────────────────────
# WORKER THREAD — runs the solver off the GUI thread
# ─────────────────────────────────────────────
class SolverWorker(QThread):
    log_line  = pyqtSignal(str)
    finished  = pyqtSignal(int, float)   # score, elapsed_seconds
    error     = pyqtSignal(str)

    def __init__(self, input_path, solver_number, genetic_params, annealing_baseline):
        super().__init__()
        self.input_path = input_path
        self.solver_number = solver_number
        self.genetic_params = genetic_params          # dict or None
        self.annealing_baseline = annealing_baseline  # int 1-4
        self._stop = False

    def run(self):
        # Redirect stdout so print() calls appear in the GUI log
        old_stdout = sys.stdout
        log_buf = _LogStream(self.log_line)
        sys.stdout = log_buf

        try:
            start = datetime.datetime.now()

            # ── import here so paths are correct ──
            sys.path.insert(0, os.path.dirname(__file__))

            from src.parser import parse_input
            from src.simulator import simulate_assignment, validate_assignment
            from src.writer import write_solution
            from src.solvers.greedy_solver import greedy_solver
            from src.solvers.nearest_solver import nearest_vehicle_solver
            from src.solvers.multiagent_solver import multiagent_solver
            from src.solvers.simulated_annealing_solver import simulated_annealing_solver
            from src.solvers.genetic_solver import genetic_solver

            problem = parse_input(self.input_path)
            print(f"Parsed: {problem.num_rides} rides, {problem.fleet_size} vehicles")
            print(f"Grid: {problem.rows}×{problem.cols}  |  Time steps: {problem.time_steps}  |  Bonus: {problem.bonus}\n")

            n = self.solver_number
            if n == 1:
                assignment = nearest_vehicle_solver(problem)
            elif n == 2:
                assignment = greedy_solver(problem)
            elif n == 3:
                assignment = simulated_annealing_solver(problem, self.annealing_baseline)
            elif n == 4:
                assignment = multiagent_solver(problem)
            elif n == 5:
                # Monkey-patch get_parameters to return GUI values
                import src.solvers.genetic_solver as gm
                gp = self.genetic_params
                def _patched_get_parameters(num_rides, fleet_size):
                    print(f"\n=== Genetic Algorithm Parameters ===")
                    print(f"  Population size : {gp['pop_size']}")
                    print(f"  Generations     : {gp['generations']}")
                    print(f"  Mutation rate   : {gp['mutation_rate']:.0%}")
                    print(f"  Elite fraction  : {gp['elite_fraction']:.0%}")
                    print(f"  Tournament size : {gp['tournament_size']}")
                    return (gp['pop_size'], gp['generations'],
                            gp['mutation_rate'], gp['elite_fraction'],
                            gp['tournament_size'])
                gm.get_parameters = _patched_get_parameters
                assignment = genetic_solver(problem)

            if not validate_assignment(assignment, problem.num_rides):
                self.error.emit("Invalid assignment generated.")
                return

            score, vehicles = simulate_assignment(problem, copy.deepcopy(assignment))

            # Write output
            out_dir = os.path.join(os.path.dirname(__file__), "output")
            os.makedirs(out_dir, exist_ok=True)
            solver_names = {1:"nearest",2:"greedy",3:"annealing",4:"multi",5:"genetic"}
            basename = os.path.splitext(os.path.basename(self.input_path))[0]
            out_file = os.path.join(out_dir, f"{solver_names[n]}_{basename}_output.txt")
            write_solution(out_file, assignment, problem.fleet_size)

            elapsed = (datetime.datetime.now() - start).total_seconds()

            print(f"\n{'─'*45}")
            print(f"  ✓  Total score  : {score:,}")
            print(f"  ✓  Elapsed time : {elapsed:.1f}s")
            print(f"  ✓  Output saved : {out_file}")
            print(f"{'─'*45}")

            self.finished.emit(score, elapsed)

        except Exception as exc:
            import traceback
            self.error.emit(traceback.format_exc())
        finally:
            sys.stdout = old_stdout


class _LogStream:
    """Bridges print() calls to Qt signal."""
    def __init__(self, signal):
        self._sig = signal
        self._buf = ""

    def write(self, text):
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self._sig.emit(line)

    def flush(self):
        if self._buf:
            self._sig.emit(self._buf)
            self._buf = ""


# ─────────────────────────────────────────────
# BADGE LABEL
# ─────────────────────────────────────────────
class Badge(QLabel):
    def __init__(self, text, color=ACCENT, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                background: {color}22;
                border: 1px solid {color}66;
                border-radius: 10px;
                color: {color};
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)


# ─────────────────────────────────────────────
# STAT CARD
# ─────────────────────────────────────────────
class StatCard(QFrame):
    def __init__(self, label, value="—", color=ACCENT, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setSpacing(2)
        lay.setContentsMargins(14, 10, 14, 10)

        self._val = QLabel(value)
        self._val.setFont(QFont("", 22, QFont.Weight.Bold))
        self._val.setStyleSheet(f"color: {color}; border: none; background: transparent;")

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 11px; border: none; background: transparent;")

        lay.addWidget(self._val)
        lay.addWidget(lbl)

    def set_value(self, v):
        self._val.setText(str(v))


# ─────────────────────────────────────────────
# MAIN WINDOW
# ─────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hash Code 2018 — Self-driving Rides")
        self.setMinimumSize(1100, 720)
        self.resize(1300, 800)

        self._worker = None
        self._running = False

        self.setStyleSheet(STYLE_MAIN)
        self._build_ui()
        self._refresh_file_list()

    # ── UI construction ────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # ── header bar ──
        root_lay.addWidget(self._make_header())

        # ── body splitter ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.addWidget(self._make_left_panel())
        splitter.addWidget(self._make_right_panel())
        splitter.setSizes([400, 900])
        root_lay.addWidget(splitter, 1)

        # ── status bar ──
        root_lay.addWidget(self._make_status_bar())

    def _make_header(self):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"background: {BG_PANEL}; border-bottom: 1px solid {BORDER};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        title = QLabel("Self-driving Rides Solver")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_PRI}; letter-spacing: 0.5px;")

        sub = QLabel("Hash Code 2018")
        sub.setStyleSheet(f"color: {TEXT_MUT}; font-size: 12px;")

        lay.addWidget(title)
        lay.addSpacing(12)
        lay.addWidget(sub)
        lay.addStretch()
        lay.addWidget(Badge("PyQt6 GUI", ACCENT))
        return bar

    def _make_left_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(330)
        panel.setMaximumWidth(460)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 16, 8, 16)
        lay.setSpacing(14)

        # ── file selector ──
        file_group = QGroupBox("Input File")
        fg_lay = QVBoxLayout(file_group)
        fg_lay.setSpacing(8)

        self._file_list = QListWidget()
        self._file_list.setMinimumHeight(130)
        self._file_list.currentItemChanged.connect(self._on_file_selected)
        fg_lay.addWidget(self._file_list)

        btn_row = QHBoxLayout()
        btn_browse = QPushButton("＋ Browse…")
        btn_browse.clicked.connect(self._browse_file)
        btn_refresh = QPushButton("↺ Refresh")
        btn_refresh.clicked.connect(self._refresh_file_list)
        btn_row.addWidget(btn_browse)
        btn_row.addWidget(btn_refresh)
        fg_lay.addLayout(btn_row)

        # file info strip
        self._file_info = QLabel("No file selected")
        self._file_info.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
        self._file_info.setWordWrap(True)
        fg_lay.addWidget(self._file_info)

        lay.addWidget(file_group)

        # ── solver selector ──
        solver_group = QGroupBox("Solver")
        sg_lay = QVBoxLayout(solver_group)
        sg_lay.setSpacing(8)

        self._solver_combo = QComboBox()
        self._solver_combo.addItems([
            "1 · Nearest vehicle",
            "2 · Greedy",
            "3 · Simulated Annealing",
            "4 · Multi-agent (Contract Net)",
            "5 · Genetic Algorithm",
        ])
        self._solver_combo.currentIndexChanged.connect(self._on_solver_changed)
        sg_lay.addWidget(self._solver_combo)

        # ── stacked param panels ──
        self._param_stack = QStackedWidget()
        self._param_stack.addWidget(QWidget())          # 0: nearest — no params
        self._param_stack.addWidget(QWidget())          # 1: greedy  — no params
        self._param_stack.addWidget(self._make_annealing_params())  # 2
        self._param_stack.addWidget(QWidget())          # 3: multi   — no params
        self._param_stack.addWidget(self._make_genetic_params())    # 4
        sg_lay.addWidget(self._param_stack)

        lay.addWidget(solver_group)
        lay.addStretch()

        # ── run / stop ──
        self._run_btn = QPushButton("▶  Run Solver")
        self._run_btn.setStyleSheet(ACCENT_BTN_STYLE)
        self._run_btn.setMinimumHeight(42)
        self._run_btn.clicked.connect(self._run_solver)

        self._stop_btn = QPushButton("■  Stop")
        self._stop_btn.setStyleSheet(DANGER_BTN_STYLE)
        self._stop_btn.setMinimumHeight(42)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_solver)

        btn_run_row = QHBoxLayout()
        btn_run_row.addWidget(self._run_btn, 3)
        btn_run_row.addWidget(self._stop_btn, 1)
        lay.addLayout(btn_run_row)

        return panel

    def _make_annealing_params(self):
        w = QWidget()
        lay = QGridLayout(w)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(8)

        lay.addWidget(QLabel("Baseline solver:"), 0, 0)
        self._ann_baseline = QComboBox()
        self._ann_baseline.addItems([
            "1 · Nearest",
            "2 · Greedy",
            "3 · Multi-agent",
            "4 · Best of all three",
        ])
        self._ann_baseline.setCurrentIndex(3)
        lay.addWidget(self._ann_baseline, 0, 1)
        return w

    def _make_genetic_params(self):
        w = QWidget()
        lay = QGridLayout(w)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(8)
        lay.setColumnStretch(1, 1)

        def row(r, label, widget, tip=""):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
            lay.addWidget(lbl, r, 0)
            lay.addWidget(widget, r, 1)
            if tip:
                widget.setToolTip(tip)

        self._g_pop = QSpinBox()
        self._g_pop.setRange(10, 2000); self._g_pop.setValue(50)
        row(0, "Population size", self._g_pop, "Candidate solutions per generation (10–2000)")

        self._g_gens = QSpinBox()
        self._g_gens.setRange(10, 10000); self._g_gens.setValue(200)
        row(1, "Generations", self._g_gens, "Evolution cycles (10–10 000)")

        self._g_mut = QDoubleSpinBox()
        self._g_mut.setRange(0.0, 1.0); self._g_mut.setSingleStep(0.01); self._g_mut.setValue(0.05)
        row(2, "Mutation rate", self._g_mut, "Probability of mutation per offspring (0–1)")

        self._g_elite = QDoubleSpinBox()
        self._g_elite.setRange(0.0, 0.5); self._g_elite.setSingleStep(0.01); self._g_elite.setValue(0.10)
        row(3, "Elite fraction", self._g_elite, "Top fraction carried unchanged (0–0.5)")

        self._g_tour = QSpinBox()
        self._g_tour.setRange(2, 20); self._g_tour.setValue(3)
        row(4, "Tournament size", self._g_tour, "Competitors per parent selection (2–20)")

        return w

    def _make_right_panel(self):
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(8, 16, 16, 16)
        lay.setSpacing(12)

        # ── stat cards ──
        cards_row = QHBoxLayout()
        self._card_score   = StatCard("Best Score",      "—",   GREEN)
        self._card_elapsed = StatCard("Elapsed Time",    "—",   AMBER)
        self._card_rides   = StatCard("Rides in File",   "—",   ACCENT)
        self._card_fleet   = StatCard("Fleet Size",      "—",   "#a78bfa")
        for c in (self._card_score, self._card_elapsed, self._card_rides, self._card_fleet):
            cards_row.addWidget(c)
        lay.addLayout(cards_row)

        # ── log header ──
        log_hdr = QHBoxLayout()
        log_lbl = QLabel("Run Log")
        log_lbl.setFont(QFont("", 13, QFont.Weight.Bold))
        log_lbl.setStyleSheet(f"color: {TEXT_PRI};")

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setVisible(False)
        self._progress.setMaximumWidth(160)
        self._progress.setFixedHeight(6)

        btn_clear = QPushButton("Clear")
        btn_clear.setMaximumWidth(70)
        btn_clear.clicked.connect(lambda: self._log.clear())

        btn_save_log = QPushButton("Save Log")
        btn_save_log.setMaximumWidth(90)
        btn_save_log.clicked.connect(self._save_log)

        log_hdr.addWidget(log_lbl)
        log_hdr.addSpacing(10)
        log_hdr.addWidget(self._progress)
        log_hdr.addStretch()
        log_hdr.addWidget(btn_clear)
        log_hdr.addWidget(btn_save_log)
        lay.addLayout(log_hdr)

        # ── log area ──
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._append_log("Hash Code 2018 Self-driving Rides Solver", TEXT_SEC)
        lay.addWidget(self._log, 1)

        return panel

    def _make_status_bar(self):
        bar = QFrame()
        bar.setFixedHeight(32)
        bar.setStyleSheet(f"background: {BG_PANEL}; border-top: 1px solid {BORDER};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)

        self._status_lbl = QLabel("Ready")
        self._status_lbl.setStyleSheet(f"color: {TEXT_MUT}; font-size: 12px;")

        self._run_indicator = QLabel("●")
        self._run_indicator.setStyleSheet(f"color: {TEXT_MUT}; font-size: 10px;")

        lay.addWidget(self._run_indicator)
        lay.addSpacing(6)
        lay.addWidget(self._status_lbl)
        lay.addStretch()
        lay.addWidget(QLabel(f"Output → {os.path.join(os.path.dirname(__file__), 'output')}"))

        return bar

    # ── file handling ──────────────────────────
    def _refresh_file_list(self):
        input_dir = os.path.join(os.path.dirname(__file__), "input")
        self._file_list.clear()
        if os.path.isdir(input_dir):
            files = sorted(f for f in os.listdir(input_dir)
                           if os.path.isfile(os.path.join(input_dir, f)))
            for f in files:
                item = QListWidgetItem(f)
                item.setData(Qt.ItemDataRole.UserRole,
                             os.path.join(input_dir, f))
                self._file_list.addItem(item)
        if self._file_list.count() > 0:
            self._file_list.setCurrentRow(0)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Input File",
            os.path.join(os.path.dirname(__file__), "input"),
            "Input Files (*.in *.txt);;All Files (*)"
        )
        if path:
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.ItemDataRole.UserRole, path)
            self._file_list.addItem(item)
            self._file_list.setCurrentItem(item)

    def _on_file_selected(self, item):
        if item is None:
            self._file_info.setText("No file selected")
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from src.parser import parse_input
            p = parse_input(path)
            self._file_info.setText(
                f"{p.rows}×{p.cols} grid  ·  {p.fleet_size} vehicles  ·  "
                f"{p.num_rides} rides  ·  bonus {p.bonus}  ·  T={p.time_steps:,}"
            )
            self._card_rides.set_value(f"{p.num_rides:,}")
            self._card_fleet.set_value(str(p.fleet_size))
        except Exception:
            self._file_info.setText("Could not parse file.")

    def _on_solver_changed(self, idx):
        self._param_stack.setCurrentIndex(idx)

    # ── solver execution ───────────────────────
    def _run_solver(self):
        item = self._file_list.currentItem()
        if item is None:
            self._append_log("⚠  Please select an input file first.", AMBER)
            return

        input_path = item.data(Qt.ItemDataRole.UserRole)
        solver_number = self._solver_combo.currentIndex() + 1

        genetic_params = None
        if solver_number == 5:
            genetic_params = {
                "pop_size":      self._g_pop.value(),
                "generations":   self._g_gens.value(),
                "mutation_rate": self._g_mut.value(),
                "elite_fraction":self._g_elite.value(),
                "tournament_size":self._g_tour.value(),
            }

        annealing_baseline = self._ann_baseline.currentIndex() + 1 if solver_number == 3 else 4

        self._log.clear()
        self._card_score.set_value("…")
        self._card_elapsed.set_value("…")
        self._append_log(f"{'═'*60}", TEXT_MUT)
        self._append_log(f"  NEW RUN  ·  {datetime.datetime.now().strftime('%H:%M:%S')}  ·  {self._solver_combo.currentText()}", ACCENT)
        self._append_log(f"  File: {os.path.basename(input_path)}", TEXT_SEC)
        self._append_log(f"{'═'*60}\n", TEXT_MUT)

        self._set_running(True)

        self._worker = SolverWorker(input_path, solver_number, genetic_params, annealing_baseline)
        self._worker.log_line.connect(self._on_log_line)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _stop_solver(self):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._append_log("\n⚠  Run terminated by user.", AMBER)
            self._set_running(False)

    def _set_running(self, running: bool):
        self._running = running
        self._run_btn.setEnabled(not running)
        self._stop_btn.setEnabled(running)
        self._progress.setVisible(running)
        if running:
            self._run_indicator.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            self._status_lbl.setText("Running…")
        else:
            self._run_indicator.setStyleSheet(f"color: {TEXT_MUT}; font-size: 10px;")
            self._status_lbl.setText("Ready")

    # ── log helpers ────────────────────────────
    def _on_log_line(self, line: str):
        # Colorise lines by content
        if any(x in line for x in ("✓", "Best Score", "Final Best")):
            color = GREEN
        elif any(x in line for x in ("⚠", "Warning", "warn")):
            color = AMBER
        elif any(x in line for x in ("ERROR", "error", "Exception")):
            color = RED_C
        elif line.startswith("  ") or line.startswith("─") or line.startswith("═"):
            color = TEXT_SEC
        else:
            color = "#a8c4e0"
        self._append_log(line, color)

    def _append_log(self, text: str, color: str = "#a8c4e0"):
        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = cursor.charFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text + "\n")
        self._log.setTextCursor(cursor)
        self._log.ensureCursorVisible()

    def _on_finished(self, score: int, elapsed: float):
        self._card_score.set_value(f"{score:,}")
        self._card_elapsed.set_value(f"{elapsed:.1f}s")
        self._set_running(False)
        self._status_lbl.setText(f"Done — score {score:,}  ({elapsed:.1f}s)")

    def _on_error(self, msg: str):
        self._append_log(f"\n{msg}", RED_C)
        self._set_running(False)
        self._status_lbl.setText("Error — see log")

    def _save_log(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Log",
            os.path.join(os.path.dirname(__file__), "logs",
                         f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
            "Text files (*.txt)"
        )
        if path:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(self._log.toPlainText())
            self._status_lbl.setText(f"Log saved → {os.path.basename(path)}")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Make the palette neutral so our stylesheet wins everywhere
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(BG_DARK))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT_PRI))
    palette.setColor(QPalette.ColorRole.Base,            QColor(BG_PANEL))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.Text,            QColor(TEXT_PRI))
    palette.setColor(QPalette.ColorRole.Button,          QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT_PRI))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
