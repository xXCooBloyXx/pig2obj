from utils.reader import Reader
import glob
import zstd
import os
import numpy as np

choice = 1
if choice == 1:
	filepath = "C:\\Users\\xXCoo\\Downloads\\MinionRush\\files\\models\\*.pig"
else:
	filepath = "C:\\Users\\xXCoo\\Downloads\\MinionRush\\pigEditor\\*.pig"

for filename in glob.glob(filepath):
	print(f"Converting {os.path.basename(filename)}...")
	filenamestr = os.path.basename(filename).split('.')[-2]
	file = open(f"./objs/{filenamestr}.obj", "w")
	filemtl = open(f"./objs/{filenamestr}.mtl", "w")
	try:
		file.write(f"mtllib {filenamestr}.mtl\n")
		
		read = Reader(open(filename, "rb").read())

		marker = read.readInt32()
		nodescount = read.readInt16()

		nodenames = []
		for i in range(nodescount):
			marker = read.readInt32()
			nodenames.append(read.readString())
			nodetype = read.readByte()
			parentid = read.readInt16()

			positions = [read.readFloat(), read.readFloat(), read.readFloat()]
			rotations = [read.readFloat(), read.readFloat(), read.readFloat(), read.readFloat()]
			scales = [read.readFloat(), read.readFloat(), read.readFloat()]

			unk1 = read.readFloat()
			unk2 = read.readInt16()
		print(f"  nodes: {len(nodenames)}")
		unk = read.readByte()

		objectescount = read.readInt16()
		for i in range(objectescount):
			marker = read.readInt32()
			nodeid = read.readInt32()
			
			lodscount = read.readInt16()
			for i in range(lodscount):
				lodid = read.readByte()
				marker = read.readInt32()

				haverig = read.readInt16()
				boundingbox_minx = read.readFloat()
				boundingbox_miny = read.readFloat()
				boundingbox_minz = read.readFloat()
				boundingbox_maxx = read.readFloat()
				boundingbox_maxy = read.readFloat()
				boundingbox_maxz = read.readFloat()

				meshescount = read.readInt16()
				print(f"  meshes({meshescount}): ")
				cv = 1
				for i in range(meshescount):
					print(f"    mesh {i+1}:")
					file.write(f"o {nodenames[-lodid]}_mesh_{i+1}\n")
					marker = read.readInt32()
					bitflags = read.readInt32()
					fvf = read.readInt32()

					pivotpoint_x = read.readFloat()
					pivotpoint_y = read.readFloat()
					pivotpoint_z = read.readFloat()

					if (bitflags & 1 != 0):
						posx = read.readFloat()
						posy = read.readFloat()
						posz = read.readFloat()
						sizex = read.readFloat()
						sizey = read.readFloat()
						sizez = read.readFloat()

					vertexescount = read.readUInt16()
					print(f"      verticesCount: {vertexescount}")
					facescount = read.readInt32()
					print(f"      facesCount: {facescount}")
					materialname = read.readString()
					print(f"      material {materialname}:")
					unk = read.readInt16()
					
					#Shitty beacuse its probably something with bitflags or fvf
					while True:
						texturelength = read.readInt16()
						if texturelength != 0:
							texturefile = read.stream.read(texturelength).decode("utf-8")
							print(f"        textureFile: {texturefile}")
							unk = read.readInt16()
						else:
							read.stream.skip(-4)
							while True:
								if read.readByte() == 2:
									read.stream.skip(-1)
									break
							break
					compression = read.readByte()
					compressedsize = read.readInt32()
					uncompressedsize = read.readInt32()
					data_d = zstd.decompress(read.stream.read(compressedsize), uncompressedsize)
					data = Reader(data_d)
					writedata = False
					if writedata:
						f = open(f"data_mesh{i+1}", "wb")
						f.write(data_d)
					if (fvf & 1) != 0: # Vertices
						vers = []
						for i in range(vertexescount):
							x, y, z = [data.readInt16() / 32767 for _ in range(3)]
							rotated_vertex = np.dot(np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]]), np.array([[x], [y], [z]]))
							file.write(f"v {rotated_vertex[0, 0]} {rotated_vertex[1, 0]} {rotated_vertex[2, 0]}\n")
							data.stream.skip(2)
					if (fvf & 2) != 0: # Normals
						norms = []
						for i in range(vertexescount):
							x, y, z = [data.readByte() / 127 for _ in range(3)]
							rotated_normal = np.dot(np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]]), np.array([[x], [y], [z]]))
							norms.append(rotated_normal[0, 0])
							norms.append(rotated_normal[1, 0])
							norms.append(rotated_normal[2, 0])
							norms.append(data.readByte())
					if (fvf & 4) != 0:
						for i in range(vertexescount):
							data.stream.skip(4)
					if (fvf & 8) != 0:
						for i in range(vertexescount):
							data.stream.skip(4)
					if (fvf & 0x40) != 0:
						for i in range(vertexescount):
							data.stream.skip(4)
					if (fvf & 0x80) != 0: # uv1
						uvs1 = []
						for i in range(vertexescount):
							for i in range(2):
								uvs1.append(data.readFloat())
					if (fvf & 0x100) != 0: # uv2
						for i in range(vertexescount):
							data.stream.skip(8)
					if haverig != 0:
						for i in range(vertexescount):
							data.stream.skip(8)
					verts = []
					for i in range(facescount):
						try:
							for i in range(3):
								verts.append(data.readInt16())
						except Exception as e:
							#print(e)
							pass
					
					# I used ZDev code!
					for i in range(0,len(norms),4):
						file.write(f"vn {norms[i]} {norms[i+1]} {norms[i+2]}\n")
					for i in range(0,len(uvs1),2):
						file.write(f"vt {uvs1[i]} {uvs1[i+1]}\n")
					filemtl.write(f"newmtl {materialname}\n")
					file.write(f"usemtl {materialname}\ns off\n")
					z = 0
					for i in range(0,len(verts),3):
						x = verts[i] + z
						y = verts[i+1] + x
						z = verts[i+2] + y
						part1 = f"{cv+x}/{cv+x}/{cv+x}"
						part2 = f"{cv+y}/{cv+y}/{cv+y}"
						part3 = f"{cv+z}/{cv+z}/{cv+z}"
						file.write(f"f {part1} {part2} {part3}\n")
					cv += vertexescount
					
					#2nd unknown data
					unk = read.stream.skip(8)
					compression = read.readByte()
					compressedsize = read.readInt32()
					uncompressedsize = read.readInt32()
					data = zstd.decompress(read.stream.read(compressedsize), uncompressedsize)
	except Exception as e:
		print(f"Failed to convert {os.path.basename(filename)}... Skipping")
		print(f"Error: {e}")
		file.close()
		os.remove(f"./objs/{filenamestr}.obj")
		filemtl.close()
		os.remove(f"./objs/{filenamestr}.mtl")
		pass