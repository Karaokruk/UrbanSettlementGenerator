import time # for timing
from math import sqrt, tan, sin, cos, pi, ceil, floor, acos, atan, asin, degrees, radians, log, atan2, acos, asin
from random import *
from numpy import *
from pymclevel import alphaMaterials, MCSchematic, MCLevel, BoundingBox
from mcplatform import *
from collections import defaultdict
from AStar import aStar
import RNG
import copy
import sys
import pickle

# These are a few helpful functions we hope you find useful to use



# sets the block to the given blocktype at the designated x y z coordinate
# *params*
# level : the minecraft world level
# (block, data) : a tuple with block = the block id and data being a subtype
# x,y,z : the coordinate to set
def setBlock(level, (block, data), x, y, z):
	level.setBlockAt((int)(x),(int)(y),(int)(z), block)
    	level.setBlockDataAt((int)(x),(int)(y),(int)(z), data)

# sets the block to the given blocktype at the designated x y z coordinate IF the block is empty (air)
# *params*
# level : the minecraft world level
# (block, data) : a tuple with block = the block id and data being a subtype
# x,y,z : the coordinate to set
def setBlockIfEmpty(level, (block, data), x, y, z):
    tempBlock = level.blockAt((int)(x),(int)(y),(int)(z))
    if tempBlock == 0:
		setBlock(level, (block, data), (int)(x),(int)(y),(int)(z))

# sets every block to the given blocktype from the given x y z coordinate all the way down to ymin if the block is empty
# *params*
# level : the minecraft world level
# (block, data) : a tuple with block = the block id and data being a subtype
# x,y,z : the coordinate to set
# ymin: the minium y in which the iteration ceases
def setBlockToGround(level, (block, data), x, y, z, ymin):
    for iterY in xrange(ymin, (int)(y)):
    	setBlockIfEmpty(level, (block, data), (int)(x),(int)(iterY),(int)(z))


# Given an x an z coordinate, this will drill down a y column from box.maxy until box.miny and return a list of blocks
def drillDown(level, x, z, miny, maxy):
	blocks = []
	for y in xrange(maxy, miny, -1):
		blocks.append(level.blockAt(x, y, z))
		# print level.blockAt(x,y,z)
	return blocks

# Given an x an z coordinate, this will go from box.miny to maxy and return the first block under an air block
def findTerrain(level, x, z, miny, maxy):
	blocks = []
	for y in xrange(miny, maxy):
		#print("y: ", y, " block: ", level.blockAt(x, y, z))
		if level.blockAt(x, y, z) == 0:
			return y-1
		# print level.blockAt(x,y,z)
	return -1
	

# Given an x an z coordinate, this will go from box.miny to maxy and return the first block under an air block
def findTerrainNew(level, x, z, miny, maxy):
	air_like = [0, 6, 17, 18, 30, 31, 32, 37, 38, 39, 40, 59, 81, 83, 85, 104, 105, 106, 107, 111, 141, 142, 161, 162, 175, 78, 79]
	ground_like = [1, 2, 3]
	water_like = [8, 9, 10, 11]

	blocks = []
	for y in xrange(maxy-1, miny-1, -1):
		#print("y: ", y, " block: ", level.blockAt(x, y, z))
		if level.blockAt(x, y, z) in air_like:
			continue
		elif level.blockAt(x, y, z) in water_like:
			return -1
		else:
			return y
		#elif level.blockAt(x, y, z) in ground_like:
		#	return y
		# print level.blockAt(x,y,z)
	return -1

# returns a 2d matrix representing tree trunk locations on an x-z coordinate basis (bird's eye view) in the given box
# *params*
# level: the minecraft world level
# box: the selected subspace of the world
def treeMap(level, box):
	# Creates a 2d array containing z rows, each of x items, all set to 0
	w = abs(box.maxz - box.minz)
	h = abs(box.maxx - box.minx)
	treeMap = zeros((w,h))

	countx = box.minx
	countz = box.minz
	# iterate over the x dimenison of the mapping
	for x in range(h):
		# iterate over the z dimension of the mapping
		countz = box.minz
		for z in range(w):
			# drillDown at this location and get all the blocks in the y-column
			column = drillDown(level, countx, countz, box.miny, box.maxy)
			for block in column:
				# check if any block in this column is a wooden trunk block. If so, there is at this x-z coordinate
				if block == 17:
					treeMap[z][x] = 17
			print treeMap[z][x] ,
			countz += 1
		print ''
		countx += 1
	return treeMap


# returns the box size dimensions in x y and z
def getBoxSize(box):
	return (box.maxx - box.minx, box.maxy - box.miny, box.maxz - box.minz)

# returns an array of blocks after raytracing from (x1,y1,z1) to (x2,y2,z2)
# this uses Bresenham 3d algorithm, taken from a modified version written by Bob Pendleton  
def raytrace((x1, y1, z1), (x2, y2, z2)):
	output = []

	x2 -= 1
	y2 -= 1
	z2 -= 1

	i = 0
	dx = 0
	dy = 0
	dz = 0
	l = 0
	m = 0
	n = 0
	x_inc = 0
	y_inc = 0
	z_inc = 0
	err_1 = 0
	err_2 = 0
	dx2 = 0
	dy2 = 0
	dz2 = 0
	point = [x1,y1,z1]

	dx = x2 - x1
	dy = y2 - y1;
	dz = z2 - z1;
	x_inc = -1  if dx < 0 else 1
	l = abs(dx)
	y_inc = -1 if dy < 0 else 1
	m = abs(dy)
	z_inc = -1 if dz < 0 else 1
	n = abs(dz)
	dx2 = l << 1
	dy2 = m << 1
	dz2 = n << 1
    
	if l >= m and l >= n:
		err_1 = dy2 - l
		err_2 = dz2 - l
		for i in range(l):
			np = (point[0], point[1], point[2])
			output.append(np)
			if err_1 > 0:
				point[1] += y_inc
				err_1 -= dx2

			if err_2 > 0:
				point[2] += z_inc
				err_2 -= dx2

			err_1 += dy2
			err_2 += dz2
			point[0] += x_inc
        
	elif m >= l and m >= n:
		err_1 = dx2 - m
		err_2 = dz2 - m
		for i in range(m):
			np = (point[0], point[1], point[2])
			output.append(np)
			if err_1 > 0:
				point[0] += x_inc
				err_1 -= dy2

			if err_2 > 0:
				point[2] += z_inc
				err_2 -= dy2

			err_1 += dx2
			err_2 += dz2
			point[1] += y_inc
        
	else: 
		err_1 = dy2 - n
		err_2 = dx2 - n
		for i in range(n):
			np = (point[0], point[1], point[2])
			output.append(np)
			if err_1 > 0:
				point[1] += y_inc
				err_1 -= dz2

			if err_2 > 0:
				point[0] += x_inc
				err_2 -= dz2

			err_1 += dy2
			err_2 += dx2
			point[2] += z_inc

	np = (point[0], point[1], point[2])
	output.append(np)
	return output

# class that allows easy indexing of dicts
class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    #__getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    def __getattr__(self, attr):
        if attr.startswith('__'):
            raise AttributeError
        return self.get(attr, None)

# generate and return 3d matrix as in the format matrix[h][w][d] 
def generateMatrix(width, depth, height, options):
	matrix = [[[None for z in range(depth)] for x in range(width)] for y in range(height)]
	return matrix

# get a subsection of a give arean partition based on the percentage
def getSubsection(y_min, y_max, x_min, x_max, z_min, z_max, percentage=0.8):

	width = x_max - x_min
	x_mid = x_min + int(width/2)

	subsection_x_size = int(width*percentage)
	subsection_x_mid = int(subsection_x_size/2)
	subsection_x_min = x_mid - subsection_x_mid
	subsection_x_max = x_mid + subsection_x_mid

	depth = z_max - z_min
	z_mid = z_min + int(depth/2)

	subsection_z_size = int(depth*percentage)
	subsection_z_mid = int(subsection_z_size/2)

	subsection_z_min = z_mid - subsection_z_mid
	subsection_z_max = z_mid + subsection_z_mid

	return (y_min, y_max, subsection_x_min, subsection_x_max, subsection_z_min, subsection_z_max)

# from a list of partitions in the format of (x_min, x_max, z_min, z_max)
# return the partition with the biggest area in the list
def getBiggestPartition(partitions):
	biggestArea = 0
	biggestPartition = None
	for p in partitions:
		width = p[1] - p[0]
		depth =  p[3] - p[2]
		area = width * depth
		print(area, width, depth)
		if area > biggestArea:
			biggestArea = area
			biggestPartition = p
	print(biggestArea)
	return biggestPartition

# fct inner partition from outer and return 4 partitions as the result
def subtractPartition(outer, inner):

	p1 = (outer[0], outer[1], outer[2], inner[2], outer[4], inner[5])
	p2 = (outer[0], outer[1], inner[2], outer[3], outer[4], inner[4])
	p3 = (outer[0], outer[1], inner[3], outer[3], inner[4], outer[5])
	p4 = (outer[0], outer[1], outer[2], inner[3], inner[5], outer[5])

	return (p1,p2,p3,p4)

def getEuclidianDistancePartitions(p1, p2):
	
	p1_center = (p1[0] + int((p1[1]-p1[0])*0.5), p1[2] + int((p1[3]-p1[2])*0.5))
	p2_center = (p2[0] + int((p2[1]-p2[0])*0.5), p2[2] + int((p2[3]-p2[2])*0.5))
	print("EuclidianDistance: ")
	print(p1_center)
	print(p2_center)
	euclidian_distance = getEuclidianDistance(p1_center,p2_center)
	print(euclidian_distance)
	return euclidian_distance

def getEuclidianDistance(p1,p2):
	distance = math.sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2))
	return distance

def getManhattanDistance(p1,p2):
	distance = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
	return distance


# Given an x an z coordinate, this will drill down a y column from box.maxy until box.miny and return a list of blocks
def drillDown(level,box):
	(width, height, depth) = utilityFunctions.getBoxSize(box)
	blocks = []
	for y in xrange(maxy, miny, -1):
		blocks.append(level.blockAt(x, y, z))
		# print level.blockAt(x,y,z)
	return blocks

def cleanProperty(matrix, h_min, h_max, x_min, x_max, z_min, z_max):
	for h in range(h_min, h_max):
		for x in range(x_min, x_max+1):
			for z in range(z_min, z_max+1):
				matrix[h][x][z] = (0,0)

# algorithm to randomly find flat areas given a height map
def getAreasSameHeight(box,terrain):
	validAreas = []

	for i in range(0, 1000):
		random_x = RNG.randint(0, box.maxx-box.minx)
		random_z = RNG.randint(0,box.maxz-box.minz)
		size_x = 15
		size_z = 15
		if checkSameHeight(terrain, 0, box.maxx-box.minx, 0,box.maxz-box.minz, random_x, random_z, size_x, size_z):
			newValidArea = (random_x, random_x+size_x-1, random_z, random_z+size_z-1)
			if newValidArea not in validAreas:
				validAreas.append(newValidArea)

	print("Valid areas found:")
	validAreas = removeOverlaping(validAreas)
	for a in validAreas:
		print(a)

	return validAreas


def hasValidGroundBlocks(x_min, x_max,z_min,z_max, height_map):
	
	for x in range(x_min, x_max):
		for z in range(z_min, z_max):
			if height_map[x][z] == -1:
				return False
	return True

def hasMinimumSize(y_min, y_max, x_min, x_max,z_min,z_max, minimum_h=4, minimum_w=16, minimum_d=16):

	if y_max-y_min < minimum_h or x_max-x_min < minimum_w or z_max-z_min < minimum_d:
		return False
	return True

def hasAcceptableSteepness(x_min, x_max,z_min,z_max, height_map, scoring_function, threshold = 5):
	initial_value = height_map[x_min][z_min]
	score = scoring_function(height_map, x_min, x_max, z_min , z_max , initial_value)
	if score > threshold:
		return False
	return True

# given a box selection, returns a 2d matrix where each element is
# the height of the first non-block air in that x, z position
def getHeightMap(level, box):
	logging.info("Calculating height map...")
	terrain = [[0 for z in range(box.minz,box.maxz)] for x in range(box.minx,box.maxx)]
	
	for d, z in zip(range(box.minz,box.maxz), range(0, box.maxz-box.minz)):
		for w, x in zip(range(box.minx,box.maxx), range(0, box.maxx-box.minx)):
			terrain[x][z] = findTerrainNew(level, w, d, box.miny, box.maxy)

	#print("Terrain Map: ")
	#for x in range(0, box.maxx-box.minx):
	#	print(terrain[x])
	return terrain

def getPathMap(height_map, width, depth):
	pathMap = []

	print(width, depth)
	for x in range(width):
		pathMap.append([])
		for z in range(depth):
			pathMap[x].append(dotdict())

	threshold = 50
	for x in range(width):
		for z in range(depth):

			#if height_map[x][z] == -1:
			#	pathMap[x][z].left = -1
			#	pathMap[x][z].right = -1
			#	pathMap[x][z].down = -1
			#	pathMap[x][z].up = -1
			#	continue

			#left
			if x-1 < 0:
				pathMap[x][z].left = -1
			else:
				pathMap[x][z].left = abs(height_map[x-1][z] - height_map[x][z])
				if pathMap[x][z].left > threshold or height_map[x-1][z] == -1:
					pathMap[x][z].left = -1


			#right
			if x+1 >= width:
				pathMap[x][z].right = -1
			else:
				pathMap[x][z].right = abs(height_map[x][z] - height_map[x+1][z])
				if pathMap[x][z].right > threshold or height_map[x+1][z] == -1:
					pathMap[x][z].right = -1

			#down 
			if z-1 < 0:
				pathMap[x][z].down = -1
			else:
				pathMap[x][z].down = abs(height_map[x][z] - height_map[x][z-1])
				if pathMap[x][z].down > threshold or height_map[x][z-1] == -1:
					pathMap[x][z].down = -1			

			#up 
			if z+1 >= depth:
				pathMap[x][z].up = -1
			else:
				pathMap[x][z].up = abs(height_map[x][z+1] - height_map[x][z])
				if pathMap[x][z].up > threshold or height_map[x][z+1] == -1:
					pathMap[x][z].up = -1
			

	#print("PathMap: ")
	#for x in range(width):
	#	for z in range(depth):
	#		logging.info("[{}],[{}]: {}".format(x, z, pathMap[x][z]))

	return pathMap


def checkSameHeight(terrain, minx, maxx, minz, maxz, random_x, random_z, mininum_w, mininum_d):
	# sample testing
	#print("Testing if valid area starting in ", random_x, random_z)
	#print("limits of matrix: ", minx, maxx, minz, maxz)

	if random_x + mininum_w > maxx or random_z + mininum_d > maxz or terrain[random_x][random_z] == -1:
		return False

	initial_value = terrain[random_x][random_z]

	for x in range(random_x, random_x + mininum_w):
		for z in range(random_z, random_z + mininum_d):
			#print("Checking x, z: ", x, z)
			if terrain[x][z] != initial_value:
				return False

	return True


def getFloodFill(matrix, x_min, x_max, z_min, z_max, random_x, random_z, floodSize):

	initial_value = matrix[random_x][random_z]

	flood_minx = flood_maxx = random_x
	flood_minz = flood_maxz = random_z
	
	for i in range(floodSize+1):

		if random_x - i >= x_min:
			flood_minx = random_x - i

		if random_x + i <= x_max:
			flood_maxx = random_x + i

		if random_z - i >= z_min:
			flood_minz = random_z - i

		if random_z + i <= z_max:
			flood_maxz = random_z + i

	return (flood_minx, flood_maxx, flood_minz, flood_maxz)



def getScoreArea_type1(height_map, min_x, max_x, min_z, max_z, initial_value):
	
	ocurred_values = []
	value = 0
	for x in range(min_x, max_x+1):
		for z in range(min_z, max_z+1):
			difference = initial_value - height_map[x][z]
			if difference not in ocurred_values:
				ocurred_values.append(difference)
  	return len(ocurred_values)

def getScoreArea_type2(height_map, min_x, max_x, min_z, max_z, initial_value):
	
	value = 0
	for x in range(min_x, max_x+1):
		for z in range(min_z, max_z+1):
			value += abs(initial_value - height_map[x][z])
  	return value

def getScoreArea_type3(height_map, min_x, max_x, min_z, max_z, initial_value):
	
	value = 0
	for x in range(min_x, max_x+1):
		for z in range(min_z, max_z+1):

			value += (abs(initial_value - height_map[x][z]))**2
  	return value

def getHeightCounts(matrix, min_x, max_x, min_z, max_z):
	flood_values = {}
	for x in range(min_x, max_x+1):
		for z in range(min_z, max_z+1):
			value = matrix[x][z]
			if value not in flood_values.keys():
				flood_values[value] = 1
			else:
				flood_values[value] += 1
	return flood_values

def getMostOcurredGroundBlock(level, height_map, min_x, max_x, min_z, max_z):
	air_like = [0, 6, 17, 18, 30, 31, 32, 37, 38, 39, 40, 59, 81, 83, 85, 104, 105, 106, 107, 111, 141, 142, 161, 162, 175, 78, 79]
	block_values = {}
	for x in range(min_x, max_x+1):
		for z in range(min_z, max_z+1):
			groundBlock = level.blockAt(x, height_map[x][z], z)
			if groundBlock not in block_values.keys():
				block_values[groundBlock] = 1
			else:
				block_values[groundBlock] += 1

	for key in sorted(block_values, key=block_values.get):
		if key not in air_like:
			return (key, 0)

	grass_block = (2,0)
	return grass_block


# receives a list of areas in the format (x_min, x_max, z_min, z_max)
# returns the same list minus any overlaping areas
def removeOverlaping(areas):
	if len(areas) == 0: return areas

	# get the first area from the list as a valid area
	validAreas = areas[:1]
	areas = areas[1:]

	for i in range(len(areas)):
		current_area = areas[0]
		for index, a in enumerate(validAreas):
			if intersectRect(current_area, a):
				break 
		else:
			validAreas.append(current_area)
		areas = areas[1:]

	return validAreas

# returns whether or not 2 partitions are colliding, must be in the format
# (x_min, x_max, z_min, z_max)
def intersectRect(p1, p2):
    return not (p2[0] >= p1[1] or p2[1] <= p1[0] or p2[3] <= p1[2] or p2[2] >= p1[3])

# update the minecraft world given a matrix with h,w,d dimensions, and each element in the
# (x, y) format, where x is the ID of the block and y the subtype
def updateWorld(level, box, matrix, height, width, depth):
	for y, h in zip(range(box.miny,box.maxy), range(0,height)):
		for x, w in zip(range(box.minx,box.maxx), range(0,width)):
			for z, d in zip(range(box.minz,box.maxz), range(0,depth)):
				if matrix[h][w][d] != None:
					try:
						setBlock(level, (matrix[h][w][d][0], matrix[h][w][d][1]), x, y, z)
					except:
						setBlock(level, (matrix[h][w][d], 0), x, y, z)

def getCentralPoint(x_min, x_max, z_min, z_max):
	x_mid = x_max - int((x_max - x_min)/2)
	z_mid = z_max - int((z_max - z_min)/2)
	return (x_mid, z_mid)

def pavementConnection_old(matrix, x_p1, z_p1, x_p2, z_p2, height_map, pavementBlock = (4,0)):
	print("Connecting ", (x_p1, z_p1), (x_p2, z_p2))
	for x in twoway_range(x_p1, x_p2):
		#h = height_map[x][z_p1]
		h = 100
		matrix[h][x][z_p1] = pavementBlock
		
		

	for z in twoway_range(z_p1, z_p2):
		#h = height_map[x_p2][z]
		h = 100
		matrix[h][x_p2][z] = pavementBlock
		matrix[h+1][x_p2][z] = (0,0)

def pavementConnection(level, matrix, path, build1, build2, height_map, pavementBlock = (4,0), baseBlock=(2,0)):
	logging.info("Connecting road between {} and {}".format(build1.entranceLot, build2.entranceLot))
	block = previous_block = path[0]
	x = block[0]
	z = block[1]
	h = 100

	print
	for i in range(0, len(path)-1):
		block = path[i]
		x = block[0]
		z = block[1]
		#h = 100
		h = height_map[x][z]
		matrix[h][x][z] = pavementBlock
		for j in range(1, 5):
			matrix[h+j][x][z] = (0,0)

		next_block = path[i+1]
		# check if we are moving in the x axis (so to add a new pavement
		# on the z-1, z+1 block)
		if x != next_block[0]:
			# if that side block is walkable
			if z-1 >= 0 and height_map[x][z-1] != -1: 
				matrix[h][x][z-1] = pavementBlock
				for j in range(1,5):
					matrix[h+j][x][z-1] = (0,0)
			if z+1 < len(matrix[h][x]) and height_map[x][z+1] != -1:
				matrix[h][x][z+1] = pavementBlock
				for j in range(1,5):
					matrix[h+j][x][z+1] = (0,0)

		elif z != next_block[1]:
			# check if we are moving in the z axis (so add a new pavement
			# on the x-1 block) and if that side block is walkable
			if x-1 >= 0 and height_map[x-1][z] != -1:
				matrix[h][x-1][z] = pavementBlock
				for j in range(1,5):
					matrix[h+j][x-1][z] = (0,0)
			if x+1 < len(matrix[h]) and height_map[x+1][z] != -1:
				matrix[h][x+1][z] = pavementBlock
				for j in range(1,5):
					matrix[h+j][x+1][z] = (0,0)

def getMST(buildings, pathMap, height_map):
	MST = []
	vertices = []
	partitions = copy.deepcopy(buildings)

	distance_dict = {}
	#print("All partitions")
	for p in partitions:
		distance_dict[p.entranceLot] = {}
	#	print p.entranceLot

	selected_vertex = partitions[RNG.randint(0, len(partitions)-1)]
	#print("Selected: " , selected_vertex)
	vertices.append(selected_vertex)
	partitions.remove(selected_vertex)

	while len(partitions) > 0:
	
		#print("PARTITIONS: ")
		#print(partitions)

		edges = []
		for v in vertices:
			for p in partitions:
				#p1 = getCentralPoint(v[2],v[3],v[4],v[5])
				#p2 = getCentralPoint(p[2],p[3],p[4],p[5])
				p1 = v.entranceLot
				p2 = p.entranceLot

				if p2 in distance_dict[p1].keys():
					distance = distance_dict[p1][p2]
				elif p1 in distance_dict[p2].keys():
					distance = distance_dict[p2][p1]
				else: 

					#distance = getManhattanDistance((p1[1],p1[2]), (p2[1],p2[2]))
					distance = aStar(p1, p2, pathMap, height_map)
					distance_dict[p1][p2] = distance
					distance_dict[p2][p1] = distance
				if distance != None:
					edges.append((len(distance), distance, v, p))
				#if distance != None:
				#	edges.append((distance, distance, v, p))
				else:
					edges.append((-1, None, v, p))
					#print("NO PATHS BETWEEN ", p1, p2)

		edges = sorted(edges)
		#print("Edges: ")
		for e in edges:
			print(e[0], e[2].entranceLot, e[3].entranceLot)

		if len(edges) > 0:
			MST.append((edges[0][0], edges[0][1], edges[0][2], edges[0][3]))
		partitions.remove(edges[0][3])
		vertices.append(edges[0][3])
		#print("partitions left: ", len(partitions))
		#print("MST: ")
		#for m in MST:
		#	print(m)

	return MST

def getMST_Manhattan(buildings, pathMap, height_map):
	MST = []
	vertices = []
	partitions = copy.deepcopy(buildings)

	selected_vertex = partitions[RNG.randint(0, len(partitions)-1)]
	vertices.append(selected_vertex)
	partitions.remove(selected_vertex)

	while len(partitions) > 0:
	
		edges = []
		for v in vertices:
			for p in partitions:				
				p1 = v.entranceLot
				p2 = p.entranceLot
				distance = getManhattanDistance((p1[1],p1[2]), (p2[1],p2[2]))	
				edges.append((distance, v, p))

		edges = sorted(edges)
		if len(edges) > 0:
			MST.append((edges[0][0], edges[0][1], edges[0][2]))
		partitions.remove(edges[0][2])
		vertices.append(edges[0][2])
	return MST
	

#print a matrix given its h,w,d dimensions
def printMatrix(matrix, height, width, depth):
	for h in range(0,height):
		print("matrix at height: ", h)
		for x in range(0,width):
			print(matrix[h][x])

def twoway_range(start, stop):
	return range(start, stop+1, 1) if (start <= stop) else range(start, stop-1, -1)

def convertHeightCoordinates(box,max_h, height):
	for y, h in zip(range(box.miny,box.maxy), range(0,max_h)):
		if y == height:
			#print("Converted Box height ", height, " to ", h)
			return h
	#print("FAILED TO CONVERT BOX HEIGHT ", height)

def convertWidthCoordinates(box,max_x, width):
	for x, w in zip(range(box.minx,box.maxx), range(0,max_x)):
		if x == width:
			#print("Converted Box width ", width, " to ", w)
			return w
	#print("FAILED TO CONVERT BOX WIDTH ", width)

def convertDepthCoordinates(box,max_z, depth):
	for z, d in zip(range(box.minz,box.maxz), range(0,max_z)):
		if z == depth:
			#print("Converted Box depth ", depth, " to ", d)
			return d
	#print("FAILED TO CONVERT BOX DEPTH ", depth)

def convertHeightMatrixToBox(box, max_y, height):
	for y, h in zip(range(box.miny,box.maxy), range(0,max_y)):
		if h == height:
			return y

def convertWidthMatrixToBox(box, max_x, width):
	for x, w in zip(range(box.minx,box.maxx), range(0,max_x)):
		if w == width:
			return x

def convertDepthMatrixToBox(box, max_z, depth):
	for z, d in zip(range(box.minz,box.maxz), range(0,max_z)):
		if d == depth:
			return z

def updateHeightMap(height_map, x_min, x_max, z_min, z_max, height):
	for x in range(x_min, x_max+1):
		for z in range(z_min, z_max+1):
			height_map[x][z] = height

def saveFiles(height_map, pathMap, all_buildings):
	with open('TestMap1HeightMap', 'wb') as matrix_file:
 		pickle.dump(height_map, matrix_file)

 	with open('TestMap1PathMap', 'wb') as matrix_file:
 		pickle.dump(pathMap, matrix_file)

	with open('TestMap1Buildings', 'wb') as matrix_file:
		pickle.dump(all_buildings, matrix_file)
