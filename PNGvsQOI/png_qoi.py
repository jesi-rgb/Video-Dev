from math import floor
from manim import *
from manim.mobject.geometry import ArrowTriangleFilledTip
from numpy import ndarray
from functions import *
from classes import *
from reducible_colors import *

np.random.seed(1)

config["assets_dir"] = "assets"

QOI_INDEX = 0
QOI_DIFF_SMALL = 1
QOI_DIFF_MED = 2
QOI_RUN = 3
QOI_RGB = 4


class QOIDemo(Scene):
    def construct(self):
        """
        Plan for animation
        1. Show RGB Image pixel representation
        2. Split RGB Image into R, G, and B channels
        3. Show 5 different compression options (keep RGB, run, index, diff small, diff large)
        4. Make a function that takes image and generates QOI tags -- TEST ON DIFFS (seems to work)
        5. Make function to take a list of encoding options (with necessary data)
        and demo QOI
        In demo, make functional example of a full encoding with list, show the entire bitsteam (can shift info out of the window)

        """
        self.show_image()

    def show_image(self):
        image = ImageMobject("r.png")
        pixel_array = image.get_pixel_array().astype(int)
        pixel_array_mob = PixelArray(pixel_array).scale(0.4).shift(UP * 2)
        self.play(FadeIn(pixel_array_mob))
        self.wait()

        flattened_pixels = self.show_rgb_split(pixel_array, pixel_array_mob)
        self.introduce_qoi_tags(flattened_pixels)
        qoi_data = self.get_qoi_encoding(pixel_array)
        print("QOI_ENCODING:\n", qoi_data)

    def get_qoi_encoding(self, pixel_array):
        """
        @param: pixel_array - np.array[r, g, b] representing pixels of image
        @return: list[] containing QOI encodings for image
        each QOI encoding is a tuple of
        """
        INDEX_SIZE = 64
        r_channel = pixel_array[:, :, 0]
        g_channel = pixel_array[:, :, 1]
        b_channel = pixel_array[:, :, 2]

        prev_rgb = [0, 0, 0]

        encodings = []
        indices = [[0, 0, 0]] * INDEX_SIZE
        run = 0
        for row in range(r_channel.shape[0]):
            for col in range(r_channel.shape[1]):
                current_rgb = [
                    r_channel[row][col],
                    g_channel[row][col],
                    b_channel[row][col],
                ]
                if prev_rgb == current_rgb:
                    run += 1
                    if run == 62 or is_last_pixel(r_channel, row, col):
                        encodings.append((QOI_RUN, run))
                        run = 0
                else:
                    index_pos = 0
                    if run > 0:
                        encodings.append((QOI_RUN, run))
                        run = 0

                    index_pos = qoi_hash(current_rgb) % INDEX_SIZE
                    if indices[index_pos] == current_rgb:
                        encodings.append((QOI_INDEX, index_pos))
                    else:
                        indices[index_pos] = current_rgb

                        dr = current_rgb[0] - prev_rgb[0]
                        dg = current_rgb[1] - prev_rgb[1]
                        db = current_rgb[2] - prev_rgb[2]

                        dr_dg = dr - dg
                        db_dg = db - dg

                        if is_diff_small(dr, dg, db):
                            encodings.append((QOI_DIFF_SMALL, dr, dg, db))
                        elif is_diff_med(dg, dr_dg, db_dg):
                            encodings.append((QOI_DIFF_MED, dg, dr_dg, db_dg))
                        else:
                            encodings.append(
                                (
                                    QOI_RGB,
                                    current_rgb[0],
                                    current_rgb[1],
                                    current_rgb[2],
                                )
                            )

                prev_rgb = current_rgb

        print("INDEX:\n", indices)
        return encodings

    def animate_encoding_of_qoi(pixel_array):
        pass

    def introduce_qoi_tags(self, flattened_pixels):
        r_channel, g_channel, b_channel = flattened_pixels
        rgb_pixels = self.get_rgb_pixels(r_channel, g_channel, b_channel)

        indices = [50, 51, 52]
        self.bring_pixel_to_screen(indices[0], flattened_pixels)
        transforms = self.get_indication_transforms(indices, rgb_pixels)
        self.play(*transforms)
        self.wait()

        transforms = self.get_indication_transforms([43], rgb_pixels)
        self.play(
            *transforms,
        )
        self.wait()

        reset_animations = self.reset_indications(rgb_pixels)
        self.play(*reset_animations)
        self.wait()

    def get_indication_transforms(self, indices, rgb_pixels, opacity=0.2):
        indication_transforms = []
        all_other_indices = [
            index for index in range(len(rgb_pixels)) if index not in indices
        ]
        for index in all_other_indices:
            animations = []
            pixel = rgb_pixels[index]
            if pixel.indicated:
                continue
            faded_pixels = self.get_faded_pixels(pixel, opacity=opacity)
            animations.extend(
                [
                    Transform(pixel.r, faded_pixels[0]),
                    Transform(pixel.g, faded_pixels[1]),
                    Transform(pixel.b, faded_pixels[2]),
                ]
            )
            indication_transforms.extend(animations)

        animations = []
        pixels = [rgb_pixels[index] for index in indices]
        for pixel in pixels:
            pixel.indicated = True
        indicated_pixels = self.get_indicated_pixels(pixels)
        surrounded_rects = self.get_surrounded_rects(indicated_pixels)
        pixels[0].surrounded = VGroup(*surrounded_rects)
        animations.extend(self.get_scale_transforms(pixels, indicated_pixels))
        animations.extend(
            [
                FadeIn(surrounded_rects[0]),
                FadeIn(surrounded_rects[1]),
                FadeIn(surrounded_rects[2]),
            ]
        )
        indication_transforms.extend(animations)

        return indication_transforms

    def get_scale_transforms(self, pixels, indicated_pixels):
        transforms = []
        for i, pixel in enumerate(pixels):
            transforms.append(Transform(pixel.r, indicated_pixels[0][i]))
            transforms.append(Transform(pixel.g, indicated_pixels[1][i]))
            transforms.append(Transform(pixel.b, indicated_pixels[2][i]))

        return transforms

    def get_faded_pixels(self, pixel, opacity=0.2):
        r_pixel = self.get_faded_pixel(pixel.r, opacity=opacity)
        g_pixel = self.get_faded_pixel(pixel.g, opacity=opacity)
        b_pixel = self.get_faded_pixel(pixel.b, opacity=opacity)
        return [r_pixel, g_pixel, b_pixel]

    def get_indicated_pixels(self, pixels, scale=1.2, shift=SMALL_BUFF, direction=UP):
        r_pixel = VGroup(
            *[
                self.get_indicated_pixel(
                    pixel.r, scale=scale, shift=shift, direction=direction
                )
                for pixel in pixels
            ]
        )
        g_pixel = VGroup(
            *[
                self.get_indicated_pixel(
                    pixel.g, scale=scale, shift=shift, direction=direction
                )
                for pixel in pixels
            ]
        )
        b_pixel = VGroup(
            *[
                self.get_indicated_pixel(
                    pixel.b, scale=scale, shift=shift, direction=direction
                )
                for pixel in pixels
            ]
        )
        return [r_pixel, g_pixel, b_pixel]

    def get_surrounded_rects(self, indicated_pixels):
        return [get_glowing_surround_rect(pixel) for pixel in indicated_pixels]

    def get_indicated_pixel(self, channel, scale=1.2, shift=SMALL_BUFF, direction=UP):
        pixel = channel.copy()
        pixel = self.get_faded_pixel(pixel, opacity=1)
        pixel.scale(scale).shift(direction * shift)
        return pixel

    def get_faded_pixel(self, channel, opacity=0.2):
        pixel = channel.copy()
        pixel[0].set_fill(opacity=opacity).set_stroke(opacity=opacity)
        pixel[1].set_fill(opacity=opacity)
        return pixel

    def get_rgb_pixels(self, r_channel, b_channel, g_channel):
        pixels = []
        for i in range(len(r_channel[1])):
            r_mob = VGroup(r_channel[0][0, i], r_channel[1][i])
            g_mob = VGroup(g_channel[0][0, i], g_channel[1][i])
            b_mob = VGroup(b_channel[0][0, i], b_channel[1][i])
            pixels.append(RGBMob(r_mob, g_mob, b_mob))

        return pixels

    def reset_indications(self, rgb_pixels):
        animations = []
        for i, pixel in enumerate(rgb_pixels):
            if pixel.indicated:
                if pixel.surrounded:
                    animations.append(FadeOut(pixel.surrounded))
                    pixel.surrounded = None
                original_pixel = self.get_indicated_pixels(
                    [pixel], scale=1 / 1.2, direction=DOWN
                )
                animations.append(Transform(pixel.r, original_pixel[0][0]))
                animations.append(Transform(pixel.g, original_pixel[1][0]))
                animations.append(Transform(pixel.b, original_pixel[2][0]))
                pixel.indicated = False
            else:
                original_pixel = self.get_faded_pixels(pixel, opacity=1)
                animations.append(Transform(pixel.r, original_pixel[0]))
                animations.append(Transform(pixel.g, original_pixel[1]))
                animations.append(Transform(pixel.b, original_pixel[2]))

        return animations

    def bring_pixel_to_screen(self, index, flattened_pixels, target_x_pos=0):
        r_channel = flattened_pixels[0]
        target_pixel = r_channel[0][index]
        shift_amount = self.get_shift_amount(
            target_pixel.get_center(), target_x_pos=target_x_pos
        )
        if not np.array_equal(shift_amount, ORIGIN):
            self.play(flattened_pixels.animate.shift(shift_amount))
            self.wait()

    def get_shift_amount(self, position, target_x_pos=0):
        x_pos = position[0]
        print(x_pos)
        BUFF = 1
        if (
            x_pos > -config.frame_x_radius + BUFF
            and x_pos < config.frame_x_radius - BUFF
        ):
            # NO Shift needed
            return ORIGIN

        return (target_x_pos - x_pos) * RIGHT

    def show_rgb_split(self, pixel_array, pixel_array_mob):
        r_channel = pixel_array[:, :, 0]
        g_channel = pixel_array[:, :, 1]
        b_channel = pixel_array[:, :, 2]

        r_channel_padded = self.get_channel_image(r_channel)
        g_channel_padded = self.get_channel_image(g_channel, mode="G")
        b_channel_padded = self.get_channel_image(b_channel, mode="B")

        pixel_array_mob_r = (
            PixelArray(r_channel_padded).scale(0.4).shift(LEFT * 4 + DOWN * 1.5)
        )
        pixel_array_mob_g = PixelArray(g_channel_padded).scale(0.4).shift(DOWN * 1.5)
        pixel_array_mob_b = (
            PixelArray(b_channel_padded).scale(0.4).shift(RIGHT * 4 + DOWN * 1.5)
        )

        self.play(
            TransformFromCopy(pixel_array_mob, pixel_array_mob_r),
            TransformFromCopy(pixel_array_mob, pixel_array_mob_b),
            TransformFromCopy(pixel_array_mob, pixel_array_mob_g),
        )
        self.wait()

        r_channel_pixel_text = self.get_pixel_values(r_channel, pixel_array_mob_r)
        g_channel_pixel_text = self.get_pixel_values(
            g_channel, pixel_array_mob_g, mode="G"
        )
        b_channel_pixel_text = self.get_pixel_values(
            b_channel, pixel_array_mob_b, mode="B"
        )
        self.play(
            FadeIn(r_channel_pixel_text),
            FadeIn(g_channel_pixel_text),
            FadeIn(b_channel_pixel_text),
        )
        self.wait()

        self.play(
            FadeOut(pixel_array_mob),
            pixel_array_mob_r.animate.shift(UP * 3),
            pixel_array_mob_b.animate.shift(UP * 3),
            pixel_array_mob_g.animate.shift(UP * 3),
            r_channel_pixel_text.animate.shift(UP * 3),
            g_channel_pixel_text.animate.shift(UP * 3),
            b_channel_pixel_text.animate.shift(UP * 3),
        )
        self.wait()

        r_channel_flattened = self.reshape_channel(r_channel_padded)
        g_channel_flattened = self.reshape_channel(g_channel_padded)
        b_channel_flattened = self.reshape_channel(b_channel_padded)

        r_channel_f_mob = (
            PixelArray(r_channel_flattened, buff=MED_SMALL_BUFF, outline=False)
            .scale(0.6)
            .to_edge(LEFT)
        )
        g_channel_f_mob = (
            PixelArray(g_channel_flattened, buff=MED_SMALL_BUFF, outline=False)
            .scale(0.6)
            .to_edge(LEFT)
        )
        b_channel_f_mob = (
            PixelArray(b_channel_flattened, buff=MED_SMALL_BUFF, outline=False)
            .scale(0.6)
            .to_edge(LEFT)
        )

        r_channel_f_mob.to_edge(LEFT).shift(DOWN * 1.1)
        g_channel_f_mob.next_to(r_channel_f_mob, DOWN * 2, aligned_edge=LEFT)
        b_channel_f_mob.next_to(g_channel_f_mob, DOWN * 2, aligned_edge=LEFT)

        r_channel_f_mob_text = self.get_pixel_values(
            r_channel_flattened[:, :, 0], r_channel_f_mob, mode="R"
        )
        g_channel_f_mob_text = self.get_pixel_values(
            g_channel_flattened[:, :, 1], g_channel_f_mob, mode="G"
        )
        b_channel_f_mob_text = self.get_pixel_values(
            b_channel_flattened[:, :, 2], b_channel_f_mob, mode="B"
        )

        r_transforms = self.get_flatten_transform(
            pixel_array_mob_r,
            r_channel_f_mob,
            r_channel_pixel_text,
            r_channel_f_mob_text,
        )

        g_transforms = self.get_flatten_transform(
            pixel_array_mob_g,
            g_channel_f_mob,
            g_channel_pixel_text,
            g_channel_f_mob_text,
        )

        b_transforms = self.get_flatten_transform(
            pixel_array_mob_b,
            b_channel_f_mob,
            b_channel_pixel_text,
            b_channel_f_mob_text,
        )

        self.play(*r_transforms, run_time=3)
        self.wait()

        self.play(*g_transforms, run_time=3)
        self.wait()

        self.play(*b_transforms, run_time=3)
        self.wait()

        self.play(
            FadeOut(pixel_array_mob_r),
            FadeOut(pixel_array_mob_g),
            FadeOut(pixel_array_mob_b),
            FadeOut(r_channel_pixel_text),
            FadeOut(g_channel_pixel_text),
            FadeOut(b_channel_pixel_text),
            r_channel_f_mob.animate.shift(UP * 2.5),
            g_channel_f_mob.animate.shift(UP * 2.5),
            b_channel_f_mob.animate.shift(UP * 2.5),
            r_channel_f_mob_text.animate.shift(UP * 2.5),
            g_channel_f_mob_text.animate.shift(UP * 2.5),
            b_channel_f_mob_text.animate.shift(UP * 2.5),
        )
        self.wait()

        r_channel = VGroup(r_channel_f_mob, r_channel_f_mob_text)
        g_channel = VGroup(g_channel_f_mob, g_channel_f_mob_text)
        b_channel = VGroup(b_channel_f_mob, b_channel_f_mob_text)

        return VGroup(r_channel, g_channel, b_channel)

        # qoi_rgb_bytes = self.get_rbg_bytes().move_to(DOWN * 2)
        # self.add(qoi_rgb_bytes)
        # self.wait()
        # self.remove(qoi_rgb_bytes)

        # qoi_index_bytes = self.get_index_bytes().move_to(DOWN * 2)
        # self.add(qoi_index_bytes)
        # self.wait()

        # self.remove(qoi_index_bytes)

        # qoi_run_bytes = self.get_run_bytes().move_to(DOWN * 2)
        # self.add(qoi_run_bytes)
        # self.wait()

        # self.remove(qoi_run_bytes)

        # qoi_large_diff_bytes = self.get_large_diff_bytes().move_to(DOWN * 2)
        # self.add(qoi_large_diff_bytes)
        # self.wait()

        # self.remove(qoi_large_diff_bytes)
        # qoi_small_diff_bytes = self.get_small_diff_bytes().move_to(DOWN * 2)
        # self.add(qoi_small_diff_bytes)
        # self.wait()

        # self.remove(qoi_small_diff_bytes)
        # self.wait()

    def get_rbg_bytes(self):
        rgb_tag_byte = Byte(["Byte[0]", "7,6,5,4,3,2,1,0"]).scale(0.5).move_to(DOWN * 2)

        red_first_byte = Byte(
            ["Byte[1]", "7,...,0"], width=2, height=rgb_tag_byte.height
        )

        red_first_byte.text.scale_to_fit_height(rgb_tag_byte.text.height)

        red_first_byte.next_to(rgb_tag_byte, RIGHT, buff=0)

        green_second_byte = Byte(
            ["Byte[2]", "7,...,0"],
            width=red_first_byte.width,
            height=rgb_tag_byte.height,
        )

        green_second_byte.text.scale_to_fit_height(red_first_byte.text.height)

        green_second_byte.next_to(red_first_byte, RIGHT, buff=0)

        blue_third_byte = Byte(
            ["Byte[3]", "7,...,0"],
            width=red_first_byte.width,
            height=rgb_tag_byte.height,
        )

        blue_third_byte.text.scale_to_fit_height(red_first_byte.text.height)

        blue_third_byte.next_to(green_second_byte, RIGHT, buff=0)

        tag_value = Byte(
            "8 bit RGB_TAG",
            width=rgb_tag_byte.width,
            height=rgb_tag_byte.height,
            text_scale=0.25,
        )

        tag_value.next_to(rgb_tag_byte, DOWN, buff=0)

        red_value = Byte(
            "Red",
            width=red_first_byte.width,
            height=red_first_byte.height,
            text_scale=0.25,
        ).next_to(red_first_byte, DOWN, buff=0)
        red_value.text.scale_to_fit_height(tag_value.text.height)

        green_value = Byte(
            "Green",
            width=green_second_byte.width,
            height=green_second_byte.height,
            text_scale=0.25,
        ).next_to(green_second_byte, DOWN, buff=0)
        green_value.text.scale_to_fit_height(tag_value.text.height)

        blue_value = Byte(
            "Blue",
            width=blue_third_byte.width,
            height=blue_third_byte.height,
            text_scale=0.25,
        ).next_to(blue_third_byte, DOWN, buff=0)
        blue_value.text.scale_to_fit_height(tag_value.text.height)

        qoi_rgb_bytes = VGroup(
            rgb_tag_byte,
            red_first_byte,
            green_second_byte,
            blue_third_byte,
            tag_value,
            red_value,
            green_value,
            blue_value,
        ).move_to(ORIGIN)

        return qoi_rgb_bytes

    def get_index_bytes(self):
        index_tag_byte = (
            Byte(["Byte[0]", "7,6,5,4,3,2,1,0"]).scale(0.5).move_to(DOWN * 2)
        )

        target_text = VGroup(index_tag_byte.text[1][1], index_tag_byte.text[1][2])
        tag_value = Byte(
            "0,0",
            width=target_text.get_center()[0]
            + SMALL_BUFF
            - index_tag_byte.get_left()[0],
            height=index_tag_byte.height,
        )
        tag_value.text.scale_to_fit_height(index_tag_byte.text[1][1].height)

        tag_value.next_to(index_tag_byte, DOWN, aligned_edge=LEFT, buff=0)

        index_value = Byte(
            "index",
            width=index_tag_byte.get_right()[0] - tag_value.get_right()[0],
            height=tag_value.height,
        )

        index_value.text.scale_to_fit_height(tag_value.text.height).scale(1.3)

        index_value.next_to(index_tag_byte, DOWN, aligned_edge=RIGHT, buff=0)

        qoi_index_bytes = VGroup(index_tag_byte, tag_value, index_value).move_to(ORIGIN)

        return qoi_index_bytes

    def get_run_bytes(self):
        run_tag_byte = Byte(["Byte[0]", "7,6,5,4,3,2,1,0"]).scale(0.5).move_to(DOWN * 2)

        target_text = VGroup(run_tag_byte.text[1][1], run_tag_byte.text[1][2])
        tag_value = Byte(
            "1,1",
            text_scale=1,
            width=target_text.get_center()[0] + SMALL_BUFF - run_tag_byte.get_left()[0],
            height=run_tag_byte.height,
        )
        tag_value.text.scale_to_fit_height(run_tag_byte.text[1][1].height)

        tag_value.next_to(run_tag_byte, DOWN, aligned_edge=LEFT, buff=0)
        tag_value.text.rotate(
            PI
        )  # Not sure why this has to be done? Some issue with VGroup arrangement
        tag_value.text[0].shift(LEFT * SMALL_BUFF * 0.5)
        tag_value.text[1].shift(RIGHT * SMALL_BUFF * 0.5)

        run_value = Byte(
            "run",
            width=run_tag_byte.get_right()[0] - tag_value.get_right()[0],
            height=tag_value.height,
        )

        run_value.text.scale_to_fit_height(tag_value.text.height).scale(1.1)

        run_value.next_to(run_tag_byte, DOWN, aligned_edge=RIGHT, buff=0)

        qoi_index_bytes = VGroup(run_tag_byte, tag_value, run_value).move_to(ORIGIN)

        return qoi_index_bytes

    def get_large_diff_bytes(self):
        diff_tag_byte = (
            Byte(["Byte[0]", "7,6,5,4,3,2,1,0"]).scale(0.5).move_to(DOWN * 2)
        )

        target_text = VGroup(diff_tag_byte.text[1][1], diff_tag_byte.text[1][2])
        tag_value = Byte(
            "1,0",
            width=target_text.get_center()[0]
            + SMALL_BUFF
            - diff_tag_byte.get_left()[0],
            height=diff_tag_byte.height,
        )
        tag_value.text.scale_to_fit_height(diff_tag_byte.text[1][1].height)
        tag_value.text.rotate(PI)

        tag_value.next_to(diff_tag_byte, DOWN, aligned_edge=LEFT, buff=0)

        dg_value = Byte(
            "diff green (dg)",
            width=diff_tag_byte.get_right()[0] - tag_value.get_right()[0],
            height=tag_value.height,
        )

        dg_value.text.scale_to_fit_height(tag_value.text.height).scale(1.1)

        dg_value.next_to(diff_tag_byte, DOWN, aligned_edge=RIGHT, buff=0)

        second_byte = (
            Byte(["Byte[1]", "7,6,5,4,3,2,1,0"])
            .scale(0.5)
            .next_to(diff_tag_byte, RIGHT, buff=0)
        )

        second_target_text = VGroup(diff_tag_byte.text[1][3], diff_tag_byte.text[1][4])

        dr_dg_value = Byte(
            "dr - dg",
            width=second_target_text.get_center()[0] - dg_value.get_right()[0],
            height=dg_value.height,
        ).next_to(second_byte, DOWN, aligned_edge=LEFT, buff=0)
        dr_dg_value.text.scale_to_fit_height(dg_value.text.height)

        db_dg_value = Byte(
            "db - dg", width=dr_dg_value.width, height=dg_value.height
        ).next_to(second_byte, DOWN, aligned_edge=RIGHT, buff=0)
        db_dg_value.text.scale_to_fit_height(dr_dg_value.text.height)

        qoi_diff_bytes = VGroup(
            diff_tag_byte,
            second_byte,
            tag_value,
            dg_value,
            dr_dg_value,
            db_dg_value,
        ).move_to(ORIGIN)

        return qoi_diff_bytes

    def get_small_diff_bytes(self):
        diff_tag_byte = (
            Byte(["Byte[0]", "7,6,5,4,3,2,1,0"]).scale(0.5).move_to(DOWN * 2)
        )

        target_text = VGroup(diff_tag_byte.text[1][1], diff_tag_byte.text[1][2])
        tag_value = Byte(
            "1,0",
            width=target_text.get_center()[0]
            + SMALL_BUFF
            - diff_tag_byte.get_left()[0],
            height=diff_tag_byte.height,
        )
        tag_value.text.scale_to_fit_height(diff_tag_byte.text[1][1].height)
        tag_value.text.rotate(PI)

        tag_value.next_to(diff_tag_byte, DOWN, aligned_edge=LEFT, buff=0)

        second_target_text = VGroup(diff_tag_byte.text[1][3], diff_tag_byte.text[1][4])

        dr_value = Byte(
            "dr",
            width=second_target_text.get_center()[0] - tag_value.get_right()[0],
            height=tag_value.height,
        ).next_to(tag_value, RIGHT, buff=0)
        dr_value.text.scale_to_fit_height(tag_value.text.height)
        dr_value.text.rotate(PI)

        third_target_text = VGroup(diff_tag_byte.text[1][5], diff_tag_byte.text[1][6])

        dg_value = Byte(
            "dg",
            width=third_target_text.get_center()[0] - dr_value.get_right()[0],
            height=tag_value.height,
        ).next_to(dr_value, RIGHT, buff=0)
        dg_value.text.scale_to_fit_height(dr_value.text.height).scale(1.2)
        dg_value.text.rotate(PI)

        db_value = Byte(
            "db",
            width=diff_tag_byte.get_right()[0] - third_target_text.get_center()[0],
            height=tag_value.height,
        ).next_to(dg_value, RIGHT, buff=0)
        db_value.text.scale_to_fit_height(dr_value.text.height)
        db_value.text.rotate(PI)

        qoi_diff_bytes = VGroup(diff_tag_byte, tag_value, dr_value, dg_value, db_value)

        return qoi_diff_bytes

    def get_pixel_values(self, channel, channel_mob, mode="R"):
        pixel_values_text = VGroup()
        for p_val, mob in zip(channel.flatten(), channel_mob):
            text = (
                Text(str(int(p_val)), font="SF Mono", weight=MEDIUM)
                .scale(0.25)
                .move_to(mob.get_center())
            )
            if mode == "G" and p_val > 200:
                text.set_color(BLACK)
            pixel_values_text.add(text)

        return pixel_values_text

    def get_channel_image(self, channel, mode="R"):
        new_channel = np.zeros((channel.shape[0], channel.shape[1], 3))
        for i in range(channel.shape[0]):
            for j in range(channel.shape[1]):
                if mode == "R":
                    new_channel[i][j] = np.array([channel[i][j], 0, 0])
                elif mode == "G":
                    new_channel[i][j] = np.array([0, channel[i][j], 0])
                else:
                    new_channel[i][j] = np.array([0, 0, channel[i][j]])

        return new_channel

    def reshape_channel(self, channel):
        return np.reshape(
            channel, (1, channel.shape[0] * channel.shape[1], channel.shape[2])
        )

    def get_flatten_transform(
        self, original_mob, flattened_mob, original_text, flattened_text
    ):
        transforms = []
        for i in range(original_mob.shape[0]):
            for j in range(original_mob.shape[1]):
                one_d_index = i * original_mob.shape[1] + j
                transforms.append(
                    TransformFromCopy(original_mob[i, j], flattened_mob[0, one_d_index])
                )
                transforms.append(
                    TransformFromCopy(
                        original_text[one_d_index], flattened_text[one_d_index]
                    )
                )

        return transforms


class Filtering(MovingCameraScene):
    def construct(self):
        # self.intro_filtering()
        # self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.present_problem()
        # self.five_filters_explanation()

    def intro_filtering(self):
        title = Text("Lossless Compression", font="CMU Serif", weight=BOLD).to_edge(UP)

        eg_data = Text(
            "00000111101010101 0000 11111 00000111101010101",
            font="SF Mono",
        ).scale(1.5)

        # eg_data[:17].set_color(RED)
        # eg_data[27:].set_opacity(0.5)

        eg_data_no_repeats = Text(
            "0101010001101001001001001001010", font="SF Mono"
        ).scale(1.5)
        brace_no_reps = Brace(eg_data_no_repeats, direction=DOWN)
        question_comp = (
            Text("?x?", font="SF Mono").scale(1.7).next_to(brace_no_reps, DOWN)
        )

        brace_zeros = Brace(eg_data[17:21], direction=DOWN)
        brace_ones = Brace(eg_data[21:26], direction=DOWN)

        comp_zeros = Text("4x0", font="SF Mono").scale(0.5).next_to(brace_zeros, DOWN)
        comp_ones = Text("5x1", font="SF Mono").scale(0.5).next_to(brace_ones, DOWN)

        self.play(Write(title))

        self.wait()

        self.play(AddTextLetterByLetter(eg_data, run_time=1))

        self.wait()

        self.play(
            Write(brace_zeros),
            Write(comp_zeros),
            Write(brace_ones),
            Write(comp_ones),
        )

        self.wait()

        self.play(
            FadeOut(brace_zeros, shift=UP),
            FadeOut(brace_ones, shift=UP),
            FadeOut(comp_zeros, shift=UP),
            FadeOut(comp_ones, shift=UP),
            FadeOut(eg_data, shift=UP),
        )

        self.wait()

        self.play(AddTextLetterByLetter(eg_data_no_repeats, run_time=1))

        self.wait()

        self.play(Write(brace_no_reps, run_time=0.5), Write(question_comp))

    def present_problem(self):
        repeating_text = (
            Text("0000000000000", font="SF Mono").scale(2).shift(UP * 1.3 + LEFT * 2)
        )
        non_rep_text = (
            Text("1001001000101", font="SF Mono").scale(2).shift(DOWN * 1.3 + RIGHT * 2)
        )

        diff = 4
        gradient_data = np.arange(0, 256, diff, dtype=np.uint8).reshape((8, 8))
        gradient_image = PixelArray(
            gradient_data, include_numbers=True, color_mode="GRAY"
        ).scale(0.6)

        self.play(FadeIn(repeating_text, shift=RIGHT))
        self.wait()
        self.play(FadeIn(non_rep_text, shift=LEFT))

        self.play(FadeOut(repeating_text), FadeOut(non_rep_text))

        self.wait()

        self.play(Write(gradient_image))

        self.wait()

        self.play(gradient_image.animate.shift(LEFT * 3))

        self.wait()

        question_1 = (
            Text(
                " How can we represent this data\n in a more repetitive way?",
                font="CMU Serif",
            )
            .scale(0.7)
            .next_to(gradient_image, RIGHT, buff=0.5)
            .shift(UP * 0.9)
        )
        question_2 = (
            Text("Any patterns to be found?", font="CMU Serif")
            .scale(0.7)
            .next_to(question_1, DOWN, buff=1.3, aligned_edge=LEFT)
        )

        self.play(Write(question_1))

        self.wait()

        self.play(Write(question_2))

        self.wait()

        self.play(FadeOut(question_1), FadeOut(question_2))

        row_to_focus_on = gradient_image[0:8]

        self.play(
            self.camera.frame.animate.set_width(row_to_focus_on.width * 1.3)
            .move_to(row_to_focus_on)
            .shift(UP),
            run_time=3,
        )

        self.wait()

        diff_t = Text(f"+{diff}", font="SF Mono").scale(0.3).set_color(REDUCIBLE_YELLOW)

        arrows = VGroup()
        diffs = VGroup()
        for i in range(1, 8):
            arrow = (
                CurvedArrow(
                    gradient_image[i - 1].get_center() + UP * 0.3,
                    gradient_image[i].get_center() + UP * 0.3,
                    radius=-0.5,
                )
                .set_color(REDUCIBLE_YELLOW)
                .set_stroke(width=1)
            )
            arrow.pop_tips()
            arrow.add_tip(
                tip_shape=ArrowTriangleFilledTip, tip_length=0.05, at_start=False
            )

            arrows.add(arrow)
            self.play(Write(arrow))

            diff_copy = diff_t.copy().next_to(arrow, UP, buff=0.1)
            diffs.add(diff_copy)
            self.play(FadeIn(diff_copy, shift=UP * 0.2))

        self.wait()

        diff_buff = (
            PixelArray(
                np.array(
                    [
                        [0, 4, 4, 4, 4, 4, 4, 4],
                    ]
                ),
                color_mode="GRAY",
                include_numbers=True,
            )
            .scale_to_fit_width(gradient_image.width)
            .next_to(gradient_image, UP * 0.45, buff=2)
        )

        [
            p.set_color(REDUCIBLE_PURPLE)
            .set_opacity(0.5)
            .set_stroke(REDUCIBLE_PURPLE, width=3, opacity=1)
            for p in diff_buff
        ]

        diff_buff.numbers.set_color(WHITE).set_opacity(1).set_stroke(width=0)

        self.play(LaggedStartMap(FadeIn, diff_buff))

    def five_filters_explanation(self):
        # intro for the name of the filters

        filter_title = Text("Filtering", font="CMU Serif", weight=BOLD).to_edge(UP)

        none_t = Text("NONE", font="CMU Serif", weight=BOLD).scale(0.7)
        sub_t = Text("SUB", font="CMU Serif", weight=BOLD).scale(0.7)
        up_t = Text("UP", font="CMU Serif", weight=BOLD).scale(0.7)
        avg_t = Text("AVG", font="CMU Serif", weight=BOLD).scale(0.7)
        paeth_t = Text("PAETH", font="CMU Serif", weight=BOLD).scale(0.7)

        filter_types = VGroup(none_t, sub_t, up_t, avg_t, paeth_t).arrange(
            RIGHT, buff=1
        )

        self.play(Write(filter_title))
        self.wait()
        self.play(LaggedStartMap(FadeIn, filter_types))

        self.wait()

        filter_types_v = (
            filter_types.copy()
            .arrange(DOWN, aligned_edge=LEFT, buff=0.7)
            .scale(0.8)
            .to_edge(LEFT)
            .shift(DOWN * 0.5)
        )

        self.play(Transform(filter_types, filter_types_v))

        self.wait()

        random_data = np.random.randint(127, 140, (9, 8))
        # random_data = np.arange(64).reshape((8, 8))
        input_img = PixelArray(
            random_data, include_numbers=True, color_mode="GRAY", outline=True
        ).scale(0.4)
        input_img_t = (
            Text("Input Image", font="CMU Serif")
            .scale(0.5)
            .next_to(input_img, DOWN, buff=0.2)
        )

        output_img = input_img.copy().next_to(input_img, RIGHT, buff=0.5)
        output_img_t = (
            Text("Filtered Image", font="CMU Serif")
            .scale(0.5)
            .next_to(output_img, DOWN, buff=0.2)
        )

        self.play(
            FadeIn(input_img),
            Write(input_img_t),
            FadeIn(output_img),
            Write(output_img_t),
        )

        line_none = self.underline_filter_type(filter_types_v[0])
        self.wait()

        zoomed_in_sample = (
            self.create_pixel_array(2, 2).scale(2).next_to(input_img, LEFT)
        )
        a_t = (
            Text("a", font="SF Mono", weight=BOLD)
            .scale(0.6)
            .set_color(REDUCIBLE_VIOLET)
            .next_to(zoomed_in_sample[0], ORIGIN)
        )
        b_t = (
            Text("b", font="SF Mono", weight=BOLD)
            .scale(0.6)
            .set_color(REDUCIBLE_GREEN_LIGHTER)
            .next_to(zoomed_in_sample[1], ORIGIN)
        )
        c_t = (
            Text("c", font="SF Mono", weight=BOLD)
            .scale(0.6)
            .set_color(REDUCIBLE_BLUE)
            .next_to(zoomed_in_sample[2], ORIGIN)
        )
        x_t = (
            Text("x", font="SF Mono", weight=BOLD)
            .scale(0.6)
            .set_color(REDUCIBLE_YELLOW)
            .next_to(zoomed_in_sample[3], ORIGIN)
        )

        sub_filtered_data = self.sub_filter_img(random_data)
        up_filtered_data = self.up_filter_img(random_data)
        avg_filtered_data = self.avg_filter_img(random_data)
        paeth_filtered_data = self.paeth_filter_img(random_data)

        sub_filtered_mob = (
            PixelArray(
                sub_filtered_data, include_numbers=True, color_mode="GRAY", outline=True
            )
            .scale(0.4)
            .move_to(output_img)
        )
        up_filtered_mob = (
            PixelArray(
                up_filtered_data, include_numbers=True, color_mode="GRAY", outline=True
            )
            .scale(0.4)
            .move_to(output_img)
        )
        avg_filtered_mob = (
            PixelArray(
                avg_filtered_data, include_numbers=True, color_mode="GRAY", outline=True
            )
            .scale(0.4)
            .move_to(output_img)
        )
        paeth_filtered_mob = (
            PixelArray(
                paeth_filtered_data,
                include_numbers=True,
                color_mode="GRAY",
                outline=True,
            )
            .scale(0.4)
            .move_to(output_img)
        )

        # self.play(
        #     FadeIn(zoomed_in_sample),
        #     FadeIn(a_t),
        #     FadeIn(b_t),
        #     FadeIn(c_t),
        #     FadeIn(x_t),
        # )
        self.wait()

        # filter_row_3 = (
        #     self.up_filter_row(random_data, 0, True).scale(0.4).move_to(output_img)
        # )

        filtered_data = random_data.copy()

        surr_rect = SurroundingRectangle(input_img[0 : random_data.shape[1]])
        self.play(Write(surr_rect))
        for row in range(random_data.shape[0]):
            if row % 2 == 0:
                filtered_row = self.sub_filter_row(random_data, row, return_row=True)
                filtered_data[row, :] = filtered_row
                filter_sub = (
                    PixelArray(filtered_data, include_numbers=True, color_mode="GRAY")
                    .scale(0.4)
                    .move_to(output_img)
                )

                next_row_slice = slice(
                    row * random_data.shape[1],
                    row * random_data.shape[1] + random_data.shape[1],
                )
                next_surr_rect = SurroundingRectangle(
                    input_img[next_row_slice], buff=0, color=REDUCIBLE_YELLOW
                )
                self.play(
                    Transform(output_img, filter_sub),
                    Transform(surr_rect, next_surr_rect),
                )
                print(f"sub filtering row {row}")
            else:
                filtered_row = self.up_filter_row(random_data, row, return_row=True)
                filtered_data[row, :] = filtered_row
                filter_up = (
                    PixelArray(filtered_data, include_numbers=True, color_mode="GRAY")
                    .scale(0.4)
                    .move_to(output_img)
                )

                next_row_slice = slice(
                    row * random_data.shape[1],
                    row * random_data.shape[1] + random_data.shape[1],
                )
                next_surr_rect = SurroundingRectangle(
                    input_img[next_row_slice], buff=0, color=REDUCIBLE_YELLOW
                )
                self.play(
                    Transform(output_img, filter_up),
                    Transform(surr_rect, next_surr_rect),
                )
                print(f"up filtering row {row}")

        # self.play(Transform(output_img, filter_row_3))

    #####################################################################

    # Functions

    def underline_filter_type(self, mob: VMobject):
        line = Line(ORIGIN, [mob.width, 0, 0]).next_to(mob, DOWN, buff=0.1)
        self.play(Write(line))

        return line

    def create_pixel_array(self, rows=8, cols=8):
        return (
            VGroup(
                *[Square(color=WHITE).set_stroke(width=2) for s in range(rows * cols)]
            )
            .arrange_in_grid(rows=rows, cols=cols, buff=0)
            .scale(0.15)
        )

    def sub_filter_img(self, img: ndarray):
        """
        Compute the sub filter for the whole input array
        """

        rows, cols = img.shape
        output = np.zeros(img.shape, dtype=np.int16)

        for j in range(rows):
            for i in range(1, cols):
                output[j, i] = int(img[j, i] - img[j, i - 1])

        output[:, 0] = img[:, 0]

        return output

    def up_filter_img(self, img: ndarray):
        """
        Compute the up filter for the whole input array
        """

        rows, cols = img.shape

        output = np.zeros(img.shape, dtype=np.uint8)

        for j in range(1, rows):
            for i in range(cols):
                output[j, i] = abs(img[j, i] - img[j - 1, i])

        output[0, :] = img[0, :]
        return output

    def avg_filter_img(self, img: ndarray):
        """
        Each byte is replaced with the difference between it and the average
        of the corresponding bytes to its left and above it, truncating any fractional part.
        """

        rows, cols = img.shape

        padded_data = np.pad(img, (1, 0), constant_values=0, mode="constant")
        print(padded_data)
        output = np.zeros(img.shape, dtype=np.uint8)

        for j in range(1, rows + 1):
            for i in range(1, cols + 1):
                avg = (padded_data[j - 1, i] + padded_data[j, i - 1]) / 2
                output[j - 1, i - 1] = floor(abs(padded_data[j, i] - avg))

        return output

    def paeth_filter_img(self, img: ndarray):
        """
        Computes the paeth predictor for the whole input array
        """

        rows, cols = img.shape

        output = np.zeros(img.shape, dtype=np.uint8)
        padded_data = np.pad(img, (1, 0), constant_values=0, mode="constant")

        for j in range(1, rows + 1):
            for i in range(1, cols + 1):
                a = padded_data[j - 1, i - 1]  # up-left
                b = padded_data[j - 1, i]  # up
                c = padded_data[j, i - 1]  # left

                base_value = b + c - a

                # the dictionary is created in this specific order to account
                # for how PNG deals with ties. The specification says
                # that in the case of ties, left byte has precedence, then up.

                paeth_dict = {
                    abs(base_value - c): c,
                    abs(base_value - b): b,
                    abs(base_value - a): a,
                }

                # The min function will output the first instance it found in case of ties.
                # So that's why we built the dict that way.
                winner = paeth_dict[min(paeth_dict.keys())]

                # print(
                #     f"output[{j-1},{i-1}] is {padded_data[j,i] = } - {winner = } which equals {abs(padded_data[j, i] - winner)}"
                # )

                output[j - 1, i - 1] = abs(padded_data[j, i] - winner)

        print(output)
        return output

    def sub_filter_row(self, img: ndarray, row=0, return_mob=False, return_row=False):
        rows, cols = img.shape
        output = img.copy()

        for i in range(1, cols):
            output[row, i] = img[row, i] - img[row, i - 1]

        output[row, 0] = img[row, 0]

        if return_mob:
            return PixelArray(output, include_numbers=True, color_mode="GRAY")
        elif return_row:
            return output[row, :]
        else:
            return output

    def up_filter_row(self, img: ndarray, row=0, return_mob=False, return_row=False):
        rows, cols = img.shape
        output = img.copy()

        if row == 0:
            pass
        else:
            for i in range(cols):
                output[row, i] = img[row, i] - img[row - 1, i]

        if return_mob:
            return PixelArray(output, include_numbers=True, color_mode="GRAY")
        elif return_row:
            return output[row, :]
        else:
            return output
