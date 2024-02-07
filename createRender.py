import mitsuba as mi
mi.set_variant('llvm_ad_rgb')
import drjit as dr
import time
import pointsTexture

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
        'type': 'rectangle',
        'bsdf': {
            'type': 'diffuse',
            'reflectance': {
                'type': 'pointsTex'
            }
        }
    }
})


if __name__ == '__main__':
    resolution = (512, 512)
    camOrigin = [0, -3, 3]
    spp = 16
    
    dr.set_flag(dr.JitFlag.VCallRecord, False)
    dr.set_flag(dr.JitFlag.LoopRecord, False)
    
    t = time.time()
    scene = make_scene(resolution, camOrigin)
    print('Created scene in', time.time()-t, 's')
    
    t = time.time()
    with dr.suspend_grad():
        image = mi.render(scene, spp=spp)
    print('Rendered in', time.time()-t, 's')
    
    t = time.time()
    mi.util.write_bitmap("render.png", image)
    print('Stored in', time.time()-t, 's')
