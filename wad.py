import struct

Lump = tuple[bytes, bytes]

class LumpList(list):
	def __getitem__(self, index):
		if type(index) is str:
			index = index.encode('ascii')
		if type(index) is bytes:
			for (name, data) in self:
				if name == index:
					return data
			raise KeyError(f'No lump named {repr(index)} was found.')
		else:
			return super().__getitem__(index)
	
	def __setitem__(self, index, newdata):
		if type(index) is str:
			index = index.encode('ascii')
		if type(index) is bytes:
			for i in range(len(self)):
				(name, data) = self[i]
				if name == index:
					self[i] = (name, newdata)
					return
			self.append((index, newdata))
		else:
			super().__setitem__(index, newdata)
	
	def __delitem__(self, index):
		if type(index) is str:
			index = index.encode('ascii')
		if type(index) is bytes:
			for i in range(len(self)):
				(name, data) = self[i]
				if name == index:
					del self[i]
					return
			raise KeyError(f'No lump named {repr(index)} was found.')
		else:
			super().__delitem__(index)

class WADError(Exception):
	pass
class WADFormatError(WADError):
	def __init__(self, msg, filename=None):
		super().__init__(msg)
		self.filename = filename

def load(filename:str) -> LumpList:
	with open(filename, 'rb') as f:
		def error(explanation):
			return WADFormatError(f'{filename} is not a WAD file ({explanation})', filename)

		magic = f.read(4)
		if magic not in (b'PWAD', b'IWAD'):
			raise error(f'invalid magic number {repr(magic)}')

		nlumps_b = f.read(4)
		if len(nlumps_b) < 4:
			raise error('EOF while reading lump count')
		nlumps = int.from_bytes(nlumps_b, 'little', signed=False)

		dirloc_b = f.read(4)
		if len(dirloc_b) < 4:
			raise error('EOF while reading directory location')
		dirloc = int.from_bytes(dirloc_b, 'little', signed=False)

		f.seek(dirloc, 0)
		
		lump_tbl = []
		for i in range(nlumps):
			dataloc_b = f.read(4)
			if len(dataloc_b) < 4:
				raise error(f'EOF while reading location of lump {i}')
			dataloc = int.from_bytes(dataloc_b, 'little', signed=False)

			size_b = f.read(4)
			if len(size_b) < 4:
				raise error(f'EOF while reading size of lump {i}')
			size = int.from_bytes(size_b, 'little', signed=False)

			name = f.read(8)
			if len(name) < 8:
				raise error(f'EOF while reading name of lump {i}')
			try:
				name = name[:name.index(b'\0')]
			except ValueError:
				pass

			lump_tbl.append((dataloc, size, name))

		lumps = LumpList()
		for (dataloc, size, name) in lump_tbl:
			f.seek(dataloc, 0)
			data = f.read(size)
			if len(data) < size:
				raise error(f'EOF while reading lump {repr(name)}')
			lumps.append((name, data))
	
	return lumps

def save(filename:str, lumps:list[Lump], magic:bytes=b'PWAD'):
	dirloc = 12
	lumplocs = []
	p = dirloc + 16*len(lumps)
	for (name, data) in lumps:
		if not 1 <= len(name) <= 8:
			raise WADError(f'Invalid lump name {repr(name)} (must be 1-8 bytes)')
		lumplocs.append(p)
		p += len(data)
	
	with open(filename, 'wb') as f:
		f.write(magic)
		f.write(struct.pack('<II', len(lumps), dirloc))
		assert f.tell() == dirloc

		for i in range(len(lumps)):
			(name, data) = lumps[i]
			f.write(struct.pack('<II', lumplocs[i], len(data)))
			f.write(name.ljust(8, b'\0'))
		for i in range(len(lumps)):
			assert f.tell() == lumplocs[i]
			(name, data) = lumps[i]
			f.write(data)
