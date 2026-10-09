import math
from matrix import scale_about_point_matrix

def ease_in_out(t):
    return 0.5 - 0.5*math.cos(math.pi*t)

def ease_out_cubic(t):
    return 1.0 - (1.0-t)**3

def build_scale_about_point_frames(kx_target, ky_target, frames_forward=30, frames_hold=15, frames_back=60):
    frames = []
    for i in range(frames_forward):
        t = ease_in_out(i/(frames_forward-1))
        frames.append((1.0+(kx_target-1.0)*t, 1.0+(ky_target-1.0)*t))
    frames += [(kx_target, ky_target)]*frames_hold
    for i in range(frames_back):
        t = ease_out_cubic(i/(frames_back-1))
        frames.append((kx_target+(1.0-kx_target)*t, ky_target+(1.0-ky_target)*t))
    return frames


class ScaleAboutPointAnimation:
    """Масштаб относительно точки A(a,b) в плоскости XOY, с плавным замедляющимся возвратом."""
    def __init__(self, model, point, kx, ky, frames_forward=30, frames_hold=15, frames_back=60, on_finish=None):
        self.model = model
        self.a, self.b = point
        self.frames = build_scale_about_point_frames(kx, ky, frames_forward, frames_hold, frames_back)
        self.base_vertices = model.snapshot()
        self.index = 0
        self.on_finish = on_finish

    def is_running(self):
        return self.index < len(self.frames)

    def step(self):
        if not self.is_running():
            return False
        kx, ky = self.frames[self.index]
        m = scale_about_point_matrix(self.a, self.b, kx, ky)
        self.model.apply_matrix_from(self.base_vertices, m)
        self.index += 1
        if not self.is_running():
            self.model.vertices = [tuple(v) for v in self.base_vertices]
            if self.on_finish:
                self.on_finish()
        return True