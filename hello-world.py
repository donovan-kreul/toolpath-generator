import mitsuba as mi 

mi.set_variant('scalar_rgb')

img = mi.render(mi.load_dict(mi.cornell_box()))

mi.util.write_bitmap("my_first_render.png", img)