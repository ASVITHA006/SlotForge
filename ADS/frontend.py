# frontend.py
import subprocess
import tkinter as tk
from tkinter import scrolledtext, messagebox, font, ttk
from datetime import datetime
import os
import re

BACKEND_EXE = "backend.exe"   # must be in same folder or provide path
LOG_FILE = "booking_log.txt"  # same as backend's logfile

# ----------------- Backend bridge -----------------
def run_backend(cmd_args):
    """Run backend.exe with list of arguments (strings) and return stdout (str)."""
    try:
        proc = subprocess.run([BACKEND_EXE] + cmd_args, capture_output=True, text=True, check=False)
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        if proc.returncode != 0:
            # return stderr if available
            return err or out or f"[backend returned non-zero status {proc.returncode}]"
        return out
    except FileNotFoundError:
        return f"ERROR: {BACKEND_EXE} not found. Compile backend and place it here."

# ----------------- Log parser to rebuild booked set -----------------
def parse_booked_from_log():
    """
    Parse booking_log.txt to reconstruct current booked slots.
    We look for lines containing 'Smart Booking', 'Manual Booking', and 'Delete'
    with 'Room X, Slot Y' occurrences and replay them.
    """
    booked = set()
    if not os.path.exists(LOG_FILE):
        return booked

    # Pattern to find "Room <num>, Slot <num>"
    pattern = re.compile(r"Room\s*([0-9]+)\s*,\s*Slot\s*([0-9]+)")
    with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Determine action: presence of 'Smart Booking' or 'Manual Booking' or 'Delete'
            action = None
            if "Smart Booking" in line or "Manual Booking" in line:
                action = "add"
            elif "Delete" in line or "Deleted" in line:
                action = "remove"
            else:
                # skip unrelated lines
                continue

            m = pattern.search(line)
            if m:
                try:
                    room = int(m.group(1))
                    slot = int(m.group(2))
                except:
                    continue
                # convert to index
                # we don't know slots per room from logfile; frontend assumes default 15 slots
                index = (room - 1) * 15 + (slot - 1)
                if action == "add":
                    booked.add(index)
                else:
                    booked.discard(index)
    return booked

# ----------------- GUI (SchedulerGUI-like) -----------------
class SchedulerGUI:
    def __init__(self, root):
        # GUI constants (must match backend's rooms & slots)
        self.rooms = 10
        self.slots = 15
        self.total_slots = self.rooms * self.slots

        # local state
        self.booked = set()
        self.selected_slots = set()

        self.root = root
        self.root.title("Smart Conference Scheduler")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        # styles/colors/fonts
        self.setup_styles()

        # layout: paned window with sidebar and main content
        self.paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.sidebar_frame = ttk.Frame(self.paned_window, width=300, style="Sidebar.TFrame")
        self.sidebar_frame.pack_propagate(False)
        self.main_content_frame = ttk.Frame(self.paned_window)

        self.paned_window.add(self.sidebar_frame, weight=1)
        self.paned_window.add(self.main_content_frame, weight=4)

        self.create_sidebar_widgets()
        self.create_main_content_widgets()

        # load booked from log to reflect backend state
        self.reload_booked_and_refresh()

    def setup_styles(self):
        self.colors = {
            "bg": "#f0f2f5",
            "sidebar": "#ffffff",
            "primary": "#0078d4",
            "accent": "#107c10",
            "danger": "#d9534f",
            "text": "#201f1e",
            "light_text": "#605e5c",
            "border": "#e1dfdd",
            "available": "#4CAF50",
            "booked": "#f44336",
            "selected": "#FF9800"
        }
        self.fonts = {
            "header": font.Font(family="Segoe UI", size=18, weight="bold"),
            "subheader": font.Font(family="Segoe UI", size=12, weight="bold"),
            "body": font.Font(family="Segoe UI", size=10),
            "button": font.Font(family="Segoe UI", size=10, weight="bold")
        }

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Sidebar.TFrame", background=self.colors["sidebar"])
        style.configure("Header.TLabel", background=self.colors["sidebar"], foreground=self.colors["primary"], font=self.fonts["header"])
        style.configure("Subheader.TLabel", background=self.colors["sidebar"], foreground=self.colors["text"], font=self.fonts["subheader"])
        style.configure("Body.TLabel", background=self.colors["sidebar"], foreground=self.colors["light_text"], font=self.fonts["body"])
        style.configure("TButton", font=self.fonts["button"], padding=(8, 6))
        # accents (ttk won't color background on some platforms; we'll use tk.Button where needed)

    def create_sidebar_widgets(self):
        content_frame = ttk.Frame(self.sidebar_frame, padding=20, style="Sidebar.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(content_frame, text="Smart Scheduler", style="Header.TLabel").pack(anchor="w", pady=(0, 20))

        ttk.Label(content_frame, text="Actions", style="Subheader.TLabel").pack(anchor="w", pady=(10, 5))

        # Use tk.Button for colored accent/danger look
        tk.Button(content_frame, text="Find & Book First Available", bg=self.colors["accent"], fg="white",
                  font=self.fonts["button"], command=self.smart_booking).pack(fill=tk.X, pady=5)
        tk.Button(content_frame, text="Book Selected Slots", bg=self.colors["primary"], fg="white",
                  font=self.fonts["button"], command=self.book_selected_slots).pack(fill=tk.X, pady=5)
        tk.Button(content_frame, text="Delete a Booking", bg=self.colors["danger"], fg="white",
                  font=self.fonts["button"], command=self.delete_booking).pack(fill=tk.X, pady=5)
        tk.Button(content_frame, text="Clear Selection", bg="#888", fg="white",
                  font=self.fonts["button"], command=self.clear_slot_selection).pack(fill=tk.X, pady=5)

        ttk.Label(content_frame, text="Views", style="Subheader.TLabel").pack(anchor="w", pady=(20, 5))
        ttk.Button(content_frame, text="View All Bookings List", command=self.show_bookings_window).pack(fill=tk.X, pady=5)
        ttk.Button(content_frame, text="Show VEB Tree", command=self.show_veb_tree_window).pack(fill=tk.X, pady=5)

        ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, pady=20)
        ttk.Label(content_frame, text="Availability Summary", style="Subheader.TLabel").pack(anchor="w", pady=(0, 10))

        self.summary_text = tk.StringVar()
        ttk.Label(content_frame, textvariable=self.summary_text, style="Body.TLabel", wraplength=250).pack(anchor="w")

    def create_main_content_widgets(self):
        header_frame = ttk.Frame(self.main_content_frame, padding=(20, 10))
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="Conference Room Status", font=self.fonts["header"], foreground=self.colors["text"]).pack(side=tk.LEFT)

        legend_frame = ttk.Frame(header_frame)
        legend_frame.pack(side=tk.RIGHT)
        for status, color in [("Available", self.colors["available"]), ("Booked", self.colors["booked"]), ("Selected", self.colors["selected"])]:
            tk.Frame(legend_frame, width=15, height=15, bg=color).pack(side=tk.LEFT, padx=(10, 2))
            ttk.Label(legend_frame, text=status, font=self.fonts["body"], foreground=self.colors["light_text"]).pack(side=tk.LEFT)

        canvas_frame = ttk.Frame(self.main_content_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.rooms_canvas = tk.Canvas(canvas_frame, bg=self.colors["bg"], highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.rooms_canvas.yview)
        self.rooms_canvas.configure(yscrollcommand=v_scrollbar.set)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rooms_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollable_frame = ttk.Frame(self.rooms_canvas)
        self.canvas_window = self.rooms_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.rooms_canvas.bind("<Configure>", self.on_canvas_configure)
        self.rooms_canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    # ---------- Rendering ----------
    def refresh_display(self):
        # update summary
        self.summary_text.set(self.get_availability_summary())

        # clear
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # draw rooms and slots
        for room in range(1, self.rooms + 1):
            room_frame = ttk.Frame(self.scrollable_frame, padding=15, style="Sidebar.TFrame")
            room_frame.pack(fill=tk.X, padx=10, pady=5)

            ttk.Label(room_frame, text=f"Conference Room {room}", font=self.fonts["subheader"], background='white').pack(anchor='w', pady=(0, 10))

            slots_frame = ttk.Frame(room_frame, style="Sidebar.TFrame")
            slots_frame.pack(fill=tk.X)

            slots_per_row = 10
            for i in range(self.slots):
                slot = i + 1
                index = (room - 1) * self.slots + (slot - 1)
                slot_info = (room, slot, index)
                is_booked = index in self.booked
                is_selected = slot_info in self.selected_slots

                color = self.colors["available"]
                state = "normal"
                if is_booked:
                    color = self.colors["booked"]
                    state = "disabled"
                elif is_selected:
                    color = self.colors["selected"]

                slot_btn = tk.Button(slots_frame, text=f"S{slot}",
                                     width=5, height=2, state=state,
                                     bg=color, fg="white", font=("Segoe UI", 8, "bold"),
                                     relief="flat", borderwidth=0,
                                     command=lambda r=room, s=slot, idx=index: self.toggle_slot_selection(r, s, idx))

                row = i // slots_per_row
                col = i % slots_per_row
                slot_btn.grid(row=row, column=col, padx=2, pady=2)

    # ---------- Actions that call backend ----------
    def smart_booking(self):
        out = run_backend(["smart_book"])
        # backend may return "Room X, Slot Y" or a descriptive message
        messagebox.showinfo("Smart Booking", out)
        # reload booked set from logfile and refresh
        self.reload_booked_and_refresh()

    def book_selected_slots(self):
        if not self.selected_slots:
            messagebox.showwarning("No Selection", "Please select one or more available slots to book.")
            return
        booked = []
        for room, slot, index in list(self.selected_slots):
            # call backend manual_book for each
            out = run_backend(["manual_book", str(room), str(slot)])
            booked.append(out)
        messagebox.showinfo("Booking Results", "\n".join(booked))
        self.selected_slots.clear()
        self.reload_booked_and_refresh()

    def delete_booking(self):
        room = self.prompt_number(f"Enter Room Number (1–{self.rooms}):", 1, self.rooms)
        if not room:
            return
        slot = self.prompt_number(f"Enter Slot Number (1–{self.slots}):", 1, self.slots)
        if not slot:
            return
        out = run_backend(["delete", str(room), str(slot)])
        messagebox.showinfo("Delete Booking", out)
        self.reload_booked_and_refresh()

    def clear_slot_selection(self):
        self.selected_slots.clear()
        self.refresh_display()

    def toggle_slot_selection(self, room, slot, index):
        slot_info = (room, slot, index)
        if slot_info in self.selected_slots:
            self.selected_slots.remove(slot_info)
        else:
            # only allow selection if not booked (we check current booked set)
            if index in self.booked:
                messagebox.showwarning("Already Booked", f"Room {room}, Slot {slot} is already booked.")
                return
            self.selected_slots.add(slot_info)
        self.refresh_display()

    # ---------- Views / Popups ----------
    def show_bookings_window(self):
        # Build a bookings list from self.booked
        if not self.booked:
            text = "📂 No bookings found."
        else:
            lines = ["📋 Current Bookings:"]
            for i, b in enumerate(sorted(self.booked), 1):
                room = b // self.slots + 1
                slot = b % self.slots + 1
                lines.append(f"{i}. Room {room}, Slot {slot}")
            text = "\n".join(lines)
        self.show_popup("All Bookings", text, width=400, height=400)

    def show_veb_tree_window(self):
        # The backend CLI does not produce a textual VEB dump, so we show helpful guidance.
        popup = tk.Toplevel(self.root)
        popup.title("VEB Tree Visualization")
        popup.geometry("800x600")
        frame = ttk.Frame(popup, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="VEB Tree Visualization", font=self.fonts["subheader"]).pack(anchor="w", pady=(0,8))
        veb_text = run_backend(["dump_veb"])
        ttk.Label(frame, text=msg, wraplength=760, style="Body.TLabel").pack(anchor="w", pady=(6,12))
        # show current bookings
        text_area = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=self.fonts["body"])
        text_area.pack(expand=True, fill=tk.BOTH)
        text_area.insert(tk.END, veb_text)
        text_area.config(state=tk.DISABLED)

    def show_popup(self, title, text, width=350, height=250):
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry(f"{width}x{height}")
        text_area = scrolledtext.ScrolledText(popup, wrap=tk.WORD, font=self.fonts["body"])
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        text_area.insert(tk.END, text)
        text_area.config(state=tk.DISABLED)

    def prompt_number(self, message, low, high):
        from tkinter.simpledialog import askinteger
        return askinteger("Input Required", message, minvalue=low, maxvalue=high, parent=self.root)

    # ---------- Utilities ----------
    def get_availability_summary(self):
        out = run_backend(["summary"])
        # backend returns a textual summary; if backend missing, fallback to computed summary
        if out and not out.startswith("ERROR"):
            return out
        free = self.total_slots - len(self.booked)
        return (f"📊 Total Rooms: {self.rooms}\n"
                f"🕓 Slots per Room: {self.slots}\n"
                f"✅ Free Slots: {free}\n"
                f"❌ Booked Slots: {len(self.booked)}")

    def get_bookings_text(self):
        if not self.booked:
            return "📂 No bookings found."
        lines = ["📋 Current Bookings:"]
        for i, b in enumerate(sorted(self.booked), 1):
            room = b // self.slots + 1
            slot = b % self.slots + 1
            lines.append(f"{i}. Room {room}, Slot {slot}")
        return "\n".join(lines)

    def reload_booked_and_refresh(self):
        # parse log file to reconstruct booked set, then refresh display
        self.booked = parse_booked_from_log()
        self.selected_slots.clear()
        self.refresh_display()

    # ---------- Canvas scroll handlers ----------
    def on_frame_configure(self, event):
        self.rooms_canvas.configure(scrollregion=self.rooms_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.rooms_canvas.itemconfig(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        if event.delta:
            self.rooms_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            if event.num == 5:
                self.rooms_canvas.yview_scroll(1, "units")
            elif event.num == 4:
                self.rooms_canvas.yview_scroll(-1, "units")


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except:
        pass
    gui = SchedulerGUI(root)
    root.mainloop()
