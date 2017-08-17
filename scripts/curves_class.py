import bpy
import math
import numpy as np
from mathutils import Vector
import json

MAXIMUM_VIEW_RAIDUS = 500

class SampleVertex:

	def __init__(self, co=(0,0,0), curvature=0, t=(1,0,0), b=(0,0,1)):
		self.co = co
		self.curvature = curvature
		self.tangent = t
		self.normal = (b[1]*t[2] - b[2]*t[1], b[2]*t[0] - b[0]*t[2], b[0]*t[1] - b[1]*t[0])
		self.binormal = b #(t[1]*n[2]-t[2]*n[1], t[2]*n[0]-t[0]*n[2], t[0]*n[1] - t[1]*n[0])

class Curve:

	def getsamplelength(self, coordinates):

		total = 0

		for i in range(len(coordinates) - 1):

			total += self.distance(coordinates[i], coordinates[i + 1])

		return total

	def distance(self, tuple1, tuple2):

		return math.sqrt(math.pow(tuple1[0] - tuple2[0], 2) + math.pow(tuple1[1] - tuple2[1], 2) + math.pow(tuple1[2] - tuple2[2], 2))

	def viewcurvature(self, samplevertices, obj):

		if bpy.data.objects.find(obj.name + '_CurvatureDetail') == -1:

			curve = bpy.data.curves.new(name=obj.name + '_CurvatureDetail', type='CURVE')
			curve.dimensions = '3D'

			curvatureobj = bpy.data.objects.new(obj.name + '_CurvatureDetail', curve)
			curvatureobj.location = obj.location
			bpy.context.scene.objects.link(curvatureobj)

		curve = bpy.data.objects[obj.name + '_CurvatureDetail'].data

		# clean curve data splines
		if (len(curve.splines)):
			for spline in curve.splines:
				curve.splines.remove(spline)

		curvatureouter = curve.splines.new('POLY')
		curvatureouter.points.add(len(samplevertices) - 1)

		for i in range(len(samplevertices)):
			sample = samplevertices[i]
			co = sample.co
			if sample.curvature == 0:
				r = MAXIMUM_VIEW_RAIDUS
			else:
				r = min(1.0 / sample.curvature, MAXIMUM_VIEW_RAIDUS)
			k = sample.curvature
			t = sample.tangent
			n = sample.normal
			b = sample.binormal
			
			radiusend = (co[0] + r*n[0], co[1] + r*n[1], co[2] + r*n[2])
			curvatureend = (co[0] + k*n[0], co[1] + k*n[1], co[2] + k*n[2])
			tangentend = (co[0] + t[0], co[1] + t[1], co[2] + t[2])
			normalend = (co[0] + n[0], co[1] + n[1], co[2] + n[2])
			binormalend = (co[0] + b[0], co[1] + b[1], co[2] + b[2])

			# tangent at sample
			# polyline = curve.splines.new('POLY')
			# polyline.points.add(1)
			# polyline.points[0].co = co + (1,)
			# polyline.points[1].co = tangentend + (1,)

			# normal at sample
			# polyline = curve.splines.new('POLY')
			# polyline.points.add(1)
			# polyline.points[0].co = co + (1,)
			# polyline.points[1].co = normalend + (1,)

			#binormal at sample
			polyline = curve.splines.new('POLY')
			polyline.points.add(1)
			polyline.points[0].co = co + (1,)
			polyline.points[1].co = binormalend + (1,)

			# curvature pointing opposite to k*n
			polyline = curve.splines.new('POLY')
			polyline.points.add(1)
			polyline.points[0].co = co + (1,)
			polyline.points[1].co = curvatureend + (1,)
			# border interpolating the end points of curvature
			curvatureouter.points[i].co = curvatureend + (1,)

			# radius at sample pointing to center
			# polyline = curve.splines.new('POLY')
			# polyline.points.add(1)
			# polyline.points[0].co = co + (1,)
			# polyline.points[1].co = radiusend + (1,)	

class Clothoid(Curve):

	def __init__(self, length, start_curvature, end_curvature):
		self.start_curvature = start_curvature
		self.end_curvature = end_curvature
		self.length = length
		self.resolution = 10

	def sample(self):

		k = (self.end_curvature - self.start_curvature) / self.length
		step = self.length / self.resolution
		s = 0
		preS = 0
		theta = 0
		vertices = []

		while s < self.length + step:

			if s == 0:
				vertices.append(SampleVertex((0,0,0), self.start_curvature))
				s += step
				continue

			if math.fabs(s - self.length) < 1E-4 or s > self.length:
				s = self.length

			preCoord = vertices[len(vertices) - 1].co
			curvature = (s + preS) * 0.5 * k + self.start_curvature

			x = preCoord[0] + (s - preS) * math.cos(theta + curvature * (s - preS) / 2)
			y = preCoord[1] + (s - preS) * math.sin(theta + curvature * (s - preS) / 2)
			z = preCoord[2]

			theta += curvature * (s - preS)
			preS = s
			s += step

			t = (math.cos(theta), math.sin(theta), 0)
			b = (-math.sin(theta) * math.copysign(1, theta), math.cos(theta) * math.copysign(1, theta), 0)
			# b = (0, 0, 1)
			
			vertices.append(SampleVertex((x, y, z), curvature, t, b))

		return vertices

	def convert2bezier(self):

		pass

class Arc(Curve):

	def __init__(self, length, radius):
		self.radius = radius
		self.length = length
		self.resolution = 10

	def sample(self):

		step = 1.0 * self.length / self.resolution

		s = 0; preS = 0
		theta = 0
		curvature = 1.0 / self.radius
		vertices = []

		while s < self.length + step:
			if s == 0:
				vertices.append(SampleVertex((0,0,0), curvature))
				s += step
				continue

			if math.fabs(s - self.length) < 1E-4 or s > self.length:
				s = self.length

			preCoord = vertices[len(vertices) - 1].co

			x = preCoord[0] + (s - preS) * math.cos(theta + (s - preS) / self.radius / 2)
			y = preCoord[1] + (s - preS) * math.sin(theta + (s - preS) / self.radius / 2)
			z = preCoord[2]

			theta += (s - preS) / self.radius
			preS = s
			s += step

			t = (math.cos(theta), math.sin(theta), 0)
			b = (-math.sin(theta) * math.copysign(1, theta), math.cos(theta) * math.copysign(1, theta), 0)
			# b = (0, 0, 1)

			vertices.append(SampleVertex((x, y, z), curvature, t, b))

		return vertices

	def convert2bezier(self):
		
		theta = self.length / self.radius
		p0 = (self.radius * math.cos(theta / 2), self.radius * math.sin(theta / 2), 0)
		p3 = (self.radius * math.cos(theta / 2), self.radius * math.sin(-theta/ 2), 0)
		p1 = ((4.0 * self.radius - p0[0]) / 3, (self.radius - p0[0]) * (3.0 * self.radius - p0[0]) / (3.0 * p0[1]), 0)
		p2 = (p1[0], -p1[1], 0)

		pi = math.pi
		#Rotate theta/2 - sign(theta) * pi / 2
		p0 = (	p0[0] * math.cos(theta / 2  + math.copysign(pi / 2, -theta)) - p0[1] * math.sin(theta / 2 + math.copysign(pi / 2, -theta)), 
				p0[0] * math.sin(theta / 2 + math.copysign(pi / 2, -theta)) + p0[1] * math.cos(theta / 2 + math.copysign(pi / 2, -theta)),
				p0[2])
		p1 = (	p1[0] * math.cos(theta / 2  + math.copysign(pi / 2, -theta)) - p1[1] * math.sin(theta / 2 + math.copysign(pi / 2, -theta)), 
				p1[0] * math.sin(theta / 2 + math.copysign(pi / 2, -theta)) + p1[1] * math.cos(theta / 2 + math.copysign(pi / 2, -theta)),
				p1[2])
		p2 = (	p2[0] * math.cos(theta / 2  + math.copysign(pi / 2, -theta)) - p2[1] * math.sin(theta / 2 + math.copysign(pi / 2, -theta)), 
				p2[0] * math.sin(theta / 2 + math.copysign(pi / 2, -theta)) + p2[1] * math.cos(theta / 2 + math.copysign(pi / 2, -theta)),
				p2[2])
		p3 = (	p3[0] * math.cos(theta / 2  + math.copysign(pi / 2, -theta)) - p3[1] * math.sin(theta / 2 + math.copysign(pi / 2, -theta)), 
				p3[0] * math.sin(theta / 2 + math.copysign(pi / 2, -theta)) + p3[1] * math.cos(theta / 2 + math.copysign(pi / 2, -theta)),
				p3[2])

		#Translate (0, sign(theta) * radius, 0)
		p0 = (	p0[0],	p0[1] + math.copysign(1, theta) * self.radius,	p0[2])
		p1 = (	p1[0],	p1[1] + math.copysign(1, theta) * self.radius, p1[2])
		p2 = (	p2[0],	p2[1] + math.copysign(1, theta) * self.radius, p2[2])
		p3 = (	p3[0],	p3[1] + math.copysign(1, theta) * self.radius, p3[2])

		if theta < 0:
			# p0 -> p1 -> p2 -> p3
			pass
		else:
			# p3 -> p2 -> p1 -> p0
			tmp = p3; p3 = p0; p0 = tmp
			tmp = p2; p2 = p1; p1 = tmp

		p0left = (2 * p0[0] - p1[0], 2 * p0[1] - p1[1], 2 * p0[2] - p1[2])
		p3right = (2 * p3[0] - p2[0], 2 * p3[1] - p2[1], 2 * p3[2] - p2[2])

		bezpoint1 = BezierControl(p0, p0left, p1)
		bezpoint2 = BezierControl(p3, p2, p3right)
		beziercurve = BezierSegment(bezpoint1, bezpoint2)

		return beziercurve

class BezierControl:

	def __init__(self, co, handle_left, handle_right, tilt=0, radius=1):
		self.co = co
		self.handle_left = handle_left
		self.handle_right = handle_right
		self.tilt = tilt
		self.radius = radius

class BezierSegment(Curve):

	def __init__(self, bezpoint1, bezpoint2):
		self.bezpoint_left = bezpoint1
		self.bezpoint_right = bezpoint2
		self.resolution = 24

	#SampleVertex resolution should be related to curvature changing rate (the largest curvature of the curve defines the resolution)
	def sample(self):
		vertices = []
		p0 = self.bezpoint_left.co
		p1 = self.bezpoint_left.handle_right
		p2 = self.bezpoint_right.handle_left
		p3 = self.bezpoint_right.co
		
		for t in np.linspace(0, 1, self.resolution + 1):
			x = (1-t)*(1-t)*(1-t)*p0[0] + 3*(1-t)*(1-t)*t*p1[0] + 3*(1-t)*t*t*p2[0] + t*t*t*p3[0]
			y = (1-t)*(1-t)*(1-t)*p0[1] + 3*(1-t)*(1-t)*t*p1[1] + 3*(1-t)*t*t*p2[1] + t*t*t*p3[1]
			z = (1-t)*(1-t)*(1-t)*p0[2] + 3*(1-t)*(1-t)*t*p1[2] + 3*(1-t)*t*t*p2[2] + t*t*t*p3[2]
			curvature, t, b = self.getdetail(t)
			vertex = SampleVertex((x, y, z), curvature, t, b)
			vertices.append(vertex)

		return vertices

	#Get Cubic Bezier's curvature, and the curve's b, n, t vector, using first and second derivitive
	#Ref https://math.libretexts.org/Core/Calculus/Vector_Calculus/2%3A_Vector-Valued_Functions_and_Motion_in_Space/2.3%3A_Curvature_and_Normal_Vectors_of_a_Curve
	#Torsion with sign 
	# 	http://web.mit.edu/hyperbook/Patrikalakis-Maekawa-Cho/node23.html - "By definition, curvature is non-negative except for planar curve"
	# 	http://web.mit.edu/hyperbook/Patrikalakis-Maekawa-Cho/node24.html
	def getdetail(self, t):
		# B'(t) = 3(1-t)^2(p1-p0)+6(1-t)t(p2-p1)+3t*t(p3-p2)
		# B''(t) = 6(1-t)(p2-2*p1+p0)+6t(p3-2*p2+p1)
		# k = |dT / ds|
		# 	= || B'(t) x B''(t) || / || B'(t) ||^3

		p0 = self.bezpoint_left.co
		p1 = self.bezpoint_left.handle_right
		p2 = self.bezpoint_right.handle_left
		p3 = self.bezpoint_right.co

		vx, vy, vz = self.getspeed(t)
		vnorm = self.distance((0,0,0),(vx, vy, vz))

		vprimex, vprimey ,vprimez = self.getderivitive2(t)
		vprimenorm =self.distance((0,0,0), (vprimex, vprimey, vprimez))

		crossx = vy * vprimez - vz * vprimey
		crossy = vz * vprimex - vx * vprimez
		crossz = vx * vprimey - vy * vprimex
		crossnorm = self.distance((0,0,0), (crossx, crossy, crossz))

		k = crossnorm / math.pow(vnorm, 3)

		# ez = t x n, v x vprime = k|v|^3 * t x n
		# curve r(t)'s second derivitvie of t always point to the center of the curve, while on the x-y plane, normal vector n points to left if follows tangent vector t
		if crossz < 0:
			k *= -1

		t = (vx/vnorm, vy/vnorm, vz/vnorm)
		b = (crossx/crossnorm, crossy/crossnorm, crossz/crossnorm)
		# b = (0, 0, 1)

		return k, t, b

	def getspeed(self, t):

		p0 = self.bezpoint_left.co
		p1 = self.bezpoint_left.handle_right
		p2 = self.bezpoint_right.handle_left
		p3 = self.bezpoint_right.co

		vx = 3*(1-t)*(1-t)*(p1[0]-p0[0])+6*(1-t)*t*(p2[0]-p1[0])+3*t*t*(p3[0]-p2[0])
		vy = 3*(1-t)*(1-t)*(p1[1]-p0[1])+6*(1-t)*t*(p2[1]-p1[1])+3*t*t*(p3[1]-p2[1])
		vz = 3*(1-t)*(1-t)*(p1[2]-p0[2])+6*(1-t)*t*(p2[2]-p1[2])+3*t*t*(p3[2]-p2[2])

		return (vx, vy, vz)

	def getderivitive2(self, t):

		p0 = self.bezpoint_left.co
		p1 = self.bezpoint_left.handle_right
		p2 = self.bezpoint_right.handle_left
		p3 = self.bezpoint_right.co

		vprimex = 6*(1-t)*(p2[0]-2*p1[0]+p0[0])+6*t*(p3[0]-2*p2[0]+p1[0])
		vprimey = 6*(1-t)*(p2[1]-2*p1[1]+p0[1])+6*t*(p3[1]-2*p2[1]+p1[1])
		vprimez = 6*(1-t)*(p2[2]-2*p1[2]+p0[2])+6*t*(p3[2]-2*p2[2]+p1[2])

		return (vprimex, vprimey, vprimez)

class BezierSpline(Curve):

	def __init__(self, spline):
		self.spline = spline
		self.segments, self.sample_vertices = self.get_segments_samples()

	def get_segments_samples(self):

		segments = []
		sample_vertices = []

		for index in range(len(self.spline.bezier_points) - 1):

			segment, samples = self.sample_segment(index, index + 1)
			segments.append(segment)

			if len(sample_vertices) == 0:
				sample_vertices.append(samples[0])
			
			sample_vertices += samples[1:]

		if self.spline.use_cyclic_u:

			segment, samples = self.sample_segment(len(self.spline.bezier_points) - 1, 0)
			segments.append(segment)
			sample_vertices += samples[1:-1]

		return segments, sample_vertices

	def sample_segment(self, ctrlPnt_index, nextCtrlPnt_index):

		ctrlPnt = self.spline.bezier_points[ctrlPnt_index]
		nextPnt = self.spline.bezier_points[nextCtrlPnt_index]

		bezpoint_left = BezierControl(ctrlPnt.co, ctrlPnt.handle_left, ctrlPnt.handle_right, ctrlPnt.tilt, ctrlPnt.radius)
		bezpoint_right = BezierControl(nextPnt.co, nextPnt.handle_left, nextPnt.handle_right, nextPnt.tilt, nextPnt.radius)

		segment = BezierSegment(bezpoint_left, bezpoint_right)
		samples = segment.sample()

		return segment, samples

def getActiveObject():

	return bpy.context.scene.objects.active

def sampleBezierObj(obj):

	if obj == None:
		print('No object is selected')
		return

	if obj.type != 'CURVE':
		print('Selected object is not a curve')
		return

	if (obj.data.splines[0].type != 'BEZIER'):
		print('Selected object is not a bezier curve')
		return

	if bpy.data.objects.find(obj.name + '_sampled') == -1:

		curve = bpy.data.curves.new(name=obj.name + '_sampled', type='CURVE')
		curve.dimensions = '3D'

		newobj = bpy.data.objects.new(obj.name + '_sampled', curve)
		newobj.location = obj.location
		bpy.context.scene.objects.link(newobj)

	sampledobj = bpy.data.objects[obj.name + '_sampled']
	# sampledobj.select = True
	# obj.select = False

	# cleans spline data in the obj to be rewritten
	if (len(sampledobj.data.splines)):
		for spline in sampledobj.data.splines:
			sampledobj.data.splines.remove(spline)

	vertices = []
	for spline in obj.data.splines:
		bezspline = BezierSpline(spline)
		samples = bezspline.sample_vertices
		vertices += samples
		bezspline.viewcurvature(samples, sampledobj)

		polyline = sampledobj.data.splines.new('POLY')
		polyline.points.add(len(samples) - 1)
		for i in range(len(samples)):
			polyline.points[i].co = samples[i].co + (1,)

	return vertices

def saveSampleVertices(samples):

	f = open('D:\Documents\Blender\data\samples.csv', 'w')
	f.write('co.x, co.y, co.z, curvautre, tangent.x, tangent.y, tangent.z, binormal.x, binormal.y, binormal.z\n')
	for sample in samples:
		f.write(str(sample.co[0]) + ',' + str(sample.co[1]) + ',' + str(sample.co[2]) + ',')
		f.write(str(sample.curvature) + ',')
		f.write(str(sample.tangent[0]) + ',' + str(sample.tangent[1]) + ',' + str(sample.tangent[2]) + ',')
		f.write(str(sample.binormal[0])+ ',' + str(sample.binormal[1]) + ',' + str(sample.binormal[2]))
		f.write('\n')

	f.close()

def main():
	clothoid = Clothoid(10, 0, 0.1)
	vertices = clothoid.sample()

	arc = Arc(10 * math.pi / 6, -10)
	vertices = arc.sample()
	# arc.draw([v.co for v in vertices])
	# print([v.co for v in vertices])

	beziercurve = arc.convert2bezier()
	vertices = beziercurve.sample()
	# beziercurve.draw([v.co for v in vertices])
	# print([v.co for v in vertices])

	obj = getActiveObject()
	vertices = sampleBezierObj(obj)
	# saveSampleVertices(vertices)

if __name__ == "__main__":
	main()