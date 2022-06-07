from manim import *
from functions import *
from reducible_colors import *
from typing import Iterable, List, Sequence


class Pixel(Square):
    def __init__(self, n, color_mode: str, outline=True):
        assert color_mode in ("RGB", "GRAY"), "Color modes are RGB and GRAY"

        if color_mode == "RGB":
            color = rgb_to_hex(n / 255)
        else:
            if isinstance(n, np.int16) or n < 0:
                n = abs(n)
            color = g2h(n / 255)

        super().__init__(side_length=1)
        if outline:
            self.set_stroke(BLACK, width=0.2)

        else:
            self.set_stroke(color, width=0.2)

        self.set_fill(color, opacity=1)
        self.color = color


class PixelArray(VGroup):
    def __init__(
        self,
        img: np.ndarray,
        include_numbers=False,
        color_mode="RGB",
        buff=0,
        outline=True,
    ):
        self.img = img
        if len(img.shape) == 3:
            rows, cols, channels = img.shape
        else:
            rows, cols = img.shape

        self.shape = img.shape

        self.pixels = VGroup()
        self.numbers = VGroup()
        for row in img:
            for p in row:
                if include_numbers:
                    number = (
                        Text(str(p), font="SF Mono", weight=MEDIUM)
                        .scale(0.7)
                        .set_color(g2h(1) if abs(p) < 180 else g2h(0))
                        .set_stroke(opacity=0)
                    )

                    self.numbers.add(number)

                    new_pix = VGroup(Pixel(p, color_mode, outline=outline), number)
                    if p < 0:
                        new_pix[1].scale(0.8)

                    self.pixels.add(new_pix)
                else:
                    self.pixels.add(Pixel(p, color_mode, outline=outline))

        super().__init__(*self.pixels)
        self.arrange_in_grid(rows, cols, buff=buff)

        self.dict = {index: p for index, p in enumerate(self)}

    def __getitem__(self, value) -> VGroup:
        if isinstance(value, slice):
            return VGroup(*list(self.dict.values())[value])
        elif isinstance(value, tuple):
            i, j = value
            one_d_index = get_1d_index(i, j, self.img)
            return self.dict[one_d_index]
        else:
            return self.dict[value]


class Byte(VGroup):
    def __init__(
        self,
        text,
        stroke_color=REDUCIBLE_VIOLET,
        stroke_width=5,
        text_scale=0.5,
        h_buff=MED_SMALL_BUFF + SMALL_BUFF,
        v_buff=MED_SMALL_BUFF,
        width=6,
        height=1.5,
        edge_buff=1,
        **kwargs,
    ):

        self.h_buff = h_buff
        self.text_scale = text_scale
        self.rect = Rectangle(height=height, width=width).set_stroke(
            width=stroke_width, color=stroke_color
        )

        if isinstance(text, list):
            text_mobs = []
            for string in text:
                text_mobs.append(self.get_text_mob(string))
            self.text = VGroup(*text_mobs).arrange(DOWN, buff=v_buff)
        else:
            self.text = self.get_text_mob(text)

        self.text.move_to(self.rect.get_center())
        self.text.scale_to_fit_width(self.rect.width - edge_buff)
        super().__init__(self.rect, self.text, **kwargs)

    def get_text_mob(self, string):
        text = VGroup(
            *[
                Text(c, font="SF Mono", weight=MEDIUM).scale(self.text_scale)
                for c in string.split(",")
            ]
        )
        text.arrange(RIGHT, buff=self.h_buff)
        return text


class RGBMob:
    def __init__(self, r_mob, g_mob, b_mob):
        self.r = r_mob
        self.g = g_mob
        self.b = b_mob
        self.indicated = False
        self.surrounded = None
        self.scaled = 1
        self.shift = ORIGIN

    def __str__(self):
        return f"RGB(R: {self.r[1].original_text}, G: {self.g[1].original_text}, B: {self.b[1].original_text}, Indicated: {self.indicated}, Surrounded: {self.surrounded[0] if self.surrounded is not None else None}, Scale: {self.scaled}, Shift: {self.shift})"

    def __repr__(self):
        return self.__str__()


string_to_mob_map = {}


class RDecimalNumber(DecimalNumber):
    def set_submobjects_from_number(self, number):
        self.number = number
        self.submobjects = []

        num_string = self.get_num_string(number)
        self.add(*(map(self.string_to_mob, num_string)))

        # Add non-numerical bits
        if self.show_ellipsis:
            self.add(
                self.string_to_mob("\\dots", Text, color=self.color),
            )

        if self.unit is not None:
            self.unit_sign = self.string_to_mob(self.unit, Text)
            self.add(self.unit_sign)

        self.arrange(
            buff=self.digit_buff_per_font_unit * self._font_size,
            aligned_edge=DOWN,
        )

        # Handle alignment of parts that should be aligned
        # to the bottom
        for i, c in enumerate(num_string):
            if c == "-" and len(num_string) > i + 1:
                self[i].align_to(self[i + 1], UP)
                self[i].shift(self[i + 1].height * DOWN / 2)
            elif c == ",":
                self[i].shift(self[i].height * DOWN / 2)
        if self.unit and self.unit.startswith("^"):
            self.unit_sign.align_to(self, UP)

        # track the initial height to enable scaling via font_size
        self.initial_height = self.height

        if self.include_background_rectangle:
            self.add_background_rectangle()

    def string_to_mob(self, string, mob_class=Text, **kwargs):
        if string not in string_to_mob_map:
            string_to_mob_map[string] = mob_class(
                string, font_size=1.0, font="SF Mono", weight=MEDIUM, **kwargs
            )
        mob = string_to_mob_map[string].copy()
        mob.font_size = self._font_size
        return mob


class RVariable(VMobject):
    def __init__(
        self, var, label, var_type=RDecimalNumber, num_decimal_places=2, **kwargs
    ):

        self.label = (
            Text(label, font="SF Mono", weight=MEDIUM)
            if isinstance(label, str)
            else label
        )
        equals = Text("=").next_to(self.label, RIGHT)
        self.label.add(equals)

        self.tracker = ValueTracker(var)

        self.value = RDecimalNumber(
            self.tracker.get_value(), num_decimal_places=num_decimal_places
        )

        self.value.add_updater(lambda v: v.set_value(self.tracker.get_value())).next_to(
            self.label,
            RIGHT,
        )

        super().__init__(**kwargs)
        self.add(self.label, self.value)


class Module(VGroup):
    def __init__(
        self,
        text,
        fill_color=REDUCIBLE_PURPLE_DARKER,
        stroke_color=REDUCIBLE_VIOLET,
        stroke_width=5,
        text_scale=0.9,
        text_position=ORIGIN,
        text_weight=NORMAL,
        width=4,
        height=2,
        **kwargs,
    ):

        self.rect = (
            RoundedRectangle(
                corner_radius=0.1, fill_color=fill_color, width=width, height=height
            )
            .set_opacity(1)
            .set_stroke(stroke_color, width=stroke_width)
        )
        if isinstance(text, list):
            text_mob = VGroup()
            for string in text:
                text = Text(str(string), weight=text_weight, font="CMU Serif").scale(
                    text_scale
                )
                text_mob.add(text)
            self.text = text_mob.arrange(DOWN, buff=SMALL_BUFF * 2)
        else:
            self.text = Text(str(text), weight=text_weight, font="CMU Serif").scale(
                text_scale
            )
        self.text.next_to(
            self.rect,
            direction=ORIGIN,
            coor_mask=text_position * 0.8,
            aligned_edge=text_position,
        )

        super().__init__(self.rect, self.text, **kwargs)
        # super().arrange(ORIGIN)


class Node:
    def __init__(self, freq, key=""):
        self.freq = freq
        self.key = key
        self.left = None
        self.right = None

    def __repr__(self):
        return "Node(freq={0}, key={1})".format(self.freq, self.key)

    def __lt__(self, other):
        return self.freq < other.freq

    def __gt__(self, other):
        return self.freq > other.freq

    def generate_mob(
        self,
        text_scale=0.6,
        radius=0.5,
        is_leaf=False,
        key_scale=None,
        key_color=PURE_BLUE,
    ):
        # geometry is first, then text mobject
        # characters will be handled with separate geometry
        # nodes that are parents will have keys that concatenate the childs
        # since huffman trees are full binary trees, guaranteed to be not length 1
        if len(self.key) > 3 and not is_leaf:
            self.is_leaf = False
            freq = Text(str(self.freq), font="SF Mono", weight=MEDIUM).scale(text_scale)
            node = Circle(radius=radius).set_color(REDUCIBLE_VIOLET)
            node.set_fill(color=REDUCIBLE_PURPLE_DARKER, opacity=1)
            freq.move_to(node.get_center())
            self.mob = VGroup(node, freq)
            self.heap_mob = self.mob
            return self.mob
        # two rectangles, top is frequency, bottom is key
        self.is_leaf = True
        freq_box = Rectangle(height=0.5, width=1).set_color(REDUCIBLE_GREEN_LIGHTER)
        freq_box.set_fill(color=REDUCIBLE_GREEN_DARKER, opacity=1)
        freq_interior = Text(str(self.freq), font="SF Mono", weight=MEDIUM).scale(
            text_scale - SMALL_BUFF
        )
        freq_interior.move_to(freq_box.get_center())
        freq = VGroup(freq_box, freq_interior)
        key_box = (
            Rectangle(height=1, width=1)
            .set_color(REDUCIBLE_VIOLET)
            .set_fill(color=key_color, opacity=1)
        )
        key_interior = Text(self.key, font="SF Mono", weight=MEDIUM).scale(text_scale)
        if key_scale:
            key_interior.scale(key_scale)
        key_interior.move_to(key_box.get_center())
        key = VGroup(key_box, key_interior)
        self.mob = VGroup(freq, key).arrange(DOWN, buff=0)
        return self.mob

    def connect_node(self, child, left=True):
        if left:
            self.left = child
        else:
            self.right = child


class ReducibleLabel(Text):
    def __init__(self, label, font="SF Mono", scale=1, weight=MEDIUM):
        super().__init__(label, font=font, weight=weight)
        self.scale(scale)


class ReducibleBarChart(BarChart):
    """
    Redefinition of the BarChart class to add font personalization
    """

    def __init__(
        self,
        values: Iterable[float],
        bar_names: Iterable[str] = None,
        y_range: Sequence[float] = None,
        x_length: float = None,
        y_length: float = ...,
        bar_colors: Iterable[str] = ...,
        bar_width: float = 0.6,
        bar_fill_opacity: float = 0.7,
        bar_stroke_width: float = 3,
        **kwargs,
    ):
        super().__init__(
            values,
            bar_names,
            y_range,
            x_length,
            y_length,
            bar_colors,
            bar_width,
            bar_fill_opacity,
            bar_stroke_width,
            **kwargs,
        )

        print(super().super())


class ReducibleAxes(Axes):
    def __init__(
        self,
        x_range: Sequence[float] = None,
        y_range: Sequence[float] = None,
        x_length: float = 6,
        y_length: float = 3,
        axis_config: dict = {"include_numbers": True, "font_size": 12},
        x_axis_config: dict = {"label_constructor": ReducibleLabel},
        y_axis_config: dict = {"label_constructor": ReducibleLabel},
        tips: bool = False,
        **kwargs,
    ):
        super().__init__(
            x_range,
            y_range,
            x_length,
            y_length,
            axis_config,
            x_axis_config,
            y_axis_config,
            tips,
            **kwargs,
        )


class Test(Scene):
    def construct(self):
        ax = ReducibleAxes().scale(0.5).to_edge(LEFT)
        bar = (
            BarChart(
                values=[4, 5, 6, 7, 8],
                bar_names=["a", "b", "c", "d", "e"],
                axis_configuration={
                    "label_constructor": ReducibleLabel,
                },
            )
            .scale(0.5)
            .to_edge(RIGHT)
        )
        # a = ReducibleBarChart(
        #     values=[4, 5, 6, 7, 8],
        #     bar_names=["a", "b", "c", "d", "e"],
        #     label_constructor=ReducibleLabel,
        # )
        self.add(ax, bar)
