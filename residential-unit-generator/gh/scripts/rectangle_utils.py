from dataclasses import dataclass, field


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float
    name: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def x0(self):
        return self.x

    @property
    def y0(self):
        return self.y

    @property
    def x1(self):
        return self.x + self.w

    @property
    def y1(self):
        return self.y + self.h

    @property
    def area(self):
        return self.w * self.h

    @property
    def center(self):
        return (self.x + self.w / 2.0, self.y + self.h / 2.0)

    @property
    def aspect_ratio(self):
        short = min(self.w, self.h)
        if short <= 1e-9:
            return float("inf")
        return max(self.w, self.h) / short

    @property
    def polygon(self):
        return [
            (self.x, self.y),
            (self.x1, self.y),
            (self.x1, self.y1),
            (self.x, self.y1),
        ]

    def copy(self, **overrides):
        values = {
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "name": self.name,
            "metadata": dict(self.metadata),
        }
        values.update(overrides)
        return Rect(**values)

    def overlaps(self, other, tol=1e-6):
        return not (
            self.x1 <= other.x0 + tol
            or other.x1 <= self.x0 + tol
            or self.y1 <= other.y0 + tol
            or other.y1 <= self.y0 + tol
        )


def split_horizontal(rect: Rect, left_ratio: float, tol=1e-6):
    if not 1e-6 < left_ratio < 1 - 1e-6:
        raise ValueError("left_ratio must be strictly between 0 and 1")
    left_w = rect.w * left_ratio
    right_w = rect.w - left_w
    return rect.copy(w=left_w), rect.copy(x=rect.x + left_w, w=right_w)


def split_vertical(rect: Rect, top_ratio: float, tol=1e-6):
    if not 1e-6 < top_ratio < 1 - 1e-6:
        raise ValueError("top_ratio must be strictly between 0 and 1")
    top_h = rect.h * top_ratio
    bottom_h = rect.h - top_h
    return rect.copy(h=top_h), rect.copy(y=rect.y + top_h, h=bottom_h)


def choose_split_direction(rect: Rect, max_aspect_ratio: float = 3.2):
    if rect.aspect_ratio >= max_aspect_ratio:
        return "vertical"
    return "horizontal"


def is_adjacent(rect_a: Rect, rect_b: Rect, tol=0.01):
    same_x = abs(rect_a.x1 - rect_b.x0) <= tol or abs(rect_b.x1 - rect_a.x0) <= tol
    same_y = abs(rect_a.y1 - rect_b.y0) <= tol or abs(rect_b.y1 - rect_a.y0) <= tol
    return (same_x and rect_a.y1 > rect_b.y0 + tol and rect_b.y1 > rect_a.y0 + tol) or (
        same_y and rect_a.x1 > rect_b.x0 + tol and rect_b.x1 > rect_a.x0 + tol
    )
