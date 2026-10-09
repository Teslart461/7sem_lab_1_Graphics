import math

def identity_matrix():
    """
    Создает и возвращает единичную матрицу 4x4
    """
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ]


def matrix_multiply(a, b):
    """
    Выполняет матричное умножение двух матриц 4x4: C = A * B
    """
    result = [[0.0] * 4 for _ in range(4)]
    
    for i in range(4):
        for j in range(4):
            total = 0.0
            for k in range(4):
                total += a[i][k] * b[k][j]
            result[i][j] = total   
    return result


def multiply_matrices(*matrices):
    """
    Последовательно перемножает цепочку матриц слева направо
    """
    if not matrices:
        return identity_matrix()
    
    res = matrices[0]
    for m in matrices[1:]:
        res = matrix_multiply(res, m)
    return res


def transform_point(point, m):
    """
    Преобразует 3D-точку (x, y, z) или вектор (x, y, z, w) матрицей 4x4: V* = V * M.
    Возвращает однородные координаты (x*, y*, z*, w*).
    """
    x = point[0]
    y = point[1]
    z = point[2]
    w = point[3] if len(point) > 3 else 1.0

    x_star = x * m[0][0] + y * m[1][0] + z * m[2][0] + w * m[3][0]
    y_star = x * m[0][1] + y * m[1][1] + z * m[2][1] + w * m[3][1]
    z_star = x * m[0][2] + y * m[1][2] + z * m[2][2] + w * m[3][2]
    w_star = x * m[0][3] + y * m[1][3] + z * m[2][3] + w * m[3][3]

    return (x_star, y_star, z_star, w_star)


def transform_point_cartesian(point, m):
    """
    Преобразует точку и возвращает 3D декартовы координаты (x*/w*, y*/w*, z*/w*)
    """
    x_s, y_s, z_s, w_s = transform_point(point, m)
    if abs(w_s) > 1e-9:
        return (x_s / w_s, y_s / w_s, z_s / w_s)
    return (x_s, y_s, z_s)


def transform_points(points, m):
    """
    Преобразует список вершин матрицей M с переходом в декартовы координаты
    """
    return [transform_point_cartesian(pt, m) for pt in points]


def translation_matrix(dx, dy, dz):
    """
    Матрица переноса
    """
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [dx,  dy,  dz,  1.0]
    ]


def scaling_matrix(sx, sy, sz):
    """
    Матрица растяжения (сжатия)
    """
    return [
        [sx,  0.0, 0.0, 0.0],
        [0.0, sy,  0.0, 0.0],
        [0.0, 0.0, sz,  0.0],
        [0.0, 0.0, 0.0, 1.0]
    ]


def rotation_x_matrix(angle_rad):
    """
    Матрица вращения вокруг оси абсцисс (X)
    """
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0,  c,   s,  0.0],
        [0.0, -s,   c,  0.0],
        [0.0, 0.0, 0.0, 1.0]
    ]


def rotation_y_matrix(angle_rad):
    """
    Матрица вращения вокруг оси ординат (Y)
    """
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return [
        [ c,   0.0, -s,  0.0],
        [0.0,  1.0, 0.0, 0.0],
        [ s,   0.0,  c,  0.0],
        [0.0,  0.0, 0.0, 1.0]
    ]


def rotation_z_matrix(angle_rad):
    """
    Матрица вращения вокруг оси аппликат (Z)
    """
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return [
        [ c,   s,   0.0, 0.0],
        [-s,   c,   0.0, 0.0],
        [0.0, 0.0,  1.0, 0.0],
        [0.0, 0.0,  0.0, 1.0]
    ]


def reflection_xy_matrix():
    """
    Матрица отражения относительно плоскости XY
    Инвертирует знак координаты Z.
    """
    return [
        [1.0, 0.0,  0.0, 0.0],
        [0.0, 1.0,  0.0, 0.0],
        [0.0, 0.0, -1.0, 0.0],
        [0.0, 0.0,  0.0, 1.0]
    ]


def reflection_xz_matrix():
    """
    Матрица отражения относительно плоскости XZ
    Инвертирует знак координаты Y
    """
    return [
        [1.0,  0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 0.0],
        [0.0,  0.0, 1.0, 0.0],
        [0.0,  0.0, 0.0, 1.0]
    ]


def reflection_yz_matrix():
    """
    Матрица отражения относительно плоскости YZ
    Инвертирует знак координаты X
    """
    return [
        [-1.0, 0.0, 0.0, 0.0],
        [ 0.0, 1.0, 0.0, 0.0],
        [ 0.0, 0.0, 1.0, 0.0],
        [ 0.0, 0.0, 0.0, 1.0]
    ]


def scale_about_point_matrix(a, b, kx, ky):
    """
    Матрица масштабирования в плоскости XOY относительно произвольной точки
    A(a, b) с коэффициентами kx (по X) и ky (по Y).

    Строится как суперпозиция трёх элементарных преобразований:
        1) перенос T(-a, -b, 0) - совмещаем точку A с началом координат
        2) масштабирование D(kx, ky, 1)
        3) перенос T(a, b, 0) - возвращаем центр растяжения на место
    """
    t1 = translation_matrix(-a, -b, 0.0)
    d = scaling_matrix(kx, ky, 1.0)
    t2 = translation_matrix(a, b, 0.0)
    return multiply_matrices(t1, d, t2)