import sys
sys.path.append("..")
import pointsGen

def getPoints():
    points = pointsGen.PointsList()
    points.addRectGrid(0.2, -1, 1, 0.1, -1, 1, 0)
    return points