import tkinter as tk
from tkinter import scrolledtext, messagebox, font, ttk
from datetime import datetime

# ======================= Van Emde Boas Tree (Original Logic) =======================
class VEBTree:
    def __init__(self, u):
        self.u = u
        self.min = None
        self.max = None
        if u <= 2:
            self.summary = None
            self.cluster = []
        else:
            self.lower_sqrt_u = 1 << (self.u.bit_length() // 2)
            self.upper_sqrt_u = self.u // self.lower_sqrt_u
            self.summary = None
            self.cluster = [None] * self.upper_sqrt_u

    def high(self, x):
        return x // self.lower_sqrt_u

    def low(self, x):
        return x % self.lower_sqrt_u

    def index(self, x, y):
        return x * self.lower_sqrt_u + y

    def is_member(self, x):
        if x == self.min or x == self.max:
            return True
        elif self.u == 2:
            return False
        else:
            cluster = self.cluster[self.high(x)]
            if cluster is None:
                return False
            return cluster.is_member(self.low(x))

    def insert_empty(self, x):
        self.min = x
        self.max = x

    def insert(self, x):
        if self.min is None:
            self.insert_empty(x)
        else:
            if x < self.min:
                x, self.min = self.min, x
            if self.u > 2:
                high = self.high(x)
                low = self.low(x)
                if self.cluster[high] is None:
                    self.cluster[high] = VEBTree(self.lower_sqrt_u)
                if self.cluster[high].min is None:
                    if self.summary is None:
                        self.summary = VEBTree(self.upper_sqrt_u)
                    self.summary.insert(high)
                    self.cluster[high].insert_empty(low)
                else:
                    self.cluster[high].insert(low)
            if x > self.max:
                self.max = x

    def delete(self, x):
        if self.min == self.max:
            self.min = None
            self.max = None
        elif self.u == 2:
            self.min = 1 - x
            self.max = self.min
        else:
            if x == self.min:
                first_cluster = self.summary.min
                if first_cluster is None:
                    self.min = self.max
                    return
                x = self.index(first_cluster, self.cluster[first_cluster].min)
                self.min = x
            high = self.high(x)
            low = self.low(x)
            if self.cluster[high] is not None:
                self.cluster[high].delete(low)
                if self.cluster[high].min is None:
                    self.summary.delete(high)
                    if x == self.max:
                        summary_max = self.summary.max
                        self.max = self.index(summary_max, self.cluster[summary_max].max) if summary_max is not None else self.min
                elif x == self.max:
                    self.max = self.index(high, self.cluster[high].max)

    def find_min(self):
        return self.min

# ======================= Conference Scheduler (Original Logic) =======================
class ConferenceScheduler:
    def __init__(self):
        self.rooms = 10
        self.slots = 15  # Updated from 48 → 15 slots per room
        self.total_slots = self.rooms * self.slots
        # Use nearest power of 2 >= total_slots for VEB tree
        veb_size = 1
        while veb_size < self.total_slots:
            veb_size *= 2
        self.veb = VEBTree(veb_size)
        self.booked = set()
        self.log_file = "booking_log.txt"

    def log_action(self, action, details):
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {action}: {details}\n")

    def smart_booking(self):
        for i in range(self.total_slots):
            if i not in self.booked:
                self.booked.add(i)
                self.veb.insert(i)
                self.log_action("Smart Booking", f"Room {i // self.slots + 1}, Slot {i % self.slots + 1}")
                return f"✅ Smart Booked → Room {i // self.slots + 1}, Slot {i % self.slots + 1}"
        return "❌ No free slots available."

    def manual_booking(self, room, slot):
        index = (room - 1) * self.slots + (slot - 1)
        if index in self.booked:
            return "⚠️ Slot already booked."
        self.booked.add(index)
        self.veb.insert(index)
        self.log_action("Manual Booking", f"Room {room}, Slot {slot}")
        return f"✅ Manually Booked → Room {room}, Slot {slot}"

    def delete_booking(self, room, slot):
        index = (room - 1) * self.slots + (slot - 1)
        if index not in self.booked:
            return "⚠️ No booking found to delete."
        self.booked.remove(index)
        self.veb.delete(index)
        self.log_action("Deleted", f"Room {room}, Slot {slot}")
        return f"🗑️ Deleted booking → Room {room}, Slot {slot}"

    def availability_summary(self):
        total_free = self.total_slots - len(self.booked)
        return (f"📊 Total Rooms: {self.rooms}\n"
                f"🕓 Slots per Room: {self.slots}\n"
                f"✅ Free Slots: {total_free}\n"
                f"❌ Booked Slots: {len(self.booked)}")

    def view_all_bookings(self):
        if not self.booked:
            return "📂 No bookings found."
        result = "📋 Current Bookings:\n"
        sorted_bookings = sorted(list(self.booked))
        for i, b in enumerate(sorted_bookings, 1):
            room = b // self.slots + 1
            slot = b % self.slots + 1
            result += f"{i}. Room {room}, Slot {slot}\n"
        return result

# ======================= GUI (Refactored for Professional Look & Feel) =======================
class SchedulerGUI:
    def __init__(self, root):
        self.scheduler = ConferenceScheduler()
        self.root = root
        self.root.title("Smart Conference Scheduler")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # --- Style Configuration ---
        self.setup_styles()

        # --- Main Layout ---
        # PanedWindow allows resizing the sidebar
        self.paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left sidebar for controls and info
        self.sidebar_frame = ttk.Frame(self.paned_window, width=300, style="Sidebar.TFrame")
        self.sidebar_frame.pack_propagate(False) # Prevent sidebar from shrinking
        
        # Right main area for room visualization
        self.main_content_frame = ttk.Frame(self.paned_window)

        self.paned_window.add(self.sidebar_frame, weight=1)
        self.paned_window.add(self.main_content_frame, weight=4)

        # --- Populate Widgets ---
        self.create_sidebar_widgets()
        self.create_main_content_widgets()

        # --- Initial Data Load ---
        # initialize selection state before rendering
        self.selected_slots = set()
        self.refresh_display()

    def setup_styles(self):
        # Colors & Fonts
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
        
        # TTK Style Configuration
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Sidebar.TFrame", background=self.colors["sidebar"])
        
        style.configure("Header.TLabel", background=self.colors["sidebar"], foreground=self.colors["primary"], font=self.fonts["header"])
        style.configure("Subheader.TLabel", background=self.colors["sidebar"], foreground=self.colors["text"], font=self.fonts["subheader"])
        style.configure("Body.TLabel", background=self.colors["sidebar"], foreground=self.colors["light_text"], font=self.fonts["body"])

        style.configure("TButton", font=self.fonts["button"], padding=(10, 8))
        style.map("TButton",
            foreground=[('active', 'white'), ('!disabled', 'white')],
            background=[('active', self.colors["primary"]), ('!disabled', self.colors["primary"])],
            bordercolor=[('!disabled', self.colors["primary"])]
        )
        style.configure("Accent.TButton", background=self.colors["accent"], bordercolor=self.colors["accent"])
        style.map("Accent.TButton", background=[('active', self.colors["accent"])])

        style.configure("Danger.TButton", background=self.colors["danger"], bordercolor=self.colors["danger"])
        style.map("Danger.TButton", background=[('active', self.colors["danger"])])

    def create_sidebar_widgets(self):
        # Padding for all sidebar content
        content_frame = ttk.Frame(self.sidebar_frame, padding=20, style="Sidebar.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(content_frame, text="Smart Scheduler", style="Header.TLabel").pack(anchor="w", pady=(0, 20))

        # --- Booking Actions ---
        ttk.Label(content_frame, text="Actions", style="Subheader.TLabel").pack(anchor="w", pady=(10, 5))
        
        ttk.Button(content_frame, text="Find & Book First Available", command=self.smart_booking, style="Accent.TButton").pack(fill=tk.X, pady=5)
        ttk.Button(content_frame, text="Book Selected Slots", command=self.book_selected_slots).pack(fill=tk.X, pady=5)
        ttk.Button(content_frame, text="Delete a Booking", command=self.delete_booking, style="Danger.TButton").pack(fill=tk.X, pady=5)
        ttk.Button(content_frame, text="Clear Selection", command=self.clear_slot_selection).pack(fill=tk.X, pady=5)

        # --- Views ---
        ttk.Label(content_frame, text="Views", style="Subheader.TLabel").pack(anchor="w", pady=(20, 5))

        ttk.Button(content_frame, text="View All Bookings List", command=self.show_bookings_window).pack(fill=tk.X, pady=5)
        ttk.Button(content_frame, text="Show VEB Tree", command=self.show_veb_tree_window).pack(fill=tk.X, pady=5)

        # --- Availability Summary ---
        ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, pady=20)
        ttk.Label(content_frame, text="Availability Summary", style="Subheader.TLabel").pack(anchor="w", pady=(0, 10))

        self.summary_text = tk.StringVar()
        ttk.Label(content_frame, textvariable=self.summary_text, style="Body.TLabel", wraplength=250).pack(anchor="w")

    def create_main_content_widgets(self):
        # Header and Legend
        header_frame = ttk.Frame(self.main_content_frame, padding=(20, 10))
        header_frame.pack(fill=tk.X)
        
        ttk.Label(header_frame, text="Conference Room Status", font=self.fonts["header"], foreground=self.colors["text"]).pack(side=tk.LEFT)
        
        legend_frame = ttk.Frame(header_frame)
        legend_frame.pack(side=tk.RIGHT)
        
        for status, color in [("Available", self.colors["available"]), ("Booked", self.colors["booked"]), ("Selected", self.colors["selected"])]:
            tk.Frame(legend_frame, width=15, height=15, bg=color).pack(side=tk.LEFT, padx=(10, 2))
            ttk.Label(legend_frame, text=status, font=self.fonts["body"], foreground=self.colors["light_text"]).pack(side=tk.LEFT)

        # Scrollable Canvas for rooms
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
        self.rooms_canvas.bind_all("<MouseWheel>", self.on_mousewheel) # Binds to all widgets for scrolling
        
    def refresh_display(self):
        """Clears and redraws the main content and updates the summary."""
        # Update summary text
        self.summary_text.set(self.scheduler.availability_summary())
        
        # Clear existing room widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Re-draw room widgets
        for room in range(1, self.scheduler.rooms + 1):
            room_frame = ttk.Frame(self.scrollable_frame, padding=15, style="Sidebar.TFrame")
            room_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(room_frame, text=f"Conference Room {room}", font=self.fonts["subheader"], background='white').pack(anchor='w', pady=(0, 10))

            slots_frame = ttk.Frame(room_frame, style="Sidebar.TFrame")
            slots_frame.pack(fill=tk.X)
            
            slots_per_row = 10 # Adjust as needed
            for i in range(self.scheduler.slots):
                slot = i + 1
                index = (room - 1) * self.scheduler.slots + (slot - 1)
                
                # Determine state and color
                slot_info = (room, slot, index)
                is_booked = index in self.scheduler.booked
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
                
    # ---------- Action Methods (connected to original logic) ----------
    
    def smart_booking(self):
        result = self.scheduler.smart_booking()
        messagebox.showinfo("Smart Booking", result)
        self.refresh_display()

    def delete_booking(self):
        room = self.prompt_number(f"Enter Room Number (1–{self.scheduler.rooms}):", 1, self.scheduler.rooms)
        if not room: return
        slot = self.prompt_number(f"Enter Slot Number (1–{self.scheduler.slots}):", 1, self.scheduler.slots)
        if not slot: return
        
        result = self.scheduler.delete_booking(room, slot)
        messagebox.showinfo("Delete Booking", result)
        self.refresh_display()

    def book_selected_slots(self):
        if not self.selected_slots:
            messagebox.showwarning("No Selection", "Please select one or more available slots to book.")
            return

        booked_details = []
        for room, slot, index in self.selected_slots:
            result = self.scheduler.manual_booking(room, slot)
            if "✅" in result:
                booked_details.append(f"Room {room}, Slot {slot}")
        
        if booked_details:
            message = "Successfully booked:\n" + "\n".join(booked_details)
            messagebox.showinfo("Booking Successful", message)
        else:
            messagebox.showerror("Booking Failed", "Could not book the selected slots. They may have been taken.")
        
        self.selected_slots.clear()
        self.refresh_display()

    def clear_slot_selection(self):
        self.selected_slots.clear()
        self.refresh_display()
        
    def toggle_slot_selection(self, room, slot, index):
        slot_info = (room, slot, index)
        if slot_info in self.selected_slots:
            self.selected_slots.remove(slot_info)
        else:
            self.selected_slots.add(slot_info)
        self.refresh_display()

    # ---------- Popups & Dialogs (using original logic) ----------

    def show_bookings_window(self):
        result = self.scheduler.view_all_bookings()
        self.show_popup("All Bookings", result, width=400, height=400)

    def show_veb_tree_window(self):
        popup = tk.Toplevel(self.root)
        popup.title("VEB Tree Visualization")
        popup.geometry("800x600")
        
        canvas_frame = tk.Frame(popup)
        canvas_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Canvas + scrollbars for VEB visualization
        self.veb_canvas = tk.Canvas(canvas_frame, width=850, height=300, bg="white")
        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.veb_canvas.yview)
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.veb_canvas.xview)
        self.veb_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.veb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind mouse wheel for scrolling inside popup (cross-platform)
        def _veb_on_mousewheel(event):
            # Windows and macOS provide event.delta; Linux uses Button-4/5
            if hasattr(event, 'delta') and event.delta:
                self.veb_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            else:
                if event.num == 5:
                    self.veb_canvas.yview_scroll(1, 'units')
                elif event.num == 4:
                    self.veb_canvas.yview_scroll(-1, 'units')

        def _veb_on_shift_mousewheel(event):
            # Horizontal scroll when Shift is held
            if hasattr(event, 'delta') and event.delta:
                self.veb_canvas.xview_scroll(int(-1 * (event.delta / 120)), 'units')
            else:
                if event.num == 5:
                    self.veb_canvas.xview_scroll(1, 'units')
                elif event.num == 4:
                    self.veb_canvas.xview_scroll(-1, 'units')

        # Focus handling so mouse wheel works when hovering
        def _veb_on_enter(event):
            self.veb_canvas.focus_set()

        def _veb_on_leave(event):
            popup.focus_set()

        # Bindings (all inside the popup method)
        self.veb_canvas.bind('<MouseWheel>', _veb_on_mousewheel)
        self.veb_canvas.bind('<Button-4>', _veb_on_mousewheel)
        self.veb_canvas.bind('<Button-5>', _veb_on_mousewheel)
        # Horizontal (Shift + wheel)
        self.veb_canvas.bind('<Shift-MouseWheel>', _veb_on_shift_mousewheel)
        self.veb_canvas.bind('<Shift-Button-4>', _veb_on_shift_mousewheel)
        self.veb_canvas.bind('<Shift-Button-5>', _veb_on_shift_mousewheel)
        self.veb_canvas.bind('<Enter>', _veb_on_enter)
        self.veb_canvas.bind('<Leave>', _veb_on_leave)

        # Draw tree and ensure scrollregion is updated
        self.draw_veb_tree()
        popup.update_idletasks()
        bbox = self.veb_canvas.bbox('all')
        if bbox:
            padding = 40
            self.veb_canvas.configure(scrollregion=(bbox[0]-padding, bbox[1]-padding, bbox[2]+padding, bbox[3]+padding))

    # ---------- Utilities and Original Methods (Unchanged Logic) ----------

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

    def draw_veb_tree(self):
        self.veb_canvas.delete("all")
        if self.scheduler.veb.min is None:
            self.veb_canvas.create_text(425, 150, text="VEB Tree is empty", font=("Arial", 14), fill="red")
            self.veb_canvas.configure(scrollregion=self.veb_canvas.bbox("all"))
            return
        
        self._draw_node(self.scheduler.veb, 500, 50, 800)
        self.veb_canvas.update_idletasks()
        bbox = self.veb_canvas.bbox("all")
        if bbox:
            padding = 100
            scroll_region = (bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding)
            self.veb_canvas.configure(scrollregion=scroll_region)

    def _draw_node(self, node, x, y, x_offset):
        if node is None: return
        node_text = f"[{node.min},{node.max}]" if node.min is not None else "[]"
        node_radius = 30
        self.veb_canvas.create_oval(x-node_radius, y-node_radius, x+node_radius, y+node_radius, fill="#87CEEB", outline="#4682B4", width=2)
        self.veb_canvas.create_text(x, y, text=node_text, font=("Arial", 8, "bold"))

        if node.u > 2 and node.cluster:
            non_empty_clusters = [(i, c) for i, c in enumerate(node.cluster) if c is not None and c.min is not None]
            if non_empty_clusters:
                num_children = len(non_empty_clusters)
                child_spacing = max(120, x_offset / max(1, num_children - 1)) if num_children > 1 else 0
                total_width = child_spacing * (num_children - 1) if num_children > 1 else 0
                start_x = x - total_width / 2
                
                for idx, (cluster_idx, cluster) in enumerate(non_empty_clusters):
                    child_x = start_x + (idx * child_spacing)
                    child_y = y + 120
                    self.veb_canvas.create_line(x, y + node_radius, child_x, child_y - node_radius, fill="#4682B4", width=2)
                    self._draw_node(cluster, child_x, child_y, x_offset * 0.6)

    # ---------- Canvas Scrolling Handlers ----------
    def on_frame_configure(self, event):
        self.rooms_canvas.configure(scrollregion=self.rooms_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.rooms_canvas.itemconfig(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        # Universal mouse wheel scrolling for Windows/macOS/Linux
        if event.delta: # Windows/macOS
            self.rooms_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else: # Linux
            if event.num == 5:
                self.rooms_canvas.yview_scroll(1, "units")
            elif event.num == 4:
                self.rooms_canvas.yview_scroll(-1, "units")


# ======================= MAIN (Updated to use ttk) =======================
if __name__ == "__main__":
    root = tk.Tk()
    # Apply a theme to the root window for better consistency
    style = ttk.Style(root)
    style.theme_use('clam')
    
    gui = SchedulerGUI(root)
    root.mainloop()