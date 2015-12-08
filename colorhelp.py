import math


class PointF:

    def __init__(self, x, y):
        self.x = x
        self.y = y


def precision(d):
    return round(10000.0 * d) / 10000.0


def crossProduct(point1, point2):
    return point1.x * point2.y - point1.y * point2.x


def checkPointInLampsReach(point, colorPoints):
    red = colorPoints[0]
    green = colorPoints[1]
    blue = colorPoints[2]
    v1 = PointF(green.x - red.x, green.y - red.y)
    v2 = PointF(blue.x - red.x, blue.y - red.y)
    q = PointF(point.x - red.x, point.y - red.y)
    s = crossProduct(q, v2) / crossProduct(v1, v2)
    t = crossProduct(v1, q) / crossProduct(v1, v2)
    if ((s >= 0.0) and (t >= 0.0) and (s + t <= 1.0)):
        return True
    else:
        return False


def getDistanceBetweenTwoPoints(one, two):
    dx = one.x - two.x
    dy = one.y - two.y
    dist = math.sqrt(dx * dx + dy * dy)
    return dist


def getClosestPointToPoints(pointA, pointB, pointP):
    pointAP = PointF(pointP.x - pointA.x, pointP.y - pointA.y)
    pointAB = PointF(pointB.x - pointA.x, pointB.y - pointA.y)
    ab2 = pointAB.x * pointAB.x + pointAB.y * pointAB.y
    apAb = pointAP.x * pointAB.x + pointAP.y * pointAB.y
    t = apAb / ab2
    if (t < 0.0):
        t = 0.0
    elif (t > 1.0):
        t = 1.0
    newPoint = PointF(pointA.x + pointAB.x * t, pointA.y + pointAB.y * t)
    return newPoint


def calculateXY(r, g, b):
    red = r / 255.0
    green = g / 255.0
    blue = b / 255.0
    if red > 0.04045:
        r = math.pow((red + 0.055) / 1.055, 2.4000000953674316)
    else:
        r = red / 12.92
    if green > 0.04045:
        g = math.pow((green + 0.055) / 1.055, 2.4000000953674316)
    else:
        g = green / 12.92
    if blue > 0.04045:
        b = math.pow((blue + 0.055) / 1.055, 2.4000000953674316)
    else:
        b = blue / 12.92

    x = r * 0.664511 + g * 0.154324 + b * 0.162028
    y = r * 0.283881 + g * 0.668433 + b * 0.047685
    z = r * 8.8E-5 + g * 0.07231 + b * 0.986039

    xy = []

    xy.append(x / (x + y + z))
    xy.append(y / (x + y + z))
    if (math.isnan(xy[0])):
        xy[0] = 0.0
    if (math.isnan(xy[1])):
        xy[1] = 0.0
    xyPoint = PointF(xy[0], xy[1])
    colorPoints = []
    # colorPoints.append( PointF(1.0, 0.0))
    # colorPoints.append( PointF(0.0, 1.0))
    # colorPoints.append( PointF(0.0, 0.0))
    colorPoints.append(PointF(0.674, 0.322))
    colorPoints.append(PointF(0.408, 0.517))
    colorPoints.append(PointF(0.168, 0.041))
    inReachOfLamps = checkPointInLampsReach(xyPoint, colorPoints)
    if not inReachOfLamps:
        pAB = getClosestPointToPoints(colorPoints[0], colorPoints[1], xyPoint)
        pAC = getClosestPointToPoints(colorPoints[2], colorPoints[0], xyPoint)
        pBC = getClosestPointToPoints(colorPoints[1], colorPoints[2], xyPoint)
        dAB = getDistanceBetweenTwoPoints(xyPoint, pAB)
        dAC = getDistanceBetweenTwoPoints(xyPoint, pAC)
        dBC = getDistanceBetweenTwoPoints(xyPoint, pBC)
        lowest = dAB
        closestPoint = pAB
        if (dAC < lowest):
            lowest = dAC
            closestPoint = pAC
        if (dBC < lowest):
            lowest = dBC
            closestPoint = pBC
        xy[0] = closestPoint.x
        xy[1] = closestPoint.y
    xy[0] = precision(xy[0])
    xy[1] = precision(xy[1])
    return xy


def colorFromXY(points):
    xy = PointF(points[0], points[1])
    colorPoints = []
    # colorPoints.append( PointF(1.0, 0.0))
    # colorPoints.append( PointF(0.0, 1.0))
    # colorPoints.append( PointF(0.0, 0.0))
    colorPoints.append(PointF(0.674, 0.322))
    colorPoints.append(PointF(0.408, 0.517))
    colorPoints.append(PointF(0.168, 0.041))
    inReachOfLamps = checkPointInLampsReach(xy, colorPoints)
    if not inReachOfLamps:
        pAB = getClosestPointToPoints(colorPoints[0], colorPoints[1], xy)
        pAC = getClosestPointToPoints(colorPoints[2], colorPoints[0], xy)
        pBC = getClosestPointToPoints(colorPoints[1], colorPoints[2], xy)
        dAB = getDistanceBetweenTwoPoints(xy, pAB)
        dAC = getDistanceBetweenTwoPoints(xy, pAC)
        dBC = getDistanceBetweenTwoPoints(xy, pBC)
        lowest = dAB
        closestPoint = pAB
        if dAC < lowest:
            lowest = dAC
            closestPoint = pAC
        if dBC < lowest:
            lowest = dBC
            closestPoint = pBC

        xy.x = closestPoint.x
        xy.y = closestPoint.y
    x = xy.x
    y = xy.y
    z = 1.0 - x - y
    y2 = 1.0
    x2 = y2 / y * x
    z2 = y2 / y * z

    r = x2 * 1.656492 - y2 * 0.354851 - z2 * 0.255038
    g = -x2 * 0.707196 + y2 * 1.655397 + z2 * 0.036152
    b = x2 * 0.051713 - y2 * 0.121364 + z2 * 1.01153
    if ((r > b) and (r > g) and (r > 1.0)):
        g /= r
        b /= r
        r = 1.0
    elif ((g > b) and (g > r) and (g > 1.0)):
        r /= g
        b /= g
        g = 1.0
    elif ((b > r) and (b > g) and (b > 1.0)):
        r /= b
        g /= b
        b = 1.0
    if r <= 0.0031308:
        r = 12.92 * r
    else:
        r = 1.055 * math.pow(r, 0.4166666567325592) - 0.055
    if g <= 0.0031308:
        g = 12.92 * g
    else:
        g = 1.055 * math.pow(g, 0.4166666567325592) - 0.055
    if b <= 0.0031308:
        b = 12.92 * b
    else:
        b = 1.055 * math.pow(b, 0.4166666567325592) - 0.055
    if ((r > b) and (r > g)):
        if (r > 1.0):
            g = g / r
            b = b / r
            r = 1.0
    elif ((g > b) and (g > r)):
        if (g > 1.0):
            r = r / g
            b = b / g
            g = 1.0
    elif ((b > r) and (b > g) and (b > 1.0)):
        r = r / b
        g = g / b
        b = 1.0
    if (r < 0.0):
        r = 0.0
    if (g < 0.0):
        g = 0.0
    if (b < 0.0):
        b = 0.0
    r1 = int(r * 255.0)
    g1 = int(g * 255.0)
    b1 = int(b * 255.0)

    return (r1, g1, b1)
