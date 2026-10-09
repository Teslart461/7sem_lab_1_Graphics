import math
import tkinter as tk
from tkinter import ttk

from model import create_letter_p, create_coordinate_axes
from matrix import (
    translation_matrix,
    scaling_matrix,
    rotation_x_matrix,
    rotation_y_matrix,
    rotation_z_matrix,
    reflection_xy_matrix,
    reflection_xz_matrix,
    reflection_yz_matrix,
    multiply_matrices
)
from projections import (
    orthographic_xy_matrix,
    orthographic_xz_matrix,
    orthographic_yz_matrix,
    cabinet_matrix,
    isometric_matrix,
    perspective_matrix,
    project_point_to_screen,
    project_points_to_screen
)
from animation import ScaleAboutPointAnimation


class GraphicsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №1: Аффинные преобразования и проецирование буквы «П» в 3D")
        self.root.geometry("1280x800")
        self.root.minsize(950, 650)

        # Модели буквы и осей
        self.letter = create_letter_p(width=5.0, height=7.0, thickness=1.5, depth=2.0)
        self.axes = create_coordinate_axes(length=9.0)

        # Параметры отображения
        self.scale = 28.0          # масштаб (пикселей на единицу модели)
        self.pan_x = 0.0           # смещение холста по горизонтали
        self.pan_y = 0.0           # смещение холста по вертикали
        self.canvas_width = 800
        self.canvas_height = 700

        # Текущая выбранная проекция
        self.projection_var = tk.StringVar(value="isometric")

        # Текст последнего действия
        self.last_action_text = "Готов к управлению"

        # Параметры анимации
        self.anim = None  # текущий ScaleAboutPointAnimation или None
        self.var_point_a = tk.StringVar(value="4.0")
        self.var_point_b = tk.StringVar(value="2.0")
        self.var_kx = tk.StringVar(value="2.0")
        self.var_ky = tk.StringVar(value="0.5")

        # Отображение координатной сетки на плоскости XZ
        self.show_grid = True
        self.grid_var = tk.BooleanVar(value=True)

        # Создаем пользовательский интерфейс
        self._build_ui()

        # Привязка клавиатурных событий ко всему окну
        self.root.bind("<Key>", self._on_key_press)
        self.root.focus_set()

        # Первичная отрисовка сцены
        self.redraw()


    def _build_ui(self):
        """
        Создает структуру интерфейса: левая часть - холст canvas,
        правая часть - панель управления и информации
        """
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая панель: графический холст
        canvas_frame = ttk.Frame(main_container)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#18181b",
            highlightthickness=1,
            highlightbackground="#3f3f46"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Button-1>", lambda e: self.root.focus_set())

        # Правая панель: Управление и информация
        right_container = ttk.Frame(main_container, width=355)
        right_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 5), pady=5)
        right_container.pack_propagate(False)

        # Добавил скроллбар потому что перестало помещаться в правую панель
        v_scrollbar = ttk.Scrollbar(right_container, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.right_canvas = tk.Canvas(
            right_container,
            highlightthickness=0,
            yscrollcommand=v_scrollbar.set,
            bg=self.root.cget("bg")
        )
        self.right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.config(command=self.right_canvas.yview)

        # Контейнер для всех виджетов внутри холста
        self.scrollable_frame = ttk.Frame(self.right_canvas)
        self.canvas_window_id = self.right_canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))
        )

        # Растягивание ширины содержимого под ширину панели
        self.right_canvas.bind(
            "<Configure>",
            lambda e: self.right_canvas.itemconfig(self.canvas_window_id, width=e.width)
        )

        # Прокрутка колесиком мыши при наведении курсора на правую панель
        def _on_mousewheel(event):
            self.right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(event):
            self.right_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(event):
            self.right_canvas.unbind_all("<MouseWheel>")

        self.right_canvas.bind("<Enter>", _bind_mousewheel)
        self.right_canvas.bind("<Leave>", _unbind_mousewheel)
        self.scrollable_frame.bind("<Enter>", _bind_mousewheel)
        self.scrollable_frame.bind("<Leave>", _unbind_mousewheel)

        # Блок: Анимация
        anim_group = ttk.LabelFrame(self.scrollable_frame, text=" Динамическое преобразование ", padding=8)
        anim_group.pack(fill=tk.X, pady=(0, 8), padx=2)

        ttk.Label(anim_group, text="Точка A(a, b) в плоскости XOY:").pack(anchor=tk.W, pady=(0, 2))
        point_frame = ttk.Frame(anim_group)
        point_frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(point_frame, text="a =").pack(side=tk.LEFT)
        ttk.Entry(point_frame, textvariable=self.var_point_a, width=6).pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(point_frame, text="b =").pack(side=tk.LEFT)
        ttk.Entry(point_frame, textvariable=self.var_point_b, width=6).pack(side=tk.LEFT, padx=(2, 0))
 
        ttk.Label(anim_group, text="Коэффициенты масштабирования:").pack(anchor=tk.W, pady=(0, 2))
        k_frame = ttk.Frame(anim_group)
        k_frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(k_frame, text="kx =").pack(side=tk.LEFT)
        ttk.Entry(k_frame, textvariable=self.var_kx, width=6).pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(k_frame, text="ky =").pack(side=tk.LEFT)
        ttk.Entry(k_frame, textvariable=self.var_ky, width=6).pack(side=tk.LEFT, padx=(2, 0))
 
        self.btn_anim = ttk.Button(
            anim_group,
            text="Запустить анимацию (Пробел)",
            command=self.start_animation,
        )
        self.btn_anim.pack(fill=tk.X, pady=(2, 2))

        # Блок выбора проекции
        proj_group = ttk.LabelFrame(self.scrollable_frame, text=" Проекция", padding=8)
        proj_group.pack(fill=tk.X, pady=(0, 8), padx=2)

        projections = [
            ("Изометрическая (3D)", "isometric"),
            ("Кабинетная", "cabinet"),
            ("Перспективная (Камера c=9)", "perspective"),
            ("Вид спереди (Орто XY)", "ortho_xy"),
            ("Вид сверху (Орто XZ)", "ortho_xz"),
            ("Вид сбоку (Орто YZ)", "ortho_yz"),
        ]

        for text, val in projections:
            rb = ttk.Radiobutton(
                proj_group,
                text=text,
                value=val,
                variable=self.projection_var,
                command=self.redraw
            )
            rb.pack(anchor=tk.W, pady=2)

        # Отображения координатной сетки XZ
        ttk.Separator(proj_group, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(6, 4))
        self.cb_grid = ttk.Checkbutton(
            proj_group,
            text="Сетка плоскости XZ",
            variable=self.grid_var,
            command=self._on_grid_toggle
        )
        self.cb_grid.pack(anchor=tk.W, pady=2)


        # Блок информации о модели
        info_group = ttk.LabelFrame(self.scrollable_frame, text=" Информация о модели ", padding=8)
        info_group.pack(fill=tk.X, pady=(0, 8), padx=2)

        v_count = len(self.letter.vertices)
        e_count = len(self.letter.edges)

        ttk.Label(info_group, text="Объект: 3D-буква «П»", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=1)

        self.lbl_stats = ttk.Label(info_group, text=f"Вершин: {v_count} | Рёбер: {e_count}")
        self.lbl_stats.pack(anchor=tk.W, pady=1)

        self.lbl_action = ttk.Label(info_group, text=f"Действие: {self.last_action_text}", foreground="#0284c7")
        self.lbl_action.pack(anchor=tk.W, pady=1)

        # Блок: Горячие клавиши
        kbd_group = ttk.LabelFrame(self.scrollable_frame, text=" Управление (Клавиатура) ", padding=8)
        kbd_group.pack(fill=tk.X, pady=(0, 8), padx=2)

        instructions = [
            ("Пробел", "Старт / Пауза анимации"),
            ("G", "Сетка XZ (Вкл / Выкл)"),
            ("←  →", "Перемещение по оси X (±1.0)"),
            ("↑  ↓", "Перемещение по оси Y (±1.0)"),
            ("Q / E", "Перемещение по оси Z (±1.0)"),
            ("W / S", "Вращение вокруг центра X (±5°)"),
            ("A / D", "Вращение вокруг центра Y (±5°)"),
            ("Z / C", "Вращение вокруг центра Z (±5°)"),
            ("+ / -", "Равномерный масштаб (×1.1 / ×0.9)"),
            ("1 / 2", "Растяжение по X (1.1 / 0.9)"),
            ("3 / 4", "Растяжение по Y (1.1 / 0.9)"),
            ("5 / 6", "Растяжение по Z (1.1 / 0.9)"),
            ("M", "Отражение относительно XOZ (зеркало по Y)"),
            ("N", "Отражение относительно YOZ (зеркало по X)"),
            ("B", "Отражение относительно XOY (зеркало по Z)"),
            ("R", "Сброс всех трансформаций"),
        ]

        for keys, desc in instructions:
            row = ttk.Frame(kbd_group)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=keys, font=("Consolas", 8, "bold"), width=9).pack(side=tk.LEFT)
            ttk.Label(row, text=desc, font=("Arial", 8)).pack(side=tk.LEFT)

        # Кнопка сброса
        ttk.Button(kbd_group, text="Сбросить всё к началу (R)", command=self.reset_model).pack(
            fill=tk.X, pady=(6, 2)
        )

        # Легенда координатных осей
        legend_frame = ttk.LabelFrame(self.scrollable_frame, text=" Оси координат ", padding=8)
        legend_frame.pack(fill=tk.X, pady=(0, 5), padx=2)

        tk.Label(legend_frame, text="Ось X — Красная", fg="#ef4444").pack(anchor=tk.W)

        tk.Label(legend_frame, text="Ось Y — Зеленая", fg="#22c55e").pack(anchor=tk.W)

        tk.Label(legend_frame, text="Ось Z — Синяя", fg="#38bdf8").pack(anchor=tk.W)


    def _on_key_press(self, event):
        """
        Обработчик клавиш клавиатуры
        Поддерживает английскую и русскую раскладки
        """
        if self.anim is not None and self.anim.is_running():
            keysym = event.keysym
            char = event.char.lower() if event.char else ""
            if char in ("r", "к") or keysym in ("Home", "Escape"):
                self.reset_model()
            return

        keysym = event.keysym
        char = event.char.lower() if event.char else ""

        step_move = 1.0
        step_rot = math.radians(5.0)
        scale_up = 1.10
        scale_down = 1.0 / 1.10

        # Старт / Пауза анимации на пробел
        if keysym == "space" or char == " ":
            self.start_animation()
            return

        # Перемещение вдоль осей X, Y, Z
        if keysym == "Left":
            self.translate_model(-step_move, 0.0, 0.0, "Сдвиг: -X")
        elif keysym == "Right":
            self.translate_model(step_move, 0.0, 0.0, "Сдвиг: +X")
        elif keysym == "Up":
            self.translate_model(0.0, step_move, 0.0, "Сдвиг: +Y")
        elif keysym == "Down":
            self.translate_model(0.0, -step_move, 0.0, "Сдвиг: -Y")
        elif keysym == "Prior" or char in ("q", "й"):
            self.translate_model(0.0, 0.0, step_move, "Сдвиг: +Z (на нас)")
        elif keysym == "Next" or char in ("e", "у"):
            self.translate_model(0.0, 0.0, -step_move, "Сдвиг: -Z (вглубь)")

        # Повороты (относительно начала координат / текущей ориентации модели)
        elif char in ("w", "ц"):
            self.rotate_model(step_rot, 0.0, 0.0, "Поворот: +X (+5°)")
        elif char in ("s", "ы"):
            self.rotate_model(-step_rot, 0.0, 0.0, "Поворот: -X (-5°)")
        elif char in ("a", "ф"):
            self.rotate_model(0.0, -step_rot, 0.0, "Поворот: -Y (-5°)")
        elif char in ("d", "в"):
            self.rotate_model(0.0, step_rot, 0.0, "Поворот: +Y (+5°)")
        elif char in ("z", "я"):
            self.rotate_model(0.0, 0.0, step_rot, "Поворот: +Z (+5°)")
        elif char in ("c", "с"):
            self.rotate_model(0.0, 0.0, -step_rot, "Поворот: -Z (-5°)")

        # Равномерное масштабирование детали
        elif char in ("+", "=") or keysym in ("plus", "equal"):
            self.scale_model(scale_up, scale_up, scale_up, "Масштаб: ×1.1")
        elif char in ("-", "_") or keysym in ("minus", "underscore"):
            self.scale_model(scale_down, scale_down, scale_down, "Масштаб: ×0.9")

        # Масштабирование по отдельным осям
        elif char == "1":
            self.scale_model(scale_up, 1.0, 1.0, "Растяжение по X (1.1)")
        elif char == "2":
            self.scale_model(scale_down, 1.0, 1.0, "Сжатие по X (0.9)")
        elif char == "3":
            self.scale_model(1.0, scale_up, 1.0, "Растяжение по Y (1.1)")
        elif char == "4":
            self.scale_model(1.0, scale_down, 1.0, "Сжатие по Y (0.9)")
        elif char == "5":
            self.scale_model(1.0, 1.0, scale_up, "Растяжение по Z (1.1)")
        elif char == "6":
            self.scale_model(1.0, 1.0, scale_down, "Сжатие по Z (0.9)")

        # Отражение (относительно координатных плоскостей)
        elif char in ("m", "ь"):
            self.reflect_model("y", "Отражение по Y (вверх ногами)")
        elif char in ("n", "т"):
            self.reflect_model("x", "Отражение по X (зеркало)")
        elif char in ("b", "и"):
            self.reflect_model("z", "Отражение по Z")

        # Переключение координатной сетки
        elif char in ("g", "п"):
            self.show_grid = not self.show_grid
            self.grid_var.set(self.show_grid)
            self.last_action_text = f"Сетка XZ: {'Вкл' if self.show_grid else 'Выкл'}"
            self.redraw()

        # Сброс к исходному состоянию
        elif char in ("r", "к") or keysym in ("Home", "Escape"):
            self.reset_model()

    def _on_grid_toggle(self):
        """
        Переключает видимость координатной сетки XZ по клику на флажок в UI
        """
        self.show_grid = self.grid_var.get()
        self.last_action_text = f"Сетка XZ: {'Вкл' if self.show_grid else 'Выкл'}"
        self.redraw()

    

    def translate_model(self, dx, dy, dz, action_name):
        """Перемещает букву матрицей переноса T(dx, dy, dz)."""
        m = translation_matrix(dx, dy, dz)
        self.letter.apply_matrix(m)
        self.last_action_text = action_name
        self.redraw()

    def rotate_model(self, rx, ry, rz, action_name):
        """
        Поворачивает букву вокруг начала мировых координат.
        M = Rx * Ry * Rz.
        """
        m = multiply_matrices(rotation_x_matrix(rx), rotation_y_matrix(ry), rotation_z_matrix(rz))
        self.letter.apply_matrix(m)
        self.last_action_text = action_name
        self.redraw()

    def scale_model(self, sx, sy, sz, action_name):
        """Масштабирует букву относительно начала мировых координат."""
        m = scaling_matrix(sx, sy, sz)
        self.letter.apply_matrix(m)
        self.last_action_text = action_name
        self.redraw()

    def reflect_model(self, axis, action_name):
        """Отражает букву относительно одной из координатных плоскостей, проходящих через (0,0,0)."""
        if axis == "x":
            m = reflection_yz_matrix()
        elif axis == "y":
            m = reflection_xz_matrix()
        else:
            m = reflection_xy_matrix()
        self.letter.apply_matrix(m)
        self.last_action_text = action_name
        self.redraw()

    def reset_model(self):
        """Сбрасывает все преобразования буквы и останавливает анимацию, если она шла."""
        if self.anim is not None and self.anim.is_running():
            self.anim = None
            self.btn_anim.config(text="Запустить анимацию (Пробел)", state="normal")
        self.letter.reset()
        self.last_action_text = "Сброс к началу"
        self.redraw()


    def start_animation(self):
        """
        Запускает анимацию масштабирования буквы в плоскости XOY относительно
        точки A(a, b) с коэффициентами kx, ky - с плавным, замедляющимся
        к концу возвратом в исходное состояние.
        """
        if self.anim is not None and self.anim.is_running():
            return  # анимация уже идёт
 
        try:
            a = float(self.var_point_a.get())
            b = float(self.var_point_b.get())
            kx = float(self.var_kx.get())
            ky = float(self.var_ky.get())
        except ValueError:
            self.last_action_text = "Ошибка: a, b, kx, ky должны быть числами"
            self.redraw()
            return
 
        self.anim = ScaleAboutPointAnimation(
            self.letter, point=(a, b), kx=kx, ky=ky, on_finish=self._on_animation_finished
        )
        self.last_action_text = f"Анимация: масштаб у A({a:g}, {b:g}), kx={kx:g}, ky={ky:g}"
        self.btn_anim.config(text="Анимация идёт...", state="disabled")
        self._animation_tick()
 
    def _animation_tick(self):
        if self.anim is None:
            return
        if self.anim.step():
            self.redraw()
            self.root.after(16, self._animation_tick)  # ~60 кадров/сек
 
    def _on_animation_finished(self):
        self.btn_anim.config(text="Запустить анимацию (Пробел)", state="normal")
        self.last_action_text = "Анимация завершена: объект точно вернулся в исходное состояние"


    def _get_current_projection_matrix(self):
        """
        Возвращает матрицу 4x4 для выбранной пользователем проекции.
        """
        proj_type = self.projection_var.get()
        match proj_type:
            case "isometric":
                return isometric_matrix()
            case "cabinet":
                return cabinet_matrix(angle_deg=45.0)
            case "perspective":
                return perspective_matrix(c=9.0)
            case "ortho_xy":
                return orthographic_xy_matrix()
            case "ortho_xz":
                return orthographic_xz_matrix()
            case "ortho_yz":
                return orthographic_yz_matrix()
            case _:
                return isometric_matrix()

    def redraw(self):
        """
        Полная перерисовка сцены на холсте:
            Очистка холста
            Получение текущей матрицы проекции
            Отрисовка координатных осей
            Отрисовка буквы
            Отрисовка точки геометрического центра
            Обновление информационной панели
        """
        self.canvas.delete("all")

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 1:
            self.canvas_width = w
        if h > 1:
            self.canvas_height = h

        proj_matrix = self._get_current_projection_matrix()

        # Рисуем координатную сетку на плоскости XZ (Y = 0)
        if self.show_grid:
            self._draw_grid(proj_matrix)

        # Рисуем координатные оси
        self._draw_axes(proj_matrix)

        # Рисуем букву
        self._draw_letter(proj_matrix)

        # Рисуем точку анимации (центр масштабирования)
        self._draw_animation_point(proj_matrix)

        # Обновляем текстовые метки
        self.lbl_action.config(text=f"Действие: {self.last_action_text}")

    def _draw_grid(self, proj_matrix, grid_range=8, step=1):
        """
        Отрисовывает координатную сетку на плоскости XZ:
        """
        color_grid = "#262939"
        color_sub_axis = "#3b425b"

        # Линии, параллельные оси Z (при постоянном x)
        for x in range(-grid_range, grid_range + 1, step):
            col = color_sub_axis if x == 0 else color_grid
            p1 = project_point_to_screen(
                (float(x), 0.0, float(-grid_range)),
                proj_matrix,
                self.canvas_width,
                self.canvas_height,
                self.scale,
                self.pan_x,
                self.pan_y
            )
            p2 = project_point_to_screen(
                (float(x), 0.0, float(grid_range)),
                proj_matrix,
                self.canvas_width,
                self.canvas_height,
                self.scale,
                self.pan_x,
                self.pan_y
            )
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=col, width=1)

        # Линии, параллельные оси X (при постоянном z)
        for z in range(-grid_range, grid_range + 1, step):
            col = color_sub_axis if z == 0 else color_grid
            p1 = project_point_to_screen(
                (float(-grid_range), 0.0, float(z)),
                proj_matrix,
                self.canvas_width,
                self.canvas_height,
                self.scale,
                self.pan_x,
                self.pan_y
            )
            p2 = project_point_to_screen(
                (float(grid_range), 0.0, float(z)),
                proj_matrix,
                self.canvas_width,
                self.canvas_height,
                self.scale,
                self.pan_x,
                self.pan_y
            )
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=col, width=1)

    def _draw_axes(self, proj_matrix):
        """
        Отрисовывает координатные оси X,Y,Z
        """
        pts = project_points_to_screen(
            self.axes.vertices,
            proj_matrix,
            self.canvas_width,
            self.canvas_height,
            self.scale,
            self.pan_x,
            self.pan_y
        )
        o_x, o_y = pts[0]  # начало координат (0, 0, 0)

        # Ось X
        x_end = pts[1]
        self.canvas.create_line(o_x, o_y, x_end[0], x_end[1], fill="#ef4444", width=2, arrow=tk.LAST)
        self.canvas.create_text(x_end[0] + 10, x_end[1], text="X", fill="#ef4444", font=("Arial", 10, "bold"))

        # Ось Y
        y_end = pts[2]
        self.canvas.create_line(o_x, o_y, y_end[0], y_end[1], fill="#22c55e", width=2, arrow=tk.LAST)
        self.canvas.create_text(y_end[0], y_end[1] - 12, text="Y", fill="#22c55e", font=("Arial", 10, "bold"))

        # Ось Z
        z_end = pts[3]
        self.canvas.create_line(o_x, o_y, z_end[0], z_end[1], fill="#38bdf8", width=2, arrow=tk.LAST)
        self.canvas.create_text(z_end[0] + 10, z_end[1] + 10, text="Z", fill="#38bdf8", font=("Arial", 10, "bold"))

    def _draw_letter(self, proj_matrix):
        """
        Отрисовывает 24 ребра буквы
        """
        pts = project_points_to_screen(
            self.letter.vertices,
            proj_matrix,
            self.canvas_width,
            self.canvas_height,
            self.scale,
            self.pan_x,
            self.pan_y
        )

        for edge_idx, (i, j) in enumerate(self.letter.edges):
            x1, y1 = pts[i]
            x2, y2 = pts[j]

            # Передняя грань
            if edge_idx < 8:
                color = "#dbf838"
                width = 2
            # Задняя грань
            elif edge_idx < 16:
                color = "#9ca701"
                width = 2
            # Продольные ребра
            else:
                color = "#a855f7"
                width = 1

            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

        # Точки на вершинах
        for px, py in pts:
            self.canvas.create_oval(px - 2, py - 2, px + 2, py + 2, fill="#f8fafc", outline="")


    def _draw_animation_point(self, proj_matrix):
        """
        Отрисовывает точку A(a, b, 0), относительно которой идет анимация.
        """
        try:
            # Пытаемся получить значения, пока пользователь печатает
            a = float(self.var_point_a.get())
            b = float(self.var_point_b.get())
        except ValueError:
            return  # Если в полях введены буквы или точки, просто не рисуем маркер

        # Точка лежит в плоскости XOY, поэтому Z = 0
        point_3d = (a, b, 0.0)
        
        # Проецируем 3D-точку в экранные координаты
        screen_x, screen_y = project_point_to_screen(
            point_3d, 
            proj_matrix, 
            self.canvas_width, 
            self.canvas_height, 
            self.scale, 
            self.pan_x, 
            self.pan_y
        )
        
        # Настраиваем стиль маркера (ярко-оранжевый, чтобы контрастировать с буквой и осями)
        color = "#f97316"  
        size = 8
        
        # 1. Рисуем перекрестие
        self.canvas.create_line(screen_x - size, screen_y, screen_x + size, screen_y, fill=color, width=2)
        self.canvas.create_line(screen_x, screen_y - size, screen_x, screen_y + size, fill=color, width=2)
        
        # 2. Рисуем круг вокруг центра
        self.canvas.create_oval(
            screen_x - size, screen_y - size, 
            screen_x + size, screen_y + size, 
            outline=color, width=2
        )


    def _on_canvas_resize(self, event):
        self.canvas_width = event.width
        self.canvas_height = event.height
        self.redraw()


def main():
    root = tk.Tk()
    app = GraphicsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()