import mitsuba as mi
import drjit as dr
from drjit.llvm import Float
import math
import random

# assigns priority to rectangular grid
def rectPriority(p):
    return 0.01*p[0] + p[1]

# find indices of the grid square containing the given point
# currently 2D only (ignores Z coordinate), subdivision is k by k, 
# indices refer to the bottom left corner of the grid
# assumes origin is at center of region being subdivided
# def getIndices(point, xStart, xStop, yStart, yStop, k):
#     return (dr.floor(point[0] * k / (xStop - xStart) + (k / 2)), dr.floor(point[1] * k / (yStop - yStart) + (k / 2)))

# given x and y values, create a grid of points, sort by priority, and rotate as needed
def createPoints(xv, yv, zv, transform, priorityFunction=None):
    l = []
    for x,y,z in zip(xv,yv,zv):
        l.append(mi.ScalarPoint3f(x,y,z))
    if priorityFunction is not None:        # sort points by (decreasing) priority if applicable
        l.sort(key=priorityFunction)
    return rotatePoints(l, transform)


def rotatePoints(pointsList, transform):
    # rotation = mi.ScalarTransform4f.rotate(axis=axis, angle=phiDegrees)
    return [transform @ point for point in pointsList]


def randomPoints(xRange, yRange, numPoints):
    xStart, xStop = xRange
    yStart, yStop = yRange
    result = []
    for i in range(numPoints):
        x, y = random.random(), random.random()
        x = x * (xStop - xStart) + xStart
        y = y * (yStop - yStart) + yStart
        result.append((x, y))
    print(result)
    return result


class PointsList():
    def __init__(self):
        self.list = list()
        
    # notice: there could be a slicker way to do this by creating an x-aligned linspace and rotating it using createPoints
    def addLine(self, start, stop, gridWidth):
        xStart, yStart = start
        xStop, yStop = stop
        length = math.sqrt((xStop - xStart)**2 + (yStop - yStart)**2)
        newLength = math.ceil(length / gridWidth) * gridWidth  # scales length to nearest multiple of gridWidth
        if newLength != length:
            # print(f"NOTE: scaled line from {xStart, yStart} to {xStop, yStop} up to fit gridWidth {gridWidth}.")
            length = newLength
        numPoints = int(length / gridWidth) + 1
        xv = dr.linspace(Float, xStart, xStop, numPoints)
        yv = dr.linspace(Float, yStart, yStop, numPoints)
        zv = dr.zeros(Float, numPoints)
        self.list += createPoints(xv, yv, zv, 0)
        
    
    # create an arc from start to stop of angle 180 degrees (half circle)    
    # 180 degrees is handled as the only case for now
    # note that delta may not be entirely accurate, but should be very close in most scenarios
    # "flip" only changes priority of points (when True, we go from stop -> start)
    def addArc(self, start, stop, thetaDegrees, delta, flip=False):
        # print(f"arc from {start} to {stop}")
        start = mi.ScalarPoint2f(start)
        stop = mi.ScalarPoint2f(stop)
        delta = max(delta, 0.01)
        thetaRadians = math.radians(thetaDegrees)
        if thetaDegrees == 180:
            center = mi.ScalarPoint2f((start[0] + stop[0]) / 2, (start[1] + stop[1]) / 2)
            r = dr.norm(stop - start) / 2
        # else:
        #     thetaRadians = min(max(thetaRadians, 0.01), math.pi)
        #     u = stop - start
        #     d = dr.norm(u)
        #     u = dr.normalize(u)
        #     rot = mi.ScalarTransform3f.rotate(angle=(-90 + thetaDegrees / 2))
        #     u = rot @ u     # point toward center of circle
        #     r = abs(d / (2 * math.cos(math.pi - thetaRadians / 2)))
        #     center = start + u * r
        v = start - center
        # print(v)
        phiRadians = math.copysign(math.pi / 2, v[1]) if v[0] == 0.0 else math.atan(v[1] / v[0])
        if v[0] < 0:
            phiRadians += math.pi
        numPoints = math.ceil(thetaRadians * r / delta)     # comparing arc lengths
        arcGapRadians = thetaRadians / numPoints
        # print(arcGapRadians, numPoints)
        xv = [center[0] + r * math.cos(phiRadians - arcGapRadians * i) for i in range(numPoints)]
        yv = [center[1] + r * math.sin(phiRadians - arcGapRadians * i) for i in range(numPoints)]
        zv = dr.zeros(Float, len(xv))
        newPoints = createPoints(xv, yv, zv, 0)
        if flip:
            newPoints.reverse()
        self.list += newPoints
        
        
    # create a series of connected line segments using `points` as vertices
    # if closed=False, do not connect last point to first
    # if arcs=True, every second line will instead be an arc of `angle` degrees
    # if flip=True, first arc will go on the "right" side (instead of left)
    # if alternating=True, arc direction will flip each time (used for snaking pattern)
    def addPolygon(self, points:list, gridWidth, closed=True, arcs=False, angle=180, flip=False, alternating=False):
        if closed == False:
            numPoints = len(points) - 1
        else:
            numPoints = len(points)
            points.append(points[0])
            
        for i in range(numPoints):
            if arcs == True and i % 2 == 1:
                if flip:
                    self.addArc(points[i+1], points[i], angle, gridWidth)
                else:
                    self.addArc(points[i], points[i+1], angle, gridWidth)
                if alternating:
                    flip = not flip
                    
            else:
                self.addLine(points[i], points[i+1], gridWidth)
    
    
    # generate a rectangular grid of points 
    # compresses xStart/xStop and yStart/yStop so that they are a multiple of xWidth and yWidth respectively
    # and stretches them far enough so that the entire surface gets the full number of possible rings
    def addRectGrid(self, xWidth, xStart, xStop, yWidth, yStart, yStop, zHeight, radius, transform=mi.ScalarTransform4f()):
        # if radius < xWidth:
        (xStart, xStop) = (math.ceil(xStart / xWidth) * xWidth, math.floor(xStop / xWidth) * xWidth)
        # else:
        #     (xStart, xStop) = (math.floor((xStart - radius) / xWidth) * xWidth, math.ceil((xStop + radius) / xWidth) * xWidth)
        # if radius < yWidth:
        (yStart, yStop) = (math.ceil(yStart / yWidth) * yWidth, math.floor(yStop / yWidth) * yWidth)
        # else:
        #     (yStart, yStop) = (math.floor((yStart - radius) / yWidth) * yWidth, math.ceil((yStop + radius) / yWidth) * yWidth)
        xVals = dr.linspace(Float, xStart, xStop, int((xStop - xStart) / xWidth) + 1)
        yVals = dr.linspace(Float, yStart, yStop, int((yStop - yStart) / yWidth) + 1)
        
        xv, yv = dr.meshgrid(xVals, yVals)
        zv = zHeight * dr.ones(Float, len(xv)) 
        self.list += createPoints(xv, yv, zv, transform, rectPriority)


    # create a grid of points along archimedean spiral
    # delta = distance between points along the spiral
    # alpha = proportion of overlap between rings on two adjacent wraps of the spiral
    # beta = angular offset 
    # direction in {-1, 1}: -1 is clockwise, 1 is cc-wise
    # origin = origin of the spiral (= u in documentation)
    # phiDegrees = specifies the amount to rotate points around (0,0,0) after generation
    def addSpiralGrid(self, radius, delta, alpha, beta, direction, numRings=100, move='out', transform=mi.ScalarTransform4f()):
        # theta = dr.linspace(Float, thetaStart, thetaStop, int((thetaStop - thetaStart) / thetaWidth) + 1)
        # r = pathStart + theta * pathWidth
        def LFunc(phi, a):
            return (a / 2) * (phi * math.sqrt(1 + phi**2) + math.log(phi + math.sqrt(1 + phi**2)))
        def LDeriv(phi, a):
            return a * math.sqrt(1 + phi**2)
        
        rho = (1 - alpha) * (2 * radius)    # distance between tool paths (i.e. between wraps of the spiral)
        a = rho / 2 * math.pi
        print('rho:', rho)
        print('a:', a)
        
        # calculate angles
        phiVals = []
        oldPhi = 0
        for i in range(1, numRings):
            newPhi = oldPhi - (LFunc(oldPhi, a) - (i - 1) * delta) / LDeriv(oldPhi, a)
            phiVals.append(newPhi)
            oldPhi = newPhi

        xv = Float([direction * a * phi * dr.cos(phi + beta) for phi in phiVals])
        yv = Float([a * phi * dr.sin(phi + beta) for phi in phiVals])
        zv = dr.zeros(Float, len(xv))
        # print("phiVals: ", phiVals)
        # print('xv: ', xv)
        points = createPoints(xv, yv, zv, transform)
        if move == 'in':
            # print('reversed!')
            points.reverse()
        # print(points[:10])
        self.list += points
        
        
    def add3DGrid(self, xWidth, xStart, xStop, yWidth, yStart, yStop, zWidth, zStart, zStop, radius, phiDegrees=0):
        if radius < zWidth:
            (zStart, zStop) = (math.floor(zStart / zWidth) * zWidth, math.ceil(zStop / zWidth) * zWidth)
        else:
            (zStart, zStop) = (math.floor((zStart - radius) / zWidth) * zWidth, math.ceil((zStop + radius) / zWidth) * xWidth)
            
        zVals = dr.linspace(Float, zStart, zStop, int((zStop - zStart) / zWidth) + 1)
        
        for z in zVals:
            self.addRectGrid(xWidth, xStart, xStop, yWidth, yStart, yStop, z, radius, phiDegrees)
    
    
    def addCircle(self, radius, arcLength, zHeight, transform=mi.ScalarTransform4f()):
        thetaWidth = float(arcLength / radius)
        thetaVals = dr.linspace(Float, 0, 2 * math.pi, math.floor(2 * math.pi / thetaWidth) + 1, True)
        xVals = radius * dr.cos(thetaVals)
        yVals = radius * dr.sin(thetaVals)
        zVals = zHeight * dr.ones(Float, len(xVals))
        
        self.list += createPoints(xVals, yVals, zVals, transform)
        
    def addCylinder(self, radius, arcLength, zWidth, zStart, zStop, transform=mi.ScalarTransform4f()):
        zVals = dr.linspace(Float, zStart, zStop, int((zStop - zStart) / zWidth) + 1, True)
        
        for z in zVals:
            print(z)
            self.addCircle(radius, arcLength, z, transform)
            
    # takes in a list of points assumed to be on the XY plane spanning from (x,y) to (-x,-y)
    # projects onto cylinder with radius `r` and transformation `transform` using additional rotation
    # (relative to length) of `phiDegrees`
    def projectToCylinder(self, x, y, r, transform=mi.ScalarTransform4f(), phiDegrees=0.0):
        rotation = mi.ScalarTransform4f.rotate(axis=[0,0,1], angle=phiDegrees)
        projected = list()
        for pt in self.list:
            t = math.pi * (1 + pt[0] / x)   # t ranges from 0 (LHS of plane) to 2pi (RHS of plane)
            projected.append(mi.ScalarPoint3f(r*math.cos(t), r*math.sin(t), pt[1] / y))
        # if transform is not None:
        self.list = rotatePoints(rotatePoints(projected, rotation), transform)
       
