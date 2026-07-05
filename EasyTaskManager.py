import tkinter as tk
from tkinter import ttk


class EasyTaskManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Easy Task Manager")
        self.geometry("560x700")
        self.configure(bg="#1c1c1e")
        self.minsize(480, 520)

        self.deleted_visible = False
        self.deleted_tasks = []

        self._build_header()
        self._build_task_area()
        self._build_deleted_panel()

        self._create_task()

    def _build_header(self):
        header = tk.Frame(self, bg="#141418", height=52)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(header, text="Easy Task Manager", fg="white", bg="#141418",
                         font=("Segoe UI", 14, "bold"))
        title.pack(side=tk.LEFT, padx=16)

        button_frame = tk.Frame(header, bg="#141418")
        button_frame.pack(side=tk.RIGHT, padx=12)

        add_btn = ttk.Button(button_frame, text="Add Task", command=self._create_task)
        add_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.toggle_deleted_btn = ttk.Button(button_frame, text="Show Deleted", command=self._toggle_deleted_panel)
        self.toggle_deleted_btn.pack(side=tk.LEFT)

    def _build_task_area(self):
        task_area = tk.Frame(self, bg="#1c1c1e")
        task_area.pack(fill=tk.BOTH, expand=True)

        self.task_canvas = tk.Canvas(task_area, bg="#1c1c1e", highlightthickness=0)
        self.task_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(task_area, orient=tk.VERTICAL, command=self.task_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_canvas.configure(yscrollcommand=scrollbar.set)

        self.task_container = tk.Frame(self.task_canvas, bg="#1c1c1e")
        self.task_canvas.create_window((0, 0), window=self.task_container, anchor="nw")
        self.task_container.bind("<Configure>", self._update_scrollregion)

        self.task_canvas.bind("<Button-1>", lambda event: self._create_task())

    def _build_deleted_panel(self):
        self.deleted_panel = tk.Frame(self, bg="#121214", height=180)
        self.deleted_panel.pack(side=tk.BOTTOM, fill=tk.X)
        self.deleted_panel.pack_forget()

        header = tk.Frame(self.deleted_panel, bg="#121214")
        header.pack(fill=tk.X, padx=12, pady=8)

        label = tk.Label(header, text="Deleted Tasks", fg="white", bg="#121214",
                         font=("Segoe UI", 11, "bold"))
        label.pack(side=tk.LEFT)

        clear_btn = ttk.Button(header, text="Clear Deleted", command=self._clear_deleted)
        clear_btn.pack(side=tk.RIGHT)

        self.deleted_list = tk.Frame(self.deleted_panel, bg="#121214")
        self.deleted_list.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

    def _update_scrollregion(self, event=None):
        self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all"))

    def _create_task(self, text=""):
        if self.task_container.winfo_children():
            last_task = self.task_container.winfo_children()[-1]
            if isinstance(last_task, TaskRow) and not last_task.is_deleted and last_task.get_text().strip() == "":
                last_task.focus()
                return

        task = TaskRow(self.task_container, on_enter=self._create_task, on_delete=self._move_to_deleted)
        task.pack(fill=tk.X, pady=6, padx=12)
        task.set_text(text)
        task.focus()
        self.after(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        self.task_canvas.update_idletasks()
        self.task_canvas.yview_moveto(1.0)

    def _move_to_deleted(self, task):
        if task.is_deleted:
            return

        task.mark_deleted()
        task.pack_forget()
        task.pack(in_=self.deleted_list, fill=tk.X, pady=4)
        self.deleted_tasks.append(task)

        if not self.deleted_visible:
            self._toggle_deleted_panel()

    def _toggle_deleted_panel(self):
        if self.deleted_visible:
            self.deleted_panel.pack_forget()
            self.deleted_visible = False
            self.toggle_deleted_btn.configure(text="Show Deleted")
        else:
            self.deleted_panel.pack(side=tk.BOTTOM, fill=tk.X)
            self.deleted_visible = True
            self.toggle_deleted_btn.configure(text="Hide Deleted")

    def _clear_deleted(self):
        for task in self.deleted_tasks:
            task.destroy()
        self.deleted_tasks.clear()

        if self.deleted_visible:
            self._toggle_deleted_panel()


class TaskRow(tk.Frame):
    def __init__(self, parent, on_enter, on_delete):
        super().__init__(parent, bg="#2c2c2e", height=58)
        self.on_enter_callback = on_enter
        self.on_delete_callback = on_delete
        self.is_deleted = False
        self._build_widgets()
        self.pack_propagate(False)

    def _build_widgets(self):
        self.priority_label = tk.Label(self, text="○", fg="gray", bg="#2c2c2e",
                                       font=("Segoe UI", 14), cursor="hand2")
        self.priority_label.pack(side=tk.LEFT, padx=(8, 4))
        self.priority_label.bind("<Button-1>", lambda e: self._cycle_priority())

        self.text = tk.Text(self, bg="#2c2c2e", fg="white", bd=0, height=1,
                             font=("Segoe UI", 11), wrap=tk.WORD, insertbackground="white")
        self.text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=8)
        self.text.bind("<Return>", self._handle_enter)
        self.text.bind("<Shift-Return>", self._insert_newline)
        self.text.bind("<KeyRelease>", self._adjust_height)

        self.complete_btn = self._create_action_button("✔", "#30d158")
        self.complete_btn.pack(side=tk.RIGHT, padx=4)
        self.complete_btn.bind("<Button-1>", lambda e: self._set_state("completed"))

        self.pending_btn = self._create_action_button("❓", "#ff9f0a")
        self.pending_btn.pack(side=tk.RIGHT, padx=4)
        self.pending_btn.bind("<Button-1>", lambda e: self._set_state("pending"))

        self.delete_btn = self._create_action_button("✖", "#ff453a")
        self.delete_btn.pack(side=tk.RIGHT, padx=4)
        self.delete_btn.bind("<Button-1>", lambda e: self._delete())

    def _create_action_button(self, text, hover_color):
        btn = tk.Label(self, text=text, fg="gray", bg="#2c2c2e",
                       font=("Segoe UI", 10, "bold"), cursor="hand2")
        btn.bind("<Enter>", lambda e: btn.config(fg=hover_color))
        btn.bind("<Leave>", lambda e: btn.config(fg="gray"))
        return btn

    def _cycle_priority(self):
        priorities = [("○", "gray"), ("●", "tomato"), ("●", "deepskyblue"), ("●", "mediumseagreen")]
        current = (self.priority_label.cget("text"), self.priority_label.cget("fg"))
        next_index = (priorities.index(current) + 1) % len(priorities) if current in priorities else 0
        symbol, color = priorities[next_index]
        self.priority_label.configure(text=symbol, fg=color)

    def _handle_enter(self, event=None):
        if event and event.state & 0x0001:
            return None
        self.on_enter_callback()
        return "break"

    def _insert_newline(self, event=None):
        self.text.insert(tk.INSERT, "\n")
        return "break"

    def _set_state(self, state):
        if self.is_deleted:
            return
        if state == "completed":
            self.configure(bg="#143e1e")
            self.text.configure(bg="#143e1e", fg="#b3b3b3")
        elif state == "pending":
            self.configure(bg="#50320a")
            self.text.configure(bg="#50320a", fg="white")

    def _delete(self):
        if self.is_deleted:
            self.destroy()
            return
        self.on_delete_callback(self)

    def mark_deleted(self):
        self.is_deleted = True
        self.priority_label.configure(state=tk.DISABLED)
        self.configure(bg="#1b1b1d")
        self.text.configure(bg="#1b1b1d", fg="#888888")

    def _adjust_height(self, event=None):
        lines = int(self.text.index("end-1c").split('.')[0])
        self.text.configure(height=max(1, min(lines, 6)))

    def get_text(self):
        return self.text.get("1.0", "end-1c")

    def set_text(self, value):
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, value)
        self._adjust_height()

    def focus(self):
        self.text.focus_set()
        self.text.mark_set(tk.INSERT, tk.END)


if __name__ == "__main__":
    app = EasyTaskManager()
    app.mainloop()