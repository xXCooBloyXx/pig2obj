from utils.reader import Reader
from utils.zstd import zstd_decompress
import os

debugMode = False

for filename in os.listdir("pig/"):
	if filename.endswith(".pig"):
		print(f"Converting file {filename}")
		read = Reader(open("pig/"+filename, "rb").read())
		objfile = open("obj/"+filename[:-4]+".obj", "w")

		nodes = []

		read.stream.skip(4)
		for i in range(read.readUShort()):
			read.stream.skip(4)
			nodes.append(read.readUTF())
			read.stream.skip(49)

		gv = 1
		read.stream.skip(1)
		for i in range(read.readUShort()):
			read.stream.skip(4)
			nodeid = read.readUInt()
			for j in range(read.readUShort()):
				read.stream.skip(5)
				hasSkeleton = read.readUShort()
				read.stream.skip(24)
				for k in range(read.readUShort()):
					meshName = f"{nodes[nodeid]}_{k}"
					print(f"Converting mesh {meshName}...")
				
					read.stream.skip(4)
					
					flags = read.readUInt()
					fvf = read.readUInt()
					
					hasVertices = (fvf & 0x1) != 0
					hasNormals = (fvf & 0x2) != 0
					hasTangents = (fvf & 0x4) != 0
					hasUnk1 = (fvf & 0x8) != 0
					hasUnk2 = (fvf & 0x40) != 0
					hasUV1 = (fvf & 0x80) != 0
					hasUV2 = (fvf & 0x100) != 0
					hasPackedVertexData = (flags & 0x1) != 0
					
					read.stream.skip(12)
					if hasPackedVertexData:
						offset = [read.readFloat(), read.readFloat(), read.readFloat()]
						scale = [read.readFloat(), read.readFloat(), read.readFloat()]
					else:
						print("[INFO] mesh has not packed vertex data")
					verticesCount = read.readUShort()
					facesCount = read.readUInt()
					materialName = read.readUTF()
					read.stream.skip(2)
					while read.readUShort() != 46374:
						read.stream.skip(-1)
					read.stream.skip(-10)
					compressedSize = read.readUInt()
					decompressedSize = read.readUInt()
					decompressedData = zstd_decompress(read.stream.read(compressedSize), decompressedSize)
					data = Reader(decompressedData)
					if debugMode:
						print("[DEBUG] saving decompressed(raw) mesh data")
						with open("pig/"+filename[:-4]+"_"+meshName+".pig.raw", "wb") as rawData:
							rawData.write(decompressedData)

					objfile.write(f"o {meshName}\n")
					if hasVertices:
						if hasPackedVertexData:
							for l in range(verticesCount):
								objfile.write(f"v {data.readNShort()+offset[0]*scale[0]} {data.readNShort()+offset[1]*scale[1]} {data.readNShort()+offset[2]*scale[2]}\n")
								data.stream.skip(2)
						else:
							for l in range(verticesCount):
								objfile.write(f"v {data.readFloat()} {data.readFloat()} {data.readFloat()}\n")
					if hasNormals:
						for l in range(verticesCount):
							objfile.write(f"vn {data.readNByte()} {data.readNByte()} {data.readNByte()}\n")
							data.stream.skip(1)
					else:
						print("[INFO] mesh has no custom normals")
						data.stream.seek(0)
						if hasPackedVertexData:
							for l in range(verticesCount):
								objfile.write(f"vn {data.readNShort()+offset[0]*scale[0]} {data.readNShort()+offset[1]*scale[1]} {data.readNShort()+offset[2]*scale[2]}\n")
								data.stream.skip(2)
						else:
							for l in range(verticesCount):
								objfile.write(f"vn {data.readFloat()} {data.readFloat()} {data.readFloat()}\n")
					
					if hasTangents:
						data.stream.skip(verticesCount*4)

					if hasUnk1:
						data.stream.skip(verticesCount*4)
					
					if hasUnk2:
						data.stream.skip(verticesCount*4)
						
					if hasUV1:
						for l in range(verticesCount):
							objfile.write(f"vt {data.readFloat()} {1-data.readFloat()}\n")
					
					if hasUV2:
						print("[INFO] mesh has second UV layer")
						data.stream.skip(verticesCount*8)
					
					if hasSkeleton:
						data.stream.skip(verticesCount*4) # indices
						data.stream.skip(verticesCount*4) # weights
						
					f3 = gv
					objfile.write(f"usemtl {materialName}\n")
					for l in range(round(facesCount/3)):
						f1 = data.readShort() + f3
						f2 = data.readShort() + f1
						f3 = data.readShort() + f2
						objfile.write(f"f {f1}/{f1}/{f1} {f2}/{f2}/{f2} {f3}/{f3}/{f3}\n")
					gv += verticesCount
					
					if hasSkeleton:
						read.stream.skip(9)
						unkSize = read.readUInt()
						read.stream.skip(unkSize+4)
					objfile.flush()

		objfile.close()
print("Done!")
os.system("pause")