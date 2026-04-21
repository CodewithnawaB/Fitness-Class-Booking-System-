"""
Fitness Class Booking System
University of Portsmouth London
Student: Shafiq ur Rehman  |  ID: 2516407  |  BSCS Year 1
Module: M34022 Programming — Assessment Item 4
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


# ─────────────────────────────────────────────
# OOP LAYER  (Task 1)
# ─────────────────────────────────────────────

class User:
    """Base class representing any system user."""

    def __init__(self, name: str, user_id: str):
        self._name = name          # encapsulated with underscore
        self._user_id = user_id

    @property
    def name(self):
        return self._name

    @property
    def user_id(self):
        return self._user_id

    def get_info(self) -> str:
        """Returns a formatted string of user information."""
        return f"User: {self._name} (ID: {self._user_id})"

    def __repr__(self):
        return self.get_info()


class Member(User):
    """
    Subclass of User representing a fitness centre member.
    Inherits name and user_id; adds membership_tier.
    """

    def __init__(self, name: str, user_id: str, membership_tier: str = "Standard"):
        super().__init__(name, user_id)
        self._membership_tier = membership_tier

    @property
    def membership_tier(self):
        return self._membership_tier

    def get_info(self) -> str:
        """Overrides base method to include membership tier."""
        return (f"Member: {self._name} (ID: {self._user_id}) "
                f"— Tier: {self._membership_tier}")

    def get_discount(self) -> float:
        """Members get a 10 % booking fee discount."""
        return 0.10


class Staff(User):
    """
    Subclass of User representing a staff member.
    Inherits name and user_id; adds role and employee_number.
    """

    def __init__(self, name: str, user_id: str, role: str, employee_number: str):
        super().__init__(name, user_id)
        self._role = role
        self._employee_number = employee_number

    @property
    def role(self):
        return self._role

    @property
    def employee_number(self):
        return self._employee_number

    def get_info(self) -> str:
        """Overrides base method to include role and employee number."""
        return (f"Staff: {self._name} (ID: {self._user_id}) "
                f"— Role: {self._role}, Emp#: {self._employee_number}")

    def can_manage_classes(self) -> bool:
        """Staff may add and remove classes."""
        return True


class FitnessClass:
    """Represents a single bookable fitness session."""

    def __init__(self, class_id: str, name: str, instructor: str,
                 capacity: int, class_type: str = "General"):
        self._class_id = class_id
        self._name = name
        self._instructor = instructor
        self._capacity = capacity
        self._class_type = class_type
        self._bookings: list[dict] = []   # list of booking dicts

    # ── properties ──────────────────────────────
    @property
    def class_id(self):
        return self._class_id

    @property
    def name(self):
        return self._name

    @property
    def instructor(self):
        return self._instructor

    @property
    def capacity(self):
        return self._capacity

    @property
    def class_type(self):
        return self._class_type

    @property
    def current_bookings(self) -> int:
        return len(self._bookings)

    @property
    def spaces_left(self) -> int:
        return self._capacity - self.current_bookings

    @property
    def is_full(self) -> bool:
        return self.current_bookings >= self._capacity

    # ── methods ──────────────────────────────────
    def add_booking(self, user: User) -> bool:
        """
        Books a user into this class.
        Returns True on success, False if full or already booked.
        """
        if self.is_full:
            return False
        # prevent duplicate booking for same user
        if any(b["user_id"] == user.user_id for b in self._bookings):
            return False
        self._bookings.append({
            "user_id":   user.user_id,
            "user_name": user.name,
            "user_type": type(user).__name__
        })
        return True

    def cancel_booking(self, user_id: str) -> bool:
        """Removes a booking by user_id. Returns True if found."""
        original = len(self._bookings)
        self._bookings = [b for b in self._bookings if b["user_id"] != user_id]
        return len(self._bookings) < original

    def get_bookings(self) -> list[dict]:
        return list(self._bookings)

    def to_dict(self) -> dict:
        return {
            "class_id":    self._class_id,
            "name":        self._name,
            "instructor":  self._instructor,
            "capacity":    self._capacity,
            "class_type":  self._class_type,
            "bookings":    self._bookings
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FitnessClass":
        obj = cls(
            data["class_id"], data["name"],
            data["instructor"], data["capacity"],
            data.get("class_type", "General")
        )
        obj._bookings = data.get("bookings", [])
        return obj

    def __repr__(self):
        return (f"FitnessClass({self._name!r}, "
                f"instructor={self._instructor!r}, "
                f"{self.current_bookings}/{self._capacity})")


class BookingSystem:
    """
    Top-level manager: stores FitnessClass objects and coordinates
    all operations including JSON persistence.
    """

    DATA_FILE = "fitness_data.json"

    def __init__(self):
        self._classes: dict[str, FitnessClass] = {}
        self._id_counter = 1
        self.load_data()

    # ── class management ────────────────────────
    def add_class(self, name: str, instructor: str,
                  capacity: int, class_type: str) -> FitnessClass:
        """Creates a new FitnessClass and stores it."""
        class_id = f"C{self._id_counter:03d}"
        self._id_counter += 1
        fc = FitnessClass(class_id, name, instructor, capacity, class_type)
        self._classes[class_id] = fc
        self.save_data()
        return fc

    def remove_class(self, class_id: str) -> bool:
        """Removes a class if it exists."""
        if class_id in self._classes:
            del self._classes[class_id]
            self.save_data()
            return True
        return False

    def get_all_classes(self) -> list[FitnessClass]:
        return list(self._classes.values())

    def get_class(self, class_id: str):
        return self._classes.get(class_id)

    # ── booking operations ───────────────────────
    def book_class(self, class_id: str, user: User) -> tuple[bool, str]:
        """
        Attempts to book a user into a class.
        Returns (success, message).
        """
        fc = self.get_class(class_id)
        if fc is None:
            return False, "Class not found."
        if fc.is_full:
            return False, f"'{fc.name}' is at full capacity ({fc.capacity})."
        if any(b["user_id"] == user.user_id for b in fc.get_bookings()):
            return False, f"{user.name} is already booked into '{fc.name}'."
        result = fc.add_booking(user)
        if result:
            self.save_data()
            return True, f"Booking confirmed: {user.name} → {fc.name}."
        return False, "Booking failed for an unknown reason."

    def cancel_booking(self, class_id: str, user_id: str) -> tuple[bool, str]:
        """Cancels a booking by class_id and user_id."""
        fc = self.get_class(class_id)
        if fc is None:
            return False, "Class not found."
        result = fc.cancel_booking(user_id)
        if result:
            self.save_data()
            return True, "Booking cancelled successfully."
        return False, "No booking found for this user in that class."

    # ── persistence ──────────────────────────────
    def save_data(self):
        """Serialises all classes to JSON."""
        payload = {
            "id_counter": self._id_counter,
            "classes": [fc.to_dict() for fc in self._classes.values()]
        }
        with open(self.DATA_FILE, "w") as f:
            json.dump(payload, f, indent=2)

    def load_data(self):
        """Loads data from JSON if the file exists."""
        if not os.path.exists(self.DATA_FILE):
            self._seed_demo_data()
            return
        try:
            with open(self.DATA_FILE) as f:
                payload = json.load(f)
            self._id_counter = payload.get("id_counter", 1)
            for d in payload.get("classes", []):
                fc = FitnessClass.from_dict(d)
                self._classes[fc.class_id] = fc
        except (json.JSONDecodeError, KeyError):
            self._seed_demo_data()

    def _seed_demo_data(self):
        """Adds sample classes so the application is not empty on first run."""
        samples = [
            ("Yoga Flow",    "Sarah Johnson", 15, "Yoga"),
            ("Spin Cycle",   "Mark Davis",    20, "Spin"),
            ("HIIT Blast",   "Emma Clarke",   12, "HIIT"),
            ("Pilates Core", "Lena Park",     10, "Pilates"),
        ]
        for name, inst, cap, ctype in samples:
            self.add_class(name, inst, cap, ctype)


# ─────────────────────────────────────────────
# GUI LAYER  (Task 2)
# ─────────────────────────────────────────────

ACCENT = "#2d5a8e"
BG = "#f4f5f7"


class FitnessApp(tk.Tk):
    """Root window and controller for the GUI application."""

    def __init__(self):
        super().__init__()
        self.title("Fitness Class Booking System")
        self.geometry("1100x680")
        self.minsize(900, 580)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.system = BookingSystem()
        self._build_ui()
        self.refresh_all()

    # ── top-level layout ────────────────────────
    def _build_ui(self):
        self._build_title_bar()
        self._build_notebook()
        self._build_status_bar()

    def _build_title_bar(self):
        bar = tk.Frame(self, bg=ACCENT, height=48)
        bar.pack(fill=tk.X)
        tk.Label(bar, text="  Fitness Class Booking System",
                 bg=ACCENT, fg="white",
                 font=("Helvetica", 14, "bold")).pack(side=tk.LEFT, pady=10)
        tk.Label(bar, text="University Fitness Centre",
                 bg=ACCENT, fg="#b0c8e8",
                 font=("Helvetica", 10)).pack(side=tk.RIGHT, padx=16)

    def _build_notebook(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook",        background=BG, borderwidth=0)
        style.configure("TNotebook.Tab",    padding=[14, 8], font=("Helvetica", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", "white"), ("", BG)],
                  foreground=[("selected", ACCENT),  ("", "#555")])

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.tab_classes  = tk.Frame(self.nb, bg="white")
        self.tab_book     = tk.Frame(self.nb, bg="white")
        self.tab_manage   = tk.Frame(self.nb, bg="white")
        self.tab_add      = tk.Frame(self.nb, bg="white")

        self.nb.add(self.tab_classes, text=" Classes ")
        self.nb.add(self.tab_book,    text=" Book a Class ")
        self.nb.add(self.tab_manage,  text=" Manage Bookings ")
        self.nb.add(self.tab_add,     text=" Add / Remove Class ")

        self._build_tab_classes()
        self._build_tab_book()
        self._build_tab_manage()
        self._build_tab_add()

        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.refresh_all())

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Ready.")
        bar = tk.Label(self, textvariable=self.status_var,
                       bg="#dde3ee", fg="#444",
                       anchor=tk.W, padx=10, font=("Helvetica", 9))
        bar.pack(fill=tk.X, side=tk.BOTTOM)

    def set_status(self, msg: str):
        self.status_var.set(msg)

    # ── Tab: Classes ────────────────────────────
    def _build_tab_classes(self):
        f = self.tab_classes

        hdr = tk.Frame(f, bg="white")
        hdr.pack(fill=tk.X, padx=20, pady=(16, 8))
        tk.Label(hdr, text="All fitness classes", bg="white",
                 font=("Helvetica", 13, "bold"), fg="#222").pack(side=tk.LEFT)
        tk.Button(hdr, text="Refresh", command=self.refresh_all,
                  bg=ACCENT, fg="white", relief=tk.FLAT,
                  padx=10, cursor="hand2").pack(side=tk.RIGHT)

        cols = ("Name", "Instructor", "Type", "Capacity", "Booked", "Spaces Left", "Status")
        self.tree_classes = ttk.Treeview(f, columns=cols, show="headings",
                                         selectmode="browse", height=16)
        widths = (180, 160, 100, 90, 80, 100, 100)
        for col, w in zip(cols, widths):
            self.tree_classes.heading(col, text=col)
            self.tree_classes.column(col, width=w, anchor=tk.CENTER)

        scroll = ttk.Scrollbar(f, orient=tk.VERTICAL,
                               command=self.tree_classes.yview)
        self.tree_classes.configure(yscrollcommand=scroll.set)
        self.tree_classes.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 4))
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_classes.tag_configure("full",    background="#fff0f0", foreground="#a00")
        self.tree_classes.tag_configure("partial", background="#fffbe6", foreground="#7a5000")
        self.tree_classes.tag_configure("open",    background="#f0fff4", foreground="#1a6b3a")

        bf = tk.Frame(f, bg="white")
        bf.pack(fill=tk.X, padx=20, pady=(4, 16))
        tk.Button(bf, text="Book selected class",
                  command=self._book_selected_from_list,
                  bg=ACCENT, fg="white", relief=tk.FLAT,
                  padx=12, cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(bf, text="View bookings for selected",
                  command=self._view_selected_bookings,
                  bg="#555", fg="white", relief=tk.FLAT,
                  padx=12, cursor="hand2").pack(side=tk.LEFT)

    def _populate_classes_tree(self):
        self.tree_classes.delete(*self.tree_classes.get_children())
        for fc in self.system.get_all_classes():
            ratio = fc.current_bookings / fc.capacity if fc.capacity else 0
            if ratio >= 1:
                status, tag = "Full", "full"
            elif ratio >= 0.7:
                status, tag = "Almost full", "partial"
            else:
                status, tag = "Available", "open"
            self.tree_classes.insert("", tk.END, iid=fc.class_id,
                values=(fc.name, fc.instructor, fc.class_type,
                        fc.capacity, fc.current_bookings,
                        fc.spaces_left, status),
                tags=(tag,))

    def _book_selected_from_list(self):
        sel = self.tree_classes.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a class first.")
            return
        self.nb.select(self.tab_book)
        self.book_class_var.set(sel[0])

    def _view_selected_bookings(self):
        sel = self.tree_classes.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a class first.")
            return
        self.nb.select(self.tab_manage)
        self.manage_filter_var.set(sel[0])
        self._populate_manage_tree()

    # ── Tab: Book a Class ───────────────────────
    def _build_tab_book(self):
        f = self.tab_book
        pad = {"padx": 20, "pady": 6}

        tk.Label(f, text="Book a fitness class", bg="white",
                 font=("Helvetica", 13, "bold"), fg="#222").pack(anchor=tk.W, **pad)

        form = tk.LabelFrame(f, text="Member / Student details",
                             bg="white", fg="#444",
                             font=("Helvetica", 10), padx=16, pady=12)
        form.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(form, text="Full name *", bg="white",
                 font=("Helvetica", 9)).grid(row=0, column=0, sticky=tk.W, pady=4)
        self.book_name_var = tk.StringVar()
        tk.Entry(form, textvariable=self.book_name_var, width=30,
                 font=("Helvetica", 10)).grid(row=0, column=1, sticky=tk.W, padx=12)

        tk.Label(form, text="User ID *", bg="white",
                 font=("Helvetica", 9)).grid(row=1, column=0, sticky=tk.W, pady=4)
        self.book_id_var = tk.StringVar()
        tk.Entry(form, textvariable=self.book_id_var, width=20,
                 font=("Helvetica", 10)).grid(row=1, column=1, sticky=tk.W, padx=12)

        tk.Label(form, text="User type *", bg="white",
                 font=("Helvetica", 9)).grid(row=2, column=0, sticky=tk.W, pady=4)
        self.book_type_var = tk.StringVar(value="Member")
        ttk.Combobox(form, textvariable=self.book_type_var,
                     values=["Member", "Student"],
                     state="readonly", width=18).grid(row=2, column=1,
                                                       sticky=tk.W, padx=12)

        tk.Label(form, text="Membership tier", bg="white",
                 font=("Helvetica", 9)).grid(row=3, column=0, sticky=tk.W, pady=4)
        self.book_tier_var = tk.StringVar(value="Standard")
        ttk.Combobox(form, textvariable=self.book_tier_var,
                     values=["Standard", "Premium", "Student"],
                     state="readonly", width=18).grid(row=3, column=1,
                                                       sticky=tk.W, padx=12)

        tk.Label(form, text="Select class *", bg="white",
                 font=("Helvetica", 9)).grid(row=4, column=0, sticky=tk.W, pady=4)
        self.book_class_var = tk.StringVar()
        self.book_class_cb = ttk.Combobox(form, textvariable=self.book_class_var,
                                           state="readonly", width=35)
        self.book_class_cb.grid(row=4, column=1, sticky=tk.W, padx=12)

        tk.Button(f, text="Confirm booking",
                  command=self._do_book,
                  bg=ACCENT, fg="white", relief=tk.FLAT,
                  font=("Helvetica", 11), padx=18, pady=6,
                  cursor="hand2").pack(anchor=tk.W, padx=20, pady=8)

    def _populate_book_cb(self):
        classes = self.system.get_all_classes()
        values = [f"{fc.class_id} — {fc.name} ({fc.current_bookings}/{fc.capacity})"
                  for fc in classes]
        ids    = [fc.class_id for fc in classes]
        self.book_class_cb["values"] = values
        self._book_class_ids = ids
        if ids and self.book_class_var.get() not in ids:
            self.book_class_cb.current(0)
            self.book_class_var.set(ids[0])

    def _do_book(self):
        name  = self.book_name_var.get().strip()
        uid   = self.book_id_var.get().strip()
        utype = self.book_type_var.get()

        if not name:
            messagebox.showerror("Validation", "Full name is required.")
            return
        if not uid:
            messagebox.showerror("Validation", "User ID is required.")
            return

        if utype == "Member":
            user = Member(name, uid, self.book_tier_var.get())
        else:
            user = Member(name, uid, "Student")

        idx = self.book_class_cb.current()
        if idx < 0 or not hasattr(self, "_book_class_ids"):
            messagebox.showerror("Validation", "Please select a class.")
            return
        class_id = self._book_class_ids[idx]

        ok, msg = self.system.book_class(class_id, user)
        if ok:
            messagebox.showinfo("Booking confirmed", msg)
            self.set_status(msg)
            self.book_name_var.set("")
            self.book_id_var.set("")
        else:
            messagebox.showerror("Booking failed", msg)
            self.set_status(f"Failed: {msg}")
        self.refresh_all()

    # ── Tab: Manage Bookings ─────────────────────
    def _build_tab_manage(self):
        f = self.tab_manage

        tk.Label(f, text="Manage bookings", bg="white",
                 font=("Helvetica", 13, "bold"), fg="#222").pack(anchor=tk.W,
                                                                   padx=20, pady=(16, 4))

        flt = tk.Frame(f, bg="white")
        flt.pack(fill=tk.X, padx=20, pady=(0, 8))
        tk.Label(flt, text="Filter by class:", bg="white",
                 font=("Helvetica", 9)).pack(side=tk.LEFT)
        self.manage_filter_var = tk.StringVar(value="ALL")
        self.manage_cb = ttk.Combobox(flt, textvariable=self.manage_filter_var,
                                       state="readonly", width=35)
        self.manage_cb.pack(side=tk.LEFT, padx=10)
        tk.Button(flt, text="Apply filter",
                  command=self._populate_manage_tree,
                  bg="#555", fg="white", relief=tk.FLAT,
                  padx=8, cursor="hand2").pack(side=tk.LEFT)

        cols = ("Class", "Member name", "User ID", "Type")
        self.tree_manage = ttk.Treeview(f, columns=cols, show="headings",
                                        selectmode="browse", height=16)
        for col in cols:
            self.tree_manage.heading(col, text=col)
            self.tree_manage.column(col, width=200, anchor=tk.W)

        scroll = ttk.Scrollbar(f, orient=tk.VERTICAL,
                                command=self.tree_manage.yview)
        self.tree_manage.configure(yscrollcommand=scroll.set)
        self.tree_manage.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 4))
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(f, text="Cancel selected booking",
                  command=self._do_cancel,
                  bg="#c0392b", fg="white", relief=tk.FLAT,
                  padx=12, pady=5, cursor="hand2").pack(anchor=tk.W,
                                                          padx=20, pady=(4, 16))

    def _populate_manage_cb(self):
        classes = self.system.get_all_classes()
        values = ["ALL — show all bookings"] + [
            f"{fc.class_id} — {fc.name}" for fc in classes]
        ids = ["ALL"] + [fc.class_id for fc in classes]
        self.manage_cb["values"] = values
        self._manage_class_ids = ids

    def _populate_manage_tree(self):
        self.tree_manage.delete(*self.tree_manage.get_children())
        selected = self.manage_filter_var.get()
        class_id = selected if selected in getattr(self, "_manage_class_ids", []) else "ALL"

        for fc in self.system.get_all_classes():
            if class_id != "ALL" and fc.class_id != class_id:
                continue
            for b in fc.get_bookings():
                self.tree_manage.insert("", tk.END,
                    iid=f"{fc.class_id}::{b['user_id']}",
                    values=(fc.name, b["user_name"], b["user_id"], b["user_type"]))

    def _do_cancel(self):
        sel = self.tree_manage.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a booking to cancel.")
            return
        iid = sel[0]
        class_id, user_id = iid.split("::", 1)
        row = self.tree_manage.item(iid)["values"]
        member_name = row[1]

        if not messagebox.askyesno("Confirm cancellation",
                                   f"Cancel booking for {member_name}?"):
            return
        ok, msg = self.system.cancel_booking(class_id, user_id)
        if ok:
            messagebox.showinfo("Cancelled", msg)
            self.set_status(msg)
        else:
            messagebox.showerror("Error", msg)
        self.refresh_all()

    # ── Tab: Add / Remove Class ──────────────────
    def _build_tab_add(self):
        f = self.tab_add

        add_frame = tk.LabelFrame(f, text="Add new class",
                                   bg="white", fg="#444",
                                   font=("Helvetica", 10), padx=16, pady=12)
        add_frame.pack(fill=tk.X, padx=20, pady=(16, 10))

        labels = ["Class name *", "Instructor name *",
                  "Maximum capacity *", "Class type"]
        self.add_vars = [tk.StringVar() for _ in labels]
        self.add_vars[3].set("Yoga")

        for i, (lbl, var) in enumerate(zip(labels, self.add_vars)):
            tk.Label(add_frame, text=lbl, bg="white",
                     font=("Helvetica", 9)).grid(row=i, column=0,
                                                   sticky=tk.W, pady=4)
            if i == 3:
                ttk.Combobox(add_frame, textvariable=var,
                             values=["Yoga","Pilates","Spin","HIIT",
                                     "Zumba","Boxing","Other"],
                             state="readonly", width=22).grid(row=i, column=1,
                                                               sticky=tk.W, padx=12)
            else:
                tk.Entry(add_frame, textvariable=var, width=30,
                         font=("Helvetica", 10)).grid(row=i, column=1,
                                                       sticky=tk.W, padx=12)

        tk.Button(f, text="Add class",
                  command=self._do_add_class,
                  bg=ACCENT, fg="white", relief=tk.FLAT,
                  font=("Helvetica", 11), padx=14, pady=5,
                  cursor="hand2").pack(anchor=tk.W, padx=20, pady=(0, 16))

        rm_frame = tk.LabelFrame(f, text="Remove a class",
                                  bg="white", fg="#444",
                                  font=("Helvetica", 10), padx=16, pady=12)
        rm_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(rm_frame, text="Select class:", bg="white",
                 font=("Helvetica", 9)).grid(row=0, column=0, sticky=tk.W, pady=4)
        self.remove_class_var = tk.StringVar()
        self.remove_cb = ttk.Combobox(rm_frame, textvariable=self.remove_class_var,
                                       state="readonly", width=35)
        self.remove_cb.grid(row=0, column=1, sticky=tk.W, padx=12)

        tk.Button(f, text="Remove class",
                  command=self._do_remove_class,
                  bg="#c0392b", fg="white", relief=tk.FLAT,
                  font=("Helvetica", 11), padx=14, pady=5,
                  cursor="hand2").pack(anchor=tk.W, padx=20, pady=(0, 16))

    def _populate_remove_cb(self):
        classes = self.system.get_all_classes()
        values = [f"{fc.class_id} — {fc.name}" for fc in classes]
        ids    = [fc.class_id for fc in classes]
        self.remove_cb["values"] = values
        self._remove_class_ids = ids
        if ids:
            self.remove_cb.current(0)

    def _do_add_class(self):
        name       = self.add_vars[0].get().strip()
        instructor = self.add_vars[1].get().strip()
        cap_str    = self.add_vars[2].get().strip()
        ctype      = self.add_vars[3].get()

        if not name:
            messagebox.showerror("Validation", "Class name is required.")
            return
        if not instructor:
            messagebox.showerror("Validation", "Instructor name is required.")
            return
        try:
            cap = int(cap_str)
            if cap < 1 or cap > 200:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation",
                                 "Capacity must be a whole number between 1 and 200.")
            return

        fc = self.system.add_class(name, instructor, cap, ctype)
        msg = f"Class '{fc.name}' added (ID: {fc.class_id})."
        messagebox.showinfo("Class added", msg)
        self.set_status(msg)
        for v in self.add_vars[:3]:
            v.set("")
        self.refresh_all()

    def _do_remove_class(self):
        idx = self.remove_cb.current()
        if idx < 0 or not hasattr(self, "_remove_class_ids"):
            messagebox.showwarning("No selection", "Please select a class to remove.")
            return
        class_id = self._remove_class_ids[idx]
        fc = self.system.get_class(class_id)
        if fc is None:
            return
        n = fc.current_bookings
        if not messagebox.askyesno("Confirm removal",
                                   f"Remove '{fc.name}'?\n"
                                   f"This will cancel {n} existing booking(s)."):
            return
        self.system.remove_class(class_id)
        msg = f"Class '{fc.name}' removed."
        messagebox.showinfo("Removed", msg)
        self.set_status(msg)
        self.refresh_all()

    # ── Refresh all views ────────────────────────
    def refresh_all(self):
        self._populate_classes_tree()
        self._populate_book_cb()
        self._populate_manage_cb()
        self._populate_manage_tree()
        self._populate_remove_cb()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = FitnessApp()
    app.mainloop()
