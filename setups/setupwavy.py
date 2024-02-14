import sys
sys.path.append("..")
import pointsGen
import math

def getPoints():
    points = pointsGen.PointsList()
    # call PointsList methods here to define a list of points
    # otherwise, can manually define points.list with a custom list
    points.addRectGrid(0.2, -1, 1, 0.1, -1, 1, 0)
    
    # project points onto curve of 60 degrees (wavy-plane.obj)
    # specifically this is pi/6 rad arc of circle with arclength 1 => radius = 6/pi
    r = 6 / math.pi
    thickness = 0.1
    for pt in points.list:
        pt[2] = -1 * math.sqrt(r**2 - pt[1]**2) + r + thickness
    
    return points