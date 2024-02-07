import mitsuba as mi 
import drjit as dr 
# import math
import pointsGen
import numpy as np
from sklearn.neighbors import KDTree
# import pickle

# import toolpath points from setup file
import setups.setup2 as setup



mi.set_variant("llvm_ad_rgb")

def ppt(v, n=''):
        print(n, type(v), dr.shape(v), len(v))
        
        
def addAttribute(props, name, default=None):
    if props.has_property(name):
        return props[name]
    else:
        return default
    
    
class MyTexture(mi.Texture):
    def __init__(self, props):
        mi.Texture.__init__(self, props)
        
        # import list of points from setup
        self.pointsList = setup.getPoints()
        # print(self.pointsList.list)
            
        # # import list of points if provided
        # if props.has_property('points'):
        #     self.pointsList = props['points']
        # else:
        #     print("No points were provided.")
        #     self.pointsList = pointsGen.PointsList()
        

        # self.pointsList.addRectGrid(0.3, -1, 1, 0.3, -1, 1, 0, 0, mi.ScalarTransform4f())
        self.tree = KDTree(self.pointsList.list, leaf_size=10)
        
    
    def eval(self, si, active=True):
        radius = 0.03
        dist, ind = self.tree.query(si.p, k=1)  # np.ndarray
        dist = (dist <= radius)
        dist = np.tile(dist, 3)                 # expand to 3 columns, all same values
        dist = dr.llvm.Array3f(dist)
        return dist * mi.Color3f(1, 0, 0) + (mi.Vector3f(1, 1, 1) - dist) * mi.Color3f(0.8, 0.8, 0.8)      
    
    def eval_3(self, si, active=True):
        return self.eval(si)
