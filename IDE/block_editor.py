from __future__ import annotations

import json
import tkinter as tk
from tkinter import BOTH, END, LEFT, RIGHT, X, font as tkfont, ttk

from parser.nodes import (
    BinaryOpNode,
    FunctionCallNode,
    FunctionNode,
    IdentifierNode,
    IfNode,
    InputNode,
    LiteralNode,
    PrintNode,
    ProgramNode,
    RepeatNode,
    ReturnNode,
    UnaryOpNode,
    VarAssignNode,
)


class AstSourceGenerator:
    def generate(self, program: ProgramNode) -> str:
        lines = self._statements(program.statements, 0)
        return "\n".join(lines) + ("\n" if lines else "")

    def _statements(self, statements: list, indent: int) -> list[str]:
        lines = []
        for statement in statements:
            lines.extend(self._statement(statement, indent))
        return lines

    def _statement(self, node, indent: int) -> list[str]:
        prefix = "    " * indent
        if isinstance(node, PrintNode):
            return [f"{prefix}출력({self._expression(node.value)})"]
        if isinstance(node, VarAssignNode):
            keyword = "변수 " if node.declare else ""
            return [f"{prefix}{keyword}{node.name} = {self._expression(node.value)}"]
        if isinstance(node, InputNode):
            values = [node.name]
            if node.prompt is not None:
                values.append(self._expression(node.prompt))
            return [f"{prefix}입력({', '.join(values)})"]
        if isinstance(node, FunctionCallNode):
            args = ", ".join(self._expression(value) for value in node.arguments)
            return [f"{prefix}{node.name}({args})"]
        if isinstance(node, IfNode):
            lines = [f"{prefix}만약 {self._expression(node.condition)}:"]
            lines.extend(self._body(node.then_body, indent + 1))
            for condition, body in node.elif_branches or []:
                lines.append(f"{prefix}아니고만약 {self._expression(condition)}:")
                lines.extend(self._body(body, indent + 1))
            if node.else_body:
                lines.append(f"{prefix}아니면:")
                lines.extend(self._body(node.else_body, indent + 1))
            return lines
        if isinstance(node, RepeatNode):
            return [f"{prefix}반복 {self._expression(node.count)}:", *self._body(node.body, indent + 1)]
        if isinstance(node, FunctionNode):
            parameters = ", ".join(node.parameters)
            return [f"{prefix}함수 {node.name}({parameters}):", *self._body(node.body, indent + 1)]
        if isinstance(node, ReturnNode):
            return [f"{prefix}반환 {self._expression(node.value)}"]
        raise ValueError(f"지원하지 않는 AST 노드입니다: {type(node).__name__}")

    def _body(self, statements: list, indent: int) -> list[str]:
        return self._statements(statements, indent) or ["    " * indent + "출력(\"\")"]

    def _expression(self, node) -> str:
        if isinstance(node, LiteralNode):
            if isinstance(node.value, str):
                return json.dumps(node.value, ensure_ascii=False)
            if isinstance(node.value, bool):
                return "참" if node.value else "거짓"
            return str(node.value)
        if isinstance(node, IdentifierNode):
            return node.name
        if isinstance(node, InputNode):
            values = [node.name]
            if node.prompt is not None:
                values.append(self._expression(node.prompt))
            return f"입력({', '.join(values)})"
        if isinstance(node, FunctionCallNode):
            args = ", ".join(self._expression(value) for value in node.arguments)
            return f"{node.name}({args})"
        if isinstance(node, UnaryOpNode):
            return f"{node.operator} {self._expression(node.operand)}"
        if isinstance(node, BinaryOpNode):
            return f"{self._expression(node.left)} {node.operator} {self._expression(node.right)}"
        raise ValueError(f"지원하지 않는 표현식 노드입니다: {type(node).__name__}")


class BlockEditor(ttk.Frame):
    PALETTE = (
        ("기본", (("출력", "print"), ("입력", "input"))),
        ("변수", (("변수 만들기", "declare"), ("변수에 값 저장", "assign"))),
        ("조건", (("만약", "if"), ("아니면", "else"))),
        ("반복", (("반복", "repeat"),)),
        ("함수", (("함수 정의", "function"), ("함수 호출", "call"))),
    )
    COLORS = {
        "print": "#4d9cff",
        "input": "#35b88a",
        "declare": "#ff9f1c",
        "assign": "#ff9f1c",
        "identifier": "#ff9f1c",
        "if": "#ff6f91",
        "else": "#ff6f91",
        "repeat": "#7c65d1",
        "function": "#d97745",
        "call": "#d97745",
        "expression": "#31a6a6",
    }
    CATEGORY_COLORS = {
        "기본": "#4d9cff",
        "변수": "#ff9f1c",
        "조건": "#ff6f91",
        "반복": "#7c65d1",
        "연산": "#31a6a6",
        "함수": "#d97745",
    }
    DESCRIPTIONS = {
        "print": "값이나 문장을 콘솔에 출력합니다.",
        "input": "사용자 입력을 변수에 저장합니다.",
        "declare": "새 변수를 만들고 처음 값을 저장합니다.",
        "assign": "이미 만든 변수의 값을 바꿉니다.",
        "if": "조건이 참일 때 내부 블록을 실행합니다.",
        "repeat": "내부 블록을 지정한 횟수만큼 반복합니다.",
        "function": "여러 명령을 하나의 함수로 묶습니다.",
        "call": "함수를 호출하여 내부 명령을 실행합니다.",
        "expression": "값을 계산하거나 논리 조건을 만듭니다.",
    }

    def __init__(self, master, app, source: str):
        super().__init__(master)
        self.app = app
        self.program = ProgramNode([])
        self.drag_kind = None
        self.drag_widget = None
        self.positions = {}
        self.block_widgets = {}
        self.connector_widgets = []
        self.preview = None
        self.preview_index = None
        self.preview_position = None
        self.tooltip = None
        self.drag_moved = False
        self.drag_appearance = []
        self.category_buttons = {}
        self.palette_buttons = []
        self.active_category = None
        self._build()
        self.load_source(source, strict=False)

    def _build(self):
        p = self.app.palette
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

        self.category_bar = tk.Frame(self, bg=p["panel"], padx=10, pady=12, width=104)
        self.category_bar.grid(row=0, column=0, sticky="ns")
        self.category_bar.grid_propagate(False)
        self.category_heading = tk.Label(
            self.category_bar,
            text="블록",
            bg=p["panel"],
            fg=p["fg"],
            font=(self.app.settings.font_family, 12, "bold"),
            anchor="w",
        )
        self.category_heading.pack(fill=X, pady=(0, 10))
        for category, items in self.PALETTE:
            button = tk.Button(
                self.category_bar,
                text=category,
                anchor="w",
                relief="flat",
                bd=0,
                padx=10,
                pady=8,
                cursor="hand2",
                command=lambda name=category, values=items: self._open_category(name, values),
            )
            button.pack(fill=X, pady=3)
            self.category_buttons[category] = button

        self.category_panel = tk.Frame(self, bg=p["panel2"], padx=12, pady=12, width=210)
        self.category_panel.grid(row=0, column=1, sticky="ns")
        self.category_panel.grid_propagate(False)
        self.category_title = tk.Label(
            self.category_panel,
            text="블록을 고르세요",
            bg=p["panel2"],
            fg=p["fg"],
            font=(self.app.settings.font_family, 11, "bold"),
            anchor="w",
        )
        self.category_title.pack(fill=X, pady=(0, 4))
        self.category_hint = tk.Label(
            self.category_panel,
            text="블록을 작업 영역으로 끌어오세요.",
            bg=p["panel2"],
            fg=p["muted"],
            anchor="w",
            justify="left",
            wraplength=180,
        )
        self.category_hint.pack(fill=X, pady=(0, 12))

        work = tk.Frame(self, bg=p["editor"], padx=14, pady=12)
        self.work_frame = work
        work.grid(row=0, column=2, sticky="nsew")
        work.columnconfigure(0, weight=1)
        work.rowconfigure(1, weight=1)

        self.workspace_header = tk.Frame(work, bg=p["editor"])
        self.workspace_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.workspace_header.columnconfigure(0, weight=1)
        self.workspace_title = tk.Label(
            self.workspace_header,
            text="작업 영역",
            bg=p["editor"],
            fg=p["fg"],
            font=(self.app.settings.font_family, 13, "bold"),
            anchor="w",
        )
        self.workspace_title.grid(row=0, column=0, sticky="w")
        self.workspace_count = tk.Label(
            self.workspace_header,
            text="0개 블록",
            bg=p["editor"],
            fg=p["muted"],
            anchor="e",
        )
        self.workspace_count.grid(row=0, column=1, sticky="e")

        self.canvas = tk.Canvas(work, highlightthickness=1, highlightbackground=p["line"], bd=0)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(work, orient="vertical", command=self.canvas.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.surface = tk.Frame(self.canvas)
        self.surface.pack_propagate(False)
        self.window_id = self.canvas.create_window((0, 0), window=self.surface, anchor="nw")
        self.surface.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._canvas_resized)
        self.canvas.bind("<ButtonRelease-1>", self._drop_existing)
        self.canvas.bind("<Delete>", self._delete_selected)
        self.app.root.bind_all("<ButtonRelease-1>", self._finish_palette_drag, add="+")
        self.app.root.bind_all("<ButtonRelease-1>", self._drop_existing, add="+")
        self.app.root.bind_all("<B1-Motion>", self._palette_motion, add="+")
        self.app.root.bind_all("<B1-Motion>", self._drag_motion, add="+")
        self.app.root.bind("<Delete>", self._delete_selected, add="+")
        self.selected = None
        self.drop_zones = []
        self.trash = tk.Label(
            work,
            text="삭제하려면 이곳으로 끌어오세요",
            bg="#6b2737",
            fg="white",
            font=(self.app.settings.font_family, 10, "bold"),
            padx=12,
            pady=8,
        )
        self.trash.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self._open_category(*self.PALETTE[0])

    def _open_category(self, category, items):
        self.active_category = category
        for child in self.category_panel.winfo_children():
            child.destroy()
        self.palette_buttons = []
        for name, button in self.category_buttons.items():
            active = name == category
            color = self.CATEGORY_COLORS.get(name, self.app.palette["accent"])
            button.configure(
                bg=color if active else self.app.palette["panel"],
                fg="#ffffff" if active else self.app.palette["fg"],
                activebackground=color,
                activeforeground="#ffffff",
            )
        color = self.CATEGORY_COLORS.get(category, self.app.palette["accent"])
        tk.Label(
            self.category_panel,
            text=f"{category} 블록",
            bg=self.app.palette["panel2"],
            fg=self.app.palette["fg"],
            font=(self.app.settings.font_family, 11, "bold"),
            anchor="w",
        ).pack(fill=X, pady=(0, 4))
        tk.Label(
            self.category_panel,
            text="마우스로 끌어서 조립하세요.",
            bg=self.app.palette["panel2"],
            fg=self.app.palette["muted"],
            anchor="w",
        ).pack(fill=X, pady=(0, 12))
        for label, kind in items:
            button = tk.Button(
                self.category_panel,
                text=f"  {label}",
                anchor="w",
                bg=self.COLORS.get(kind, color),
                fg="#ffffff",
                activebackground=self._darken(self.COLORS.get(kind, color)),
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=10,
                pady=9,
                cursor="hand2",
                font=(self.app.settings.font_family, 10, "bold"),
            )
            button.pack(fill=X, pady=4)
            button.bind("<ButtonPress-1>", lambda _event, value=kind: self._start_palette_drag(value))
            self.palette_buttons.append(button)

    def _canvas_resized(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)
        width = max(320, min(620, event.width - 96))
        for widget in self.block_widgets.values():
            widget.place_configure(width=width)

    def apply_settings(self):
        palette = self.app.palette
        self.configure(style="Editor.TFrame")
        self.category_bar.configure(bg=palette["panel"])
        self.category_heading.configure(bg=palette["panel"], fg=palette["fg"])
        self.category_panel.configure(bg=palette["panel2"])
        self.work_frame.configure(bg=palette["editor"])
        self.workspace_header.configure(bg=palette["editor"])
        self.workspace_title.configure(bg=palette["editor"], fg=palette["fg"])
        self.workspace_count.configure(bg=palette["editor"], fg=palette["muted"])
        self.canvas.configure(bg=palette["editor"])
        self.surface.configure(bg=palette["editor"])
        self.trash.configure(bg=palette["error"], fg="#ffffff")
        self.app.style.configure(
            "BlockCategory.TButton",
            background=palette["panel2"],
            foreground=palette["fg"],
            padding=(10, 7),
        )
        self.app.style.configure(
            "BlockCategoryActive.TButton",
            background=palette["select"],
            foreground=palette["fg"],
            padding=(10, 7),
        )
        for name, button in self.category_buttons.items():
            active = name == self.active_category
            color = self.CATEGORY_COLORS.get(name, palette["accent"])
            button.configure(
                bg=color if active else palette["panel"],
                fg="#ffffff" if active else palette["fg"],
                activebackground=color,
                activeforeground="#ffffff",
            )
        if self.active_category is not None:
            items = dict((category, values) for category, values in self.PALETTE)[self.active_category]
            self._open_category(self.active_category, items)
        self._render()

    def load_source(self, source: str, strict: bool = True) -> None:
        from lexer.lexer import Lexer
        from parser.parser import Parser
        try:
            self.program = Parser(Lexer(source).tokenize(), source).parse()
        except Exception:
            if strict:
                raise
            self.program = ProgramNode([])
        self._render()

    def source(self) -> str:
        return AstSourceGenerator().generate(self.program)

    def _start_palette_drag(self, kind):
        self.drag_kind = kind

    def _palette_motion(self, event):
        target = self._body_at(event.x_root, event.y_root)
        for zone, _body in self.drop_zones:
            zone.configure(highlightbackground="#ffd166" if target and target[0] is zone else self.app.palette["line"])
        if self.drag_kind is not None:
            self._update_insert_preview(event.x_root, event.y_root, 52)

    def _finish_palette_drag(self, event):
        if self.drag_kind is None:
            return
        canvas_x = self.canvas.winfo_rootx()
        canvas_y = self.canvas.winfo_rooty()
        inside = canvas_x <= event.x_root <= canvas_x + self.canvas.winfo_width() and canvas_y <= event.y_root <= canvas_y + self.canvas.winfo_height()
        if self.drag_kind is not None and inside:
            target = self._body_at(event.x_root, event.y_root)
            target_list = target[1] if target else self.program.statements
            new_node = self._new_node(self.drag_kind)
            if target is None and self.preview_index is not None:
                target_list.insert(self.preview_index, new_node)
            else:
                target_list.append(new_node)
            self._changed()
        self.drag_kind = None
        self._clear_insert_preview()
        for zone, _body in self.drop_zones:
            zone.configure(highlightbackground=self.app.palette["line"])

    def _body_at(self, x_root, y_root):
        for zone, body in self.drop_zones:
            left = zone.winfo_rootx()
            top = zone.winfo_rooty()
            right = left + zone.winfo_width()
            bottom = top + zone.winfo_height()
            if left <= x_root <= right and top <= y_root <= bottom:
                return zone, body
        return None

    def _new_node(self, kind):
        value = LiteralNode("안녕하세요")
        if kind == "print": return PrintNode(value)
        if kind == "input": return InputNode("이름", LiteralNode("이름: "))
        if kind == "declare": return VarAssignNode("변수", LiteralNode(0), declare=True)
        if kind == "assign": return VarAssignNode("변수", LiteralNode(0))
        if kind == "if": return IfNode(LiteralNode(True), [PrintNode(value)], [])
        if kind == "else": return IfNode(LiteralNode(False), [], [PrintNode(value)])
        if kind == "repeat": return RepeatNode(LiteralNode(3), [PrintNode(value)])
        if kind == "function": return FunctionNode("인사", ["이름"], [PrintNode(IdentifierNode("이름"))])
        if kind == "call": return FunctionCallNode("인사", [LiteralNode("Hangullo")])
        operators = {"add": "+", "subtract": "-", "multiply": "*", "divide": "/", "compare": ">=", "and": "그리고", "or": "또는"}
        if kind in operators: return PrintNode(BinaryOpNode(LiteralNode(1), operators[kind], LiteralNode(2)))
        if kind == "not": return PrintNode(UnaryOpNode("아니다", LiteralNode(True)))
        if kind == "identifier": return PrintNode(IdentifierNode("변수"))
        return PrintNode(LiteralNode(""))

    def _render(self):
        for child in self.surface.winfo_children():
            child.destroy()
        self.drop_zones = []
        self.block_widgets = {}
        self.connector_widgets = []
        self.workspace_count.configure(text=f"{len(self.program.statements)}개 블록")
        for index, node in enumerate(self.program.statements):
            self._render_node(self.surface, node, index, 0)
        if not self.program.statements:
            self.empty_state = tk.Frame(
                self.surface,
                bg=self.app.palette["editor"],
                highlightthickness=1,
                highlightbackground=self.app.palette["line"],
                padx=24,
                pady=20,
            )
            self.empty_state.place(x=24, y=24, width=420, height=112)
            tk.Label(
                self.empty_state,
                text="아직 블록이 없습니다",
                bg=self.app.palette["editor"],
                fg=self.app.palette["fg"],
                font=(self.app.settings.font_family, 13, "bold"),
                anchor="w",
            ).pack(fill=X)
            tk.Label(
                self.empty_state,
                text="왼쪽 팔레트에서 블록을 끌어와 프로그램을 시작하세요.",
                bg=self.app.palette["editor"],
                fg=self.app.palette["muted"],
                anchor="w",
                wraplength=360,
            ).pack(fill=X, pady=(7, 0))
        minimum_height = 170 if not self.program.statements else 120
        self.surface.configure(height=max(minimum_height, len(self.program.statements) * 90 + 40))
        self.update_idletasks()
        self._ensure_positions()
        self._draw_connectors()

    def _render_node(self, parent, node, index, indent):
        block_color = self.COLORS.get(self._kind(node), "#5f9ea0")
        frame = tk.Frame(
            parent,
            bg=block_color,
            padx=10,
            pady=8,
            cursor="hand2",
            highlightthickness=2,
            highlightbackground=self._darken(block_color),
            highlightcolor="#ffffff",
        )
        if parent is self.surface:
            x, y = self.positions.get(id(node), (24, index * 90 + 20))
            frame.place(x=x, y=y, width=max(320, min(620, self.canvas.winfo_width() - 96)))
            self.block_widgets[id(node)] = frame
        else:
            frame.pack(fill=X, pady=4, padx=(indent * 22, 4))
        frame.bind("<ButtonPress-1>", lambda event, item=frame, item_node=node: self._start_existing(event, item, item_node))
        self._render_content(frame, node)
        info = tk.Button(
            frame,
            text="ⓘ",
            width=3,
            relief="flat",
            bd=0,
            bg=frame.cget("bg"),
            fg="white",
            activebackground=frame.cget("bg"),
            activeforeground="white",
            command=lambda item=frame, item_node=node: self._show_tooltip_for(item, item_node),
        )
        info.pack(side="right", padx=(4, 0))
        info.bind("<Enter>", lambda _event, item=frame, item_node=node: self._show_tooltip_for(item, item_node))
        info.bind("<Leave>", lambda _event: self._hide_tooltip())
        tk.Button(
            frame,
            text="×",
            width=3,
            relief="flat",
            bd=0,
            bg=frame.cget("bg"),
            fg="white",
            activebackground=self._darken(frame.cget("bg")),
            activeforeground="white",
            font=(self.app.settings.font_family, 11, "bold"),
            command=lambda item_node=node: self._remove(item_node),
        ).pack(side=RIGHT)
        if isinstance(node, (IfNode, RepeatNode, FunctionNode)):
            bodies = [("실행 영역", node.then_body)]
            if isinstance(node, IfNode):
                bodies = [("참일 때", node.then_body), ("아니면", node.else_body)]
            for title, children in bodies:
                zone = tk.Frame(
                    frame,
                    bg=self.app.palette["editor"],
                    padx=10,
                    pady=7,
                    highlightthickness=2,
                    highlightbackground=self._darken(block_color),
                )
                zone.pack(fill=X, pady=(6, 0))
                tk.Label(
                    zone,
                    text=title,
                    bg=self.app.palette["editor"],
                    fg=self.app.palette["muted"],
                    anchor="w",
                    font=(self.app.settings.font_family, 9, "bold"),
                ).pack(fill=X)
                self.drop_zones.append((zone, children))
                for body_index, child in enumerate(children):
                    self._render_node(zone, child, body_index, indent + 1)

    def _render_content(self, frame, node):
        background = frame.cget("bg")
        if isinstance(node, PrintNode):
            tk.Label(frame, text="출력", bg=background, fg="white").pack(side=LEFT, padx=(0, 6))
            self._value_block(frame, node.value, lambda value: self._set_node_value(node, "value", value))
        elif isinstance(node, VarAssignNode):
            tk.Label(frame, text="변수" if node.declare else "저장", bg=background, fg="white").pack(side=LEFT, padx=(0, 5))
            self._name_entry(frame, node, "name")
            tk.Label(frame, text="←", bg=background, fg="white").pack(side=LEFT, padx=5)
            self._value_block(frame, node.value, lambda value: self._set_node_value(node, "value", value))
        elif isinstance(node, InputNode):
            tk.Label(frame, text="입력", bg=background, fg="white").pack(side=LEFT, padx=(0, 5))
            self._name_entry(frame, node, "name")
            self._value_block(frame, node.prompt, lambda value: self._set_node_value(node, "prompt", value), "안내 문구", allow_empty=True)
        elif isinstance(node, IfNode):
            tk.Label(frame, text="만약", bg=background, fg="white").pack(side=LEFT, padx=(0, 5))
            self._value_block(frame, node.condition, lambda value: self._set_node_value(node, "condition", value))
        elif isinstance(node, RepeatNode):
            tk.Label(frame, text="반복", bg=background, fg="white").pack(side=LEFT, padx=(0, 5))
            self._value_block(frame, node.count, lambda value: self._set_node_value(node, "count", value))
        elif isinstance(node, FunctionNode):
            tk.Label(frame, text="함수", bg=background, fg="white").pack(side=LEFT, padx=(0, 5))
            self._name_entry(frame, node, "name")
        elif isinstance(node, FunctionCallNode):
            tk.Label(frame, text="호출", bg=background, fg="white").pack(side=LEFT, padx=(0, 5))
            self._name_entry(frame, node, "name")
            for index, argument in enumerate(node.arguments):
                self._value_block(
                    frame,
                    argument,
                    lambda value, position=index: self._set_call_argument(node, position, value),
                )
        elif isinstance(node, ReturnNode):
            tk.Label(frame, text="반환", bg=background, fg="white").pack(side=LEFT, padx=(0, 5))
            self._value_block(frame, node.value, lambda value: self._set_node_value(node, "value", value))
        else:
            tk.Label(frame, text=self._label(node), bg=background, fg="white", anchor="w").pack(side=LEFT, fill=X, expand=True)

    def _value_block(self, parent, value, setter, placeholder="값", allow_empty=False):
        """Render expression AST nodes as editable round value blocks."""
        if isinstance(value, BinaryOpNode):
            group = tk.Frame(parent, bg=parent.cget("bg"))
            group.pack(side=LEFT, padx=(0, 4))
            self._value_block(group, value.left, lambda replacement: self._set_expression_part(value, "left", replacement))
            self._round_block(group, value.operator, "#176b87", lambda event: self._show_operator_menu(event, value))
            self._value_block(group, value.right, lambda replacement: self._set_expression_part(value, "right", replacement))
            return
        if isinstance(value, UnaryOpNode):
            group = tk.Frame(parent, bg=parent.cget("bg"))
            group.pack(side=LEFT, padx=(0, 4))
            self._round_block(group, value.operator, "#176b87", lambda event: self._show_unary_menu(event, value))
            self._value_block(group, value.operand, lambda replacement: self._set_expression_part(value, "operand", replacement))
            return

        text, color = self._value_block_text(value, placeholder)
        self._round_block(
            parent,
            text,
            color,
            lambda event: self._show_value_menu(event, value, setter, allow_empty),
            lambda event: self._edit_current_value(value, setter),
        )

    def _round_block(self, parent, text, color, menu_command, value_command=None):
        font = tkfont.Font(family=self.app.settings.font_family, size=9, weight="bold")
        text = self._fit_bubble_text(font, text, 146)
        value_width = max(58, min(176, font.measure(text) + 30))
        arrow_width = 30
        width = value_width + arrow_width
        height = 30
        canvas = tk.Canvas(parent, width=width, height=height, bg=parent.cget("bg"), highlightthickness=0, bd=0, cursor="hand2")
        canvas.pack(side=LEFT, padx=(0, 5))
        radius = height // 2
        canvas.create_oval(0, 1, radius * 2, height - 1, fill=color, outline=self._darken(color))
        canvas.create_rectangle(radius, 1, width - radius, height - 1, fill=color, outline=color)
        canvas.create_oval(width - radius * 2, 1, width, height - 1, fill=self._darken(color), outline=self._darken(color))
        canvas.create_rectangle(value_width, 1, width - radius, height - 1, fill=self._darken(color), outline=self._darken(color))
        canvas.create_line(value_width, 5, value_width, height - 5, fill="#ffffff", width=1)
        canvas.create_text(value_width // 2, height // 2, text=text, fill="#ffffff", font=font)
        canvas.create_polygon(value_width + 9, 11, value_width + 21, 11, value_width + 15, 17, fill="#ffffff", outline="#ffffff")

        def clicked(event):
            if event.x >= value_width:
                menu_command(event)
            elif value_command is not None:
                value_command(event)

        canvas.bind("<Button-1>", clicked)
        return canvas

    def _fit_bubble_text(self, font, text, maximum_width):
        if font.measure(text) <= maximum_width:
            return text
        shortened = text
        while shortened and font.measure(f"{shortened}...") > maximum_width:
            shortened = shortened[:-1]
        return f"{shortened}..."

    def _value_block_text(self, value, placeholder):
        if value is None:
            return placeholder, "#708090"
        if isinstance(value, IdentifierNode):
            return value.name, "#b56b00"
        if isinstance(value, LiteralNode):
            if isinstance(value.value, str):
                return f'"{value.value}"' or '""', "#356fbb"
            if isinstance(value.value, bool):
                return "참" if value.value else "거짓", "#7653b8"
            return str(value.value), "#bc7b12"
        return AstSourceGenerator()._expression(value), "#176b87"

    def _show_value_menu(self, event, value, setter, allow_empty):
        menu = tk.Menu(self, tearoff=False, bg=self.app.palette["panel2"], fg=self.app.palette["fg"], activebackground=self.app.palette["select"])
        menu.add_command(label="문자열", command=lambda: self._edit_string(value, setter))
        menu.add_command(label="숫자", command=lambda: self._edit_number(value, setter))
        menu.add_command(label="참", command=lambda: setter(LiteralNode(True)))
        menu.add_command(label="거짓", command=lambda: setter(LiteralNode(False)))

        variables = tk.Menu(menu, tearoff=False)
        names = self._available_variables()
        if names:
            for name in names:
                variables.add_command(label=name, command=lambda selected=name: setter(IdentifierNode(selected)))
        else:
            variables.add_command(label="사용 가능한 변수가 없습니다", state="disabled")
        menu.add_cascade(label="변수", menu=variables)

        operations = tk.Menu(menu, tearoff=False)
        for label, operator in (("더하기", "+"), ("빼기", "-"), ("곱하기", "*"), ("나누기", "/"), ("나머지", "%"), ("비교", ">="), ("그리고", "그리고"), ("또는", "또는")):
            operations.add_command(label=label, command=lambda op=operator: setter(BinaryOpNode(LiteralNode(0), op, LiteralNode(0))))
        operations.add_command(label="아니다", command=lambda: setter(UnaryOpNode("아니다", LiteralNode(True))))
        menu.add_cascade(label="연산", menu=operations)
        if allow_empty:
            menu.add_separator()
            menu.add_command(label="값 없음", command=lambda: setter(None))
        menu.tk_popup(event.x_root, event.y_root)

    def _show_operator_menu(self, event, expression):
        menu = tk.Menu(self, tearoff=False)
        for label, operator in (("더하기", "+"), ("빼기", "-"), ("곱하기", "*"), ("나누기", "/"), ("나머지", "%"), ("같다", "=="), ("크거나 같다", ">="), ("그리고", "그리고"), ("또는", "또는")):
            menu.add_command(label=label, command=lambda op=operator: self._set_expression_part(expression, "operator", op))
        menu.tk_popup(event.x_root, event.y_root)

    def _show_unary_menu(self, event, expression):
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label="아니다", command=lambda: self._set_expression_part(expression, "operator", "아니다"))
        menu.tk_popup(event.x_root, event.y_root)

    def _edit_string(self, value, setter):
        initial = value.value if isinstance(value, LiteralNode) and isinstance(value.value, str) else ""
        text = self._value_input_dialog("문자열 값", "문자열을 입력하세요.", initial)
        if text is not None:
            setter(LiteralNode(text))

    def _edit_current_value(self, value, setter):
        if isinstance(value, LiteralNode) and isinstance(value.value, str):
            self._edit_string(value, setter)
        elif isinstance(value, LiteralNode) and isinstance(value.value, (int, float)) and not isinstance(value.value, bool):
            self._edit_number(value, setter)

    def _edit_number(self, value, setter):
        initial = value.value if isinstance(value, LiteralNode) and isinstance(value.value, (int, float)) and not isinstance(value.value, bool) else 0
        text = self._value_input_dialog("숫자 값", "숫자를 입력하세요.", str(initial))
        if text is None:
            return
        try:
            number = float(text) if any(mark in text for mark in (".", "e", "E")) else int(text)
        except ValueError:
            self.app.write_console("블록 값 오류: 숫자만 입력할 수 있습니다.\n", "error")
            return
        setter(LiteralNode(number))

    def _value_input_dialog(self, title, prompt, initial):
        p = self.app.palette
        dialog = tk.Toplevel(self.app.root, bg=p["panel"])
        dialog.title(title)
        dialog.transient(self.app.root)
        dialog.resizable(False, False)
        dialog.grab_set()
        result = {"value": None}

        content = tk.Frame(dialog, bg=p["panel"], padx=20, pady=18)
        content.pack(fill=BOTH, expand=True)
        tk.Label(
            content,
            text=title,
            bg=p["panel"],
            fg=p["fg"],
            font=(self.app.settings.font_family, 12, "bold"),
            anchor="w",
        ).pack(fill=X)
        tk.Label(content, text=prompt, bg=p["panel"], fg=p["muted"], anchor="w").pack(fill=X, pady=(5, 10))
        entry = tk.Entry(
            content,
            bg=p["panel2"],
            fg=p["fg"],
            insertbackground=p["fg"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=p["line"],
            highlightcolor=p["accent"],
            font=(self.app.settings.font_family, 10),
        )
        entry.insert(0, initial)
        entry.pack(fill=X, ipady=7)

        actions = tk.Frame(content, bg=p["panel"])
        actions.pack(fill=X, pady=(16, 0))

        def confirm(_event=None):
            result["value"] = entry.get()
            dialog.destroy()

        def cancel(_event=None):
            dialog.destroy()

        tk.Button(
            actions,
            text="취소",
            command=cancel,
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            bg=p["panel2"],
            fg=p["fg"],
            activebackground=p["select"],
            activeforeground=p["fg"],
        ).pack(side=RIGHT)
        tk.Button(
            actions,
            text="확인",
            command=confirm,
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            bg=p["accent"],
            fg="#ffffff",
            activebackground=p["accent"],
            activeforeground="#ffffff",
        ).pack(side=RIGHT, padx=(0, 6))
        dialog.protocol("WM_DELETE_WINDOW", cancel)
        dialog.bind("<Return>", confirm)
        dialog.bind("<Escape>", cancel)
        dialog.update_idletasks()
        x = self.app.root.winfo_rootx() + max(0, (self.app.root.winfo_width() - dialog.winfo_width()) // 2)
        y = self.app.root.winfo_rooty() + max(0, (self.app.root.winfo_height() - dialog.winfo_height()) // 3)
        dialog.geometry(f"+{x}+{y}")
        entry.focus_set()
        entry.selection_range(0, END)
        dialog.wait_window()
        return result["value"]

    def _available_variables(self):
        names = []

        def collect(statements):
            for statement in statements:
                if isinstance(statement, (VarAssignNode, InputNode)) and statement.name not in names:
                    names.append(statement.name)
                if isinstance(statement, FunctionNode):
                    for parameter in statement.parameters:
                        if parameter not in names:
                            names.append(parameter)
                    collect(statement.body)
                elif isinstance(statement, IfNode):
                    collect(statement.then_body)
                    collect(statement.else_body)
                    for _condition, body in statement.elif_branches or []:
                        collect(body)
                elif isinstance(statement, RepeatNode):
                    collect(statement.body)

        collect(self.program.statements)
        return names

    def _set_node_value(self, node, attribute, value):
        setattr(node, attribute, value)
        self._changed()

    def _set_call_argument(self, node, index, value):
        node.arguments[index] = value
        self._changed()

    def _set_expression_part(self, expression, attribute, value):
        setattr(expression, attribute, value)
        self._changed()

    def _name_entry(self, parent, node, attribute):
        entry = tk.Entry(parent, width=10)
        entry.configure(
            bg=self.app.palette["panel2"],
            fg=self.app.palette["fg"],
            insertbackground=self.app.palette["fg"],
            selectbackground=self.app.palette["select"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.app.palette["line"],
            highlightcolor=self.app.palette["accent"],
        )
        entry.insert(0, getattr(node, attribute))
        entry.pack(side=LEFT, padx=(0, 5))
        entry.bind("<Return>", lambda _event: self._update_name(node, attribute, entry.get()))
        entry.bind("<FocusOut>", lambda _event: self._update_name(node, attribute, entry.get()))

    def _update_name(self, node, attribute, value):
        value = value.strip()
        if value:
            setattr(node, attribute, value)
            self._changed()

    def _kind(self, node):
        if isinstance(node, VarAssignNode):
            return "declare" if node.declare else "assign"
        return {PrintNode: "print", InputNode: "input", IfNode: "if", RepeatNode: "repeat", FunctionNode: "function", FunctionCallNode: "call"}.get(type(node), "expression")

    def _label(self, node):
        if isinstance(node, PrintNode): return f"출력  {AstSourceGenerator()._expression(node.value)}"
        if isinstance(node, VarAssignNode): return f"{'변수 ' if node.declare else ''}{node.name} = {AstSourceGenerator()._expression(node.value)}"
        if isinstance(node, InputNode): return f"입력  {node.name}, {AstSourceGenerator()._expression(node.prompt) if node.prompt else '없음'}"
        if isinstance(node, IfNode): return f"만약  {AstSourceGenerator()._expression(node.condition)}"
        if isinstance(node, RepeatNode): return f"반복  {AstSourceGenerator()._expression(node.count)}회"
        if isinstance(node, FunctionNode): return f"함수  {node.name}({', '.join(node.parameters)})"
        if isinstance(node, FunctionCallNode): return f"함수 호출  {node.name}()"
        return AstSourceGenerator()._expression(node)

    def _ensure_positions(self):
        y = 18
        for node in self.program.statements:
            widget = self.block_widgets.get(id(node))
            if widget is None:
                continue
            self.positions[id(node)] = (24, y)
            widget.place_configure(x=24, y=y)
            y += widget.winfo_height() + 12
        minimum_height = 170 if not self.program.statements else 120
        self.surface.configure(height=max(minimum_height, y + 18))

    def _draw_connectors(self):
        for connector in self.connector_widgets:
            connector.destroy()
        self.connector_widgets = []
        for first, second in zip(self.program.statements, self.program.statements[1:]):
            first_widget = self.block_widgets.get(id(first))
            second_widget = self.block_widgets.get(id(second))
            if first_widget is None or second_widget is None:
                continue
            first_x, first_y = self.positions[id(first)]
            second_x, second_y = self.positions[id(second)]
            if abs(first_x - second_x) > 18 or second_y < first_y + first_widget.winfo_height() - 20:
                continue
            connector = tk.Frame(self.surface, bg=self.app.palette["line"], width=4, height=max(8, second_y - (first_y + first_widget.winfo_height())))
            connector.place(x=first_x + 18, y=first_y + first_widget.winfo_height(), anchor="n")
            self.connector_widgets.append(connector)

    def _update_insert_preview(self, x_root, y_root, height):
        if not self.block_widgets:
            self._clear_insert_preview()
            return
        canvas_x = x_root - self.surface.winfo_rootx()
        canvas_y = y_root - self.surface.winfo_rooty()
        ordered = [
            item for item in sorted(
            ((index, node, self.block_widgets.get(id(node))) for index, node in enumerate(self.program.statements)),
            key=lambda item: item[2].winfo_y() if item[2] is not None else 0,
            )
            if item[2] is not None and item[2] is not self.drag_widget
        ]
        if not ordered:
            self._clear_insert_preview()
            return

        stack_left = min(widget.winfo_x() for _index, _node, widget in ordered)
        stack_right = max(widget.winfo_x() + widget.winfo_width() for _index, _node, widget in ordered)
        if not stack_left - 24 <= canvas_x <= stack_right + 24:
            self._clear_insert_preview()
            return

        candidate = None
        snap_margin = 18
        for index, _node, widget in ordered:
            widget_top = widget.winfo_y()
            if abs(canvas_y - widget_top) <= snap_margin:
                candidate = (index, widget_top - height - 12)
                break

        if candidate is None:
            last_index, _node, last_widget = ordered[-1]
            last_bottom = last_widget.winfo_y() + last_widget.winfo_height()
            if abs(canvas_y - last_bottom) <= snap_margin:
                candidate = (last_index + 1, last_bottom + 12)

        if candidate is None:
            self._clear_insert_preview()
            return
        index, y = candidate
        preview_node = self.drag_node if self.drag_widget is not None else self._new_node(self.drag_kind)
        preview_color = self.COLORS.get(self._kind(preview_node), "#5f9ea0")
        preview_text = self._label(preview_node)
        if self.preview is None:
            self.preview = tk.Frame(
                self.surface,
                padx=8,
                pady=6,
                relief="flat",
                bd=0,
                highlightthickness=2,
                highlightbackground="#ffd166",
            )
            self.preview_label = tk.Label(self.preview, anchor="w")
            self.preview_label.pack(fill=X)
        ghost_color = self._blend_with_editor(preview_color)
        self.preview.configure(bg=ghost_color)
        self.preview_label.configure(text=f"여기에 결합: {preview_text}", bg=ghost_color, fg=self.app.palette["fg"])
        y = max(8, y)
        self.preview.place(x=24, y=y, width=max(320, min(620, self.canvas.winfo_width() - 96)), height=height)
        self.preview.lift()
        self.preview_index = index
        self.preview_position = (24, y)

    def _clear_insert_preview(self):
        if self.preview is not None:
            self.preview.destroy()
            self.preview = None
        self.preview_index = None
        self.preview_position = None

    def _show_tooltip_for(self, widget, node):
        self._hide_tooltip()
        tooltip = tk.Toplevel(self.app.root)
        self.tooltip = tooltip
        tooltip.overrideredirect(True)
        tooltip.attributes("-topmost", True)
        text = self.DESCRIPTIONS.get(self._kind(node), "이 블록은 Hangullo 프로그램의 한 명령을 나타냅니다.")
        label = tk.Label(tooltip, text=text, bg="#fff3bf", fg="#3b2f00", padx=9, pady=6, relief="solid", bd=1)
        label.pack()
        tooltip.update_idletasks()
        tooltip.geometry(f"+{widget.winfo_rootx() + widget.winfo_width() + 8}+{widget.winfo_rooty()}")

    def _hide_tooltip(self):
        if self.tooltip is not None:
            self.tooltip.destroy()
            self.tooltip = None

    def _start_existing(self, _event, widget, node):
        self.drag_widget = widget
        self.drag_node = node
        self.drag_moved = False
        self.selected_node = node
        self.selected = widget
        widget.configure(relief="solid", bd=2)
        widget.lift()
        if widget.master is self.surface:
            self.drag_origin = (_event.x_root, _event.y_root)
            self.drag_position = (widget.winfo_x(), widget.winfo_y())

    def _drag_motion(self, event):
        if self.drag_widget is None or self.drag_widget.master is not self.surface:
            return
        delta_x = event.x_root - self.drag_origin[0]
        delta_y = event.y_root - self.drag_origin[1]
        if not self.drag_moved and abs(delta_x) < 4 and abs(delta_y) < 4:
            return
        if not self.drag_moved:
            self._set_drag_appearance(self.drag_widget, faded=True)
        self.drag_moved = True
        new_x = max(8, self.drag_position[0] + delta_x)
        new_y = max(8, self.drag_position[1] + delta_y)
        self.drag_widget.place_configure(x=new_x, y=new_y)
        self.surface.configure(height=max(self.surface.winfo_height(), new_y + self.drag_widget.winfo_height() + 24))
        target = self._body_at(event.x_root, event.y_root)
        for zone, _body in self.drop_zones:
            zone.configure(highlightbackground="#ffd166" if target and target[0] is zone else self.app.palette["line"])
        self._update_insert_preview(event.x_root, event.y_root, self.drag_widget.winfo_height())

    def _drop_existing(self, event=None):
        if self.app.mode != "블록 코딩" or self.app.current_tab() is None or self.app.current_tab().block_editor is not self:
            return
        if self.drag_widget is not None:
            dragged_widget = self.drag_widget
            dragged_node = self.drag_node
            self._restore_drag_appearance()
            dragged_widget.configure(relief="flat", bd=0)
            was_moved = self.drag_moved
            self.drag_widget = None
            self.drag_moved = False
            for zone, _body in self.drop_zones:
                zone.configure(highlightbackground=self.app.palette["line"])
            if not was_moved:
                dragged_widget.configure(
                    highlightthickness=2,
                    highlightbackground=self._darken(dragged_widget.cget("bg")),
                )
                self._clear_insert_preview()
                return
            for widget in self.surface.winfo_children():
                if isinstance(widget, tk.Frame):
                    widget.configure(highlightthickness=0)
            if event is not None and self._inside(self.trash, event.x_root, event.y_root):
                self._clear_insert_preview()
                self._remove(dragged_node)
                self.positions.pop(id(dragged_node), None)
                return
            target = self._body_at(event.x_root, event.y_root) if event is not None else None
            if target:
                self._clear_insert_preview()
                self._remove_from(self.program.statements, dragged_node)
                target[1].append(dragged_node)
                self.positions.pop(id(dragged_node), None)
                self._changed()
                return
            if self.preview_index is not None and dragged_node in self.program.statements:
                drag_index = self.program.statements.index(dragged_node)
                item = self.program.statements.pop(drag_index)
                target_index = self.preview_index - (1 if drag_index < self.preview_index else 0)
                self.program.statements.insert(max(0, target_index), item)
                self.positions.pop(id(dragged_node), None)
            elif event is not None:
                self.positions[id(dragged_node)] = (24, self.selected.winfo_y())
            self._clear_insert_preview()
            self._changed()

    def _delete_selected(self, _event=None):
        if self.app.mode != "블록 코딩" or self.app.current_tab() is None or self.app.current_tab().block_editor is not self:
            return
        if self.selected is not None:
            self.selected.destroy()
            self.selected = None
            self._remove(getattr(self, "selected_node", None))

    def _inside(self, widget, x_root, y_root):
        left = widget.winfo_rootx()
        top = widget.winfo_rooty()
        return left <= x_root <= left + widget.winfo_width() and top <= y_root <= top + widget.winfo_height()

    def _blend_with_editor(self, color: str, ratio: float = 0.28) -> str:
        base = self.app.palette["editor"]
        try:
            color = color.lstrip("#")
            base = base.lstrip("#")
            red = int(color[0:2], 16)
            green = int(color[2:4], 16)
            blue = int(color[4:6], 16)
            base_red = int(base[0:2], 16)
            base_green = int(base[2:4], 16)
            base_blue = int(base[4:6], 16)
        except (ValueError, IndexError):
            return self.app.palette["panel2"]
        mixed = (
            round(base_red * (1 - ratio) + red * ratio),
            round(base_green * (1 - ratio) + green * ratio),
            round(base_blue * (1 - ratio) + blue * ratio),
        )
        return f"#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}"

    def _set_drag_appearance(self, widget, faded: bool):
        """Approximate widget opacity by fading every visible color into the canvas."""
        if not faded or self.drag_appearance:
            return
        color_options = (
            "background",
            "foreground",
            "activebackground",
            "activeforeground",
            "insertbackground",
            "highlightbackground",
            "highlightcolor",
        )
        for item in (widget, *widget.winfo_children()):
            for option in color_options:
                if option not in item.keys():
                    continue
                try:
                    original = item.cget(option)
                    self.drag_appearance.append((item, option, original))
                    item.configure(**{option: self._fade_color(original, 0.62)})
                except tk.TclError:
                    continue

    def _restore_drag_appearance(self):
        for widget, option, color in self.drag_appearance:
            try:
                if widget.winfo_exists():
                    widget.configure(**{option: color})
            except tk.TclError:
                continue
        self.drag_appearance = []

    def _fade_color(self, color: str, opacity: float) -> str:
        try:
            red, green, blue = (value // 256 for value in self.winfo_rgb(color))
            base_red, base_green, base_blue = (
                value // 256 for value in self.winfo_rgb(self.app.palette["editor"])
            )
        except tk.TclError:
            return color
        mixed = (
            round(base_red * (1 - opacity) + red * opacity),
            round(base_green * (1 - opacity) + green * opacity),
            round(base_blue * (1 - opacity) + blue * opacity),
        )
        return f"#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}"

    def _darken(self, color: str) -> str:
        color = color.lstrip("#")
        try:
            red = max(0, int(color[0:2], 16) - 34)
            green = max(0, int(color[2:4], 16) - 34)
            blue = max(0, int(color[4:6], 16) - 34)
        except (ValueError, IndexError):
            return "#000000"
        return f"#{red:02x}{green:02x}{blue:02x}"

    def _remove(self, target):
        if target is None:
            return
        if self._remove_from(self.program.statements, target):
            self._changed()

    def _remove_from(self, statements, target):
        if target in statements:
            statements.remove(target)
            return True
        for node in statements:
            bodies = []
            if isinstance(node, IfNode):
                bodies = [node.then_body, node.else_body, *[body for _, body in node.elif_branches or []]]
            elif isinstance(node, (RepeatNode, FunctionNode)):
                bodies = [node.body]
            for body in bodies:
                if self._remove_from(body, target):
                    return True
        return False

    def _changed(self):
        self._render()
        self.app.block_source_changed(self.source())
