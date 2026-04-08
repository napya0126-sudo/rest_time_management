import tkinter as tk
from tkinter import messagebox
import argparse
from dataclasses import dataclass
from enum import Enum, auto
from datetime import datetime, timedelta


class Phase(Enum):
    WORK = auto()
    BREAK = auto()


@dataclass
class TimerConfig:
    work_seconds: int = 90 * 60
    break_seconds: int = 15 * 60
    snooze_seconds: int = 5 * 60
    emergency_hold_seconds: int = 3


class RestTimeApp:
    def __init__(self, root: tk.Tk, config: TimerConfig):
        self.root = root
        self.config = config

        self.phase = Phase.WORK
        self.phase_end_time = datetime.now() + timedelta(seconds=self.config.work_seconds)
        self.session_active = False
        self.overlay: tk.Toplevel | None = None
        self.phase_job_id: str | None = None
        self.emergency_job_id: str | None = None

        self.root.title("Rest Time Manager")
        self.root.geometry("520x240")
        self.root.configure(bg="#F5F5F7")
        self.root.attributes("-topmost", True)

        self.status_label = tk.Label(
            self.root,
            text="",
            fg="#222222",
            bg="#F5F5F7",
            font=("Helvetica", 18),
        )
        self.status_label.pack(pady=(28, 8))

        self.countdown_label = tk.Label(
            self.root,
            text="",
            fg="#111111",
            bg="#F5F5F7",
            font=("Helvetica", 42, "bold"),
        )
        self.countdown_label.pack(pady=(8, 16))

        self.info_label = tk.Label(
            self.root,
            text=(
                f"Cycle: {self.config.work_seconds // 60} min work / {self.config.break_seconds // 60} min break\n"
                f"Emergency unlock: hold Esc for {self.config.emergency_hold_seconds}s during break"
            ),
            fg="#666666",
            bg="#F5F5F7",
            font=("Helvetica", 11),
            justify="center",
        )
        self.info_label.pack()

        self.session_button = tk.Button(
            self.root,
            text="Start Work Session",
            command=self.toggle_session,
            bg="#111111",
            fg="#FFFFFF",
            activebackground="#2A2A2A",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=18,
            pady=8,
            font=("Helvetica", 11, "bold"),
        )
        self.session_button.pack(pady=(16, 0))

        self.update_main_ui()

    def run(self):
        self.root.mainloop()

    def tick(self):
        if not self.session_active:
            self.phase_job_id = None
            return

        now = datetime.now()
        remaining = self.phase_end_time - now
        remaining_seconds = max(0, int(remaining.total_seconds()))

        if self.phase == Phase.WORK:
            self.update_work_countdown(remaining_seconds)
            if remaining_seconds <= 0:
                self.show_break_prompt()
                return
        else:
            self.update_break_countdown(remaining_seconds)
            if remaining_seconds <= 0:
                self.end_break_mode()
                return

        self.phase_job_id = self.root.after(1000, self.tick)

    def update_main_ui(self):
        if not self.session_active:
            self.status_label.config(text="IDLE")
            self.countdown_label.config(text="--:--")
            self.session_button.config(text="Start Work Session")
        elif self.phase == Phase.WORK:
            self.status_label.config(text="WORK")
            self.session_button.config(text="Stop Session")
        else:
            self.status_label.config(text="BREAK")
            self.session_button.config(text="Stop Session")

    def update_work_countdown(self, remaining_seconds: int):
        self.countdown_label.config(text=self.format_mmss(remaining_seconds))

    def update_break_countdown(self, remaining_seconds: int):
        if self.overlay:
            self.overlay_countdown_label.config(text=self.format_mmss(remaining_seconds))

    def show_break_prompt(self):
        if not self.session_active:
            return
        self.cancel_phase_job()
        self.root.attributes("-topmost", True)
        self.root.lift()

        answer = messagebox.askyesnocancel(
            "Break Reminder",
            (
                "Would you like to start your break now?\n\n"
                f"Yes: Start break\nNo: Snooze for {self.config.snooze_seconds // 60} min"
            ),
            parent=self.root,
        )

        if answer is True:
            self.start_break_mode()
        elif answer is False:
            self.snooze_work()
        else:
            self.snooze_work()

    def snooze_work(self):
        self.phase = Phase.WORK
        self.phase_end_time = datetime.now() + timedelta(seconds=self.config.snooze_seconds)
        self.update_main_ui()
        self.tick()

    def start_break_mode(self):
        if not self.session_active:
            return
        self.phase = Phase.BREAK
        self.phase_end_time = datetime.now() + timedelta(seconds=self.config.break_seconds)
        self.update_main_ui()

        self.overlay = tk.Toplevel(self.root)
        self.overlay.configure(bg="#DADADA")
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-topmost", True)
        # Keep foreground readable while allowing background apps to be visible.
        self.overlay.attributes("-alpha", 0.45)
        self.overlay.overrideredirect(True)
        self.overlay.focus_force()

        card = tk.Frame(self.overlay, bg="#F7F7F7", bd=0, highlightthickness=0)
        card.place(relx=0.5, rely=0.5, anchor="center", width=700, height=420)

        title = tk.Label(
            card,
            text="Take a break",
            fg="#1B1B1B",
            bg="#F7F7F7",
            font=("Helvetica", 36),
        )
        title.pack(pady=(48, 18))

        subtitle = tk.Label(
            card,
            text="Break mode is active",
            fg="#666666",
            bg="#F7F7F7",
            font=("Helvetica", 16),
        )
        subtitle.pack()

        self.overlay_countdown_label = tk.Label(
            card,
            text="",
            fg="#111111",
            bg="#F7F7F7",
            font=("Helvetica", 86, "bold"),
        )
        self.overlay_countdown_label.pack(pady=(28, 8))

        description = tk.Label(
            card,
            text=f"Emergency only: hold Esc for {self.config.emergency_hold_seconds}s to unlock",
            fg="#7A7A7A",
            bg="#F7F7F7",
            font=("Helvetica", 12),
            justify="center",
        )
        description.pack(pady=(8, 0))

        hint_line = tk.Frame(card, bg="#E3E3E3", height=1)
        hint_line.pack(side="bottom", fill="x", padx=40, pady=(0, 28))

        hint = tk.Label(
            card,
            text="Breathe deeply and relax your eyes and shoulders",
            fg="#8A8A8A",
            bg="#F7F7F7",
            font=("Helvetica", 12),
        )
        hint.pack(side="bottom", pady=(0, 14))

        # オーバーレイ全体をクリックしてもフォーカスを戻す。
        self.overlay.bind("<Button-1>", lambda _e: self.overlay.focus_force())

        title = tk.Label(
            self.overlay,
            text="",
            bg="#DADADA",
            fg="#DADADA",
            font=("Helvetica", 1),
        )
        title.place(x=0, y=0)

        self.overlay.bind("<Escape>", self.on_emergency_press)
        self.overlay.bind("<KeyRelease-Escape>", self.on_emergency_release)

        self.tick()

    def end_break_mode(self):
        if self.overlay is not None:
            self.overlay.destroy()
            self.overlay = None

        self.cancel_emergency_job()
        if not self.session_active:
            self.update_main_ui()
            return
        self.phase = Phase.WORK
        self.phase_end_time = datetime.now() + timedelta(seconds=self.config.work_seconds)
        self.update_main_ui()
        self.tick()

    def emergency_unlock(self):
        if self.phase == Phase.BREAK:
            self.end_break_mode()

    def on_emergency_press(self, _event):
        if self.emergency_job_id is None:
            self.emergency_job_id = self.root.after(
                self.config.emergency_hold_seconds * 1000,
                self.emergency_unlock,
            )

    def on_emergency_release(self, _event):
        self.cancel_emergency_job()

    def cancel_phase_job(self):
        if self.phase_job_id is not None:
            self.root.after_cancel(self.phase_job_id)
            self.phase_job_id = None

    def cancel_emergency_job(self):
        if self.emergency_job_id is not None:
            self.root.after_cancel(self.emergency_job_id)
            self.emergency_job_id = None

    def toggle_session(self):
        if self.session_active:
            self.stop_session()
        else:
            self.start_session()

    def start_session(self):
        self.session_active = True
        self.phase = Phase.WORK
        self.phase_end_time = datetime.now() + timedelta(seconds=self.config.work_seconds)
        self.cancel_phase_job()
        self.update_main_ui()
        self.tick()

    def stop_session(self):
        self.session_active = False
        self.cancel_phase_job()
        if self.phase == Phase.BREAK:
            self.end_break_mode()
        self.phase = Phase.WORK
        self.update_main_ui()

    @staticmethod
    def format_mmss(total_seconds: int) -> str:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


def main():
    parser = argparse.ArgumentParser(description="Rest cycle management app")
    parser.add_argument("--demo", action="store_true", help="Run in short demo mode")
    parser.add_argument("--work-seconds", type=int, default=None, help="Work duration in seconds")
    parser.add_argument("--break-seconds", type=int, default=None, help="Break duration in seconds")
    parser.add_argument("--snooze-seconds", type=int, default=None, help="Snooze duration in seconds")
    args = parser.parse_args()

    config = TimerConfig()
    if args.demo:
        config = TimerConfig(work_seconds=20, break_seconds=15, snooze_seconds=10, emergency_hold_seconds=2)
    if args.work_seconds is not None:
        config.work_seconds = max(1, args.work_seconds)
    if args.break_seconds is not None:
        config.break_seconds = max(1, args.break_seconds)
    if args.snooze_seconds is not None:
        config.snooze_seconds = max(1, args.snooze_seconds)

    root = tk.Tk()
    app = RestTimeApp(root, config)
    app.run()


if __name__ == "__main__":
    main()
