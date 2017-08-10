import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def readCSV(filename):

	xarray = []
	yarray = []
	zarray = []

	with open(filename, 'r') as f:
		for line in f:
			if (line[0] == 'T'):
				continue
			x, y , z = [float(s) for s in line.split(',')]
			xarray.append(x)
			yarray.append(y)
			zarray.append(z)

	return xarray, yarray, zarray

def main():

	filename = "../data/Central.csv"
	xarray, yarray, zarray = readCSV(filename)

	fig = plt.figure()
	ax = fig.gca(projection='3d')
	
	ax.plot(xarray, yarray, zarray, label='parametric curve')

	plt.show()

if __name__ == "__main__":
	main()