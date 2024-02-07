import sys
sys.path.append("..")
import pointsGen

def getPoints():
    points = pointsGen.PointsList()
    points.addSpiralGrid(0.2, 0.2, 0.9, 0.5, 1)
    return points