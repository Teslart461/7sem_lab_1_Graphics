from matrix import transform_points

class Model:
    """
    Класс модели хранит: вершины (текущие и начальные), рёбра + методы трансфорамации
    """
    def __init__(self, vertices, edges):
        # Базовые исходные координаты
        self.initial_vertices = [tuple(v) for v in vertices]
        # Текущие трансформированные координаты вершин
        self.vertices = [tuple(v) for v in vertices]
        # Список ребер
        self.edges = list(edges)

    def apply_matrix(self, matrix):
        """
        Применяет матрицу преобразования к текущим координатам вершин
        """
        self.vertices = transform_points(self.vertices, matrix)

    def reset(self):
        """
        Возвращает вершины модели в исходное состояние
        """
        self.vertices = [tuple(v) for v in self.initial_vertices]

    def apply_matrix_from(self, base_vertices, matrix):
        """
        Применяет матрицу к переданному базовому состоянию base_vertices
        и записывает результат как текущие вершины.

        Нужен для анимаций: каждый кадр пересчитывает преобразование заново
        от одного и того же опорного состояния (момента запуска анимации),
        а не накапливает его поверх предыдущего кадра.
        """
        self.vertices = transform_points(base_vertices, matrix)

    def snapshot(self):
        """Копия текущих вершин - опорная точка для будущей анимации."""
        return list(self.vertices)


def create_letter_p(width=3.0, height=5.0, thickness=1.0, depth=2.0):
    """
    Генерирует 3D-проволочную модель буквы "П",
    центрированную в начале координат (0, 0, 0)

    Параметры:
      width - общая ширина буквы
      height - общая высота буквы
      thickness - толщина вертикальных стоек и верхней перекладины
      depth - глубина буквы
    """
    d2 = depth / 2.0

    # Внешние границы
    left        = 0.0
    right       = width
    bottom      = 0.0
    top         = height

    # Внутренние границы проёма
    inner_left  = left + thickness      # правая грань левой ножки
    inner_right = right - thickness     # левая грань правой ножки
    inner_top   = top - thickness       # низ перекладины

    # 8 точек 2D-контура буквы "П" (обход по часовой стрелке)
    contour_2d = [
        (left,        bottom),      # 0: низ левой ноги (снаружи)
        (left,        top),         # 1: верх левой ноги (снаружи)
        (right,       top),         # 2: верх правой ноги (снаружи)
        (right,       bottom),      # 3: низ правой ноги (снаружи)
        (inner_right, bottom),      # 4: низ правой ноги (внутри)
        (inner_right, inner_top),   # 5: верх проёма справа
        (inner_left,  inner_top),   # 6: верх проёма слева
        (inner_left,  bottom),      # 7: низ левой ноги (внутри)
    ]

    # Создаем 16 3D-вершин
    # 0..7 - передняя грань
    # 8..15 - задняя грань
    vertices = []
    for x, y in contour_2d:
        vertices.append((x, y, d2))
    for x, y in contour_2d:
        vertices.append((x, y, -d2))

    # Создаем 24 ребра
    edges = []

    # Ребра передней грани
    for i in range(8):
        next_i = (i + 1) % 8
        edges.append((i, next_i))

    # Ребра задней грани
    for i in range(8):
        next_i = (i + 1) % 8
        edges.append((i + 8, next_i + 8))

    # Соединительные ребра между передней и задней гранями
    for i in range(8):
        edges.append((i, i + 8))

    return Model(vertices, edges)


def create_coordinate_axes(length=10.0):
    """
    Создает модель 3D координатных осей:
    Ось X: от (0,0,0) до (length, 0, 0)
    Ось Y: от (0,0,0) до (0, length, 0)
    Ось Z: от (0,0,0) до (0, 0, length)
    """
    vertices = [
        (0.0, 0.0, 0.0),     
        (length, 0.0, 0.0),   
        (0.0, length, 0.0),    
        (0.0, 0.0, length)    
    ]
    edges = [
        (0, 1),  
        (0, 2), 
        (0, 3)   
    ]
    return Model(vertices, edges)