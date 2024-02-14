import mitsuba as mi
mi.set_variant('llvm_ad_rgb')
import drjit as dr
import sys
import time
import importlib
import pointsTexture
# import setups.setup1 as setup1

# # import specific list of toolpath points
# try:
#     setup_name = sys.argv[1]
#     # setup_name = "setups." + setup_name
#     print("Pulling from: ", setup_name)
# except:
#     print('Setup file is missing or not specified.')
#     exit()

try:
    render_name = sys.argv[1]
except:
    render_name = 'render'

# # setup = __import__(setup_name)
# setup = importlib.import_module(setup_name)

mi.register_texture("pointsTex", lambda props: pointsTexture.MyTexture(props))

def make_scene(resolution, camOrigin):
    cam_transform = mi.ScalarTransform4f.look_at(
        origin=camOrigin,
        target=[0, 0, 0],
        up=[0, 1, 0]
    )
    return mi.load_dict({
    'type': 'scene',
    'integrator': {
        'type': 'path',
        'max_depth': 3,
        'hide_emitters': True,
    },
    'light': {
        'type': 'constant',
        'radiance': 0.2
    },
    'sensor': {
        'type': 'perspective',
        'to_world': cam_transform,
        'fov': 45,
        'film': {
            'type': 'hdrfilm',
            'width': resolution[0],
            'height': resolution[1],
            'filter': { 'type': 'lanczos' }
        }
    },
    'object': {
    #     'type': 'rectangle',
    #     'bsdf': {
    #         'type': 'diffuse',
    #         'reflectance': {
    #             'type': 'pointsTex',
    #             # 'pointsList': points
    #         }
    #     }
        'type': 'obj',
        'filename': 'objects/wavy-plane.obj',
        'bsdf': {
            'type': 'diffuse',
            'reflectance': {
                'type': 'pointsTex',
            }
        }
    }
})


if __name__ == '__main__':
    # default parameters, optionally overwritten by setup file 
    resolution = (512, 512)
    camOrigin = [0, -2, 3]
    spp = 16

    # pull PointsList from setup file
    # points = setup1.getPoints()
    
    # drjit tricks to simplify our pointsTexture code
    dr.set_flag(dr.JitFlag.VCallRecord, False)
    dr.set_flag(dr.JitFlag.LoopRecord, False)
    
    # create scene
    t = time.time()
    scene = make_scene(resolution, camOrigin)
    print('Created scene in', time.time()-t, 's')
    
    # render scene
    t = time.time()
    with dr.suspend_grad():
        image = mi.render(scene, spp=spp)
    print('Rendered in', time.time()-t, 's')
    
    # write to output file
    t = time.time()
    mi.util.write_bitmap('./renders/' + render_name + '.png', image)
    print('Stored in', time.time()-t, 's')
