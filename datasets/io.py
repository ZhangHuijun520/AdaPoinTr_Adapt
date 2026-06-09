import h5py
import numpy as np
import os

class IO:
    @classmethod
    def get(cls, file_path):
        _, file_extension = os.path.splitext(file_path)

        if file_extension in ['.npy']:
            return cls._read_npy(file_path)
        elif file_extension in ['.pcd', '.ply']:
            return cls._read_pcd(file_path)
        elif file_extension in ['.h5']:
            return cls._read_h5(file_path)
        elif file_extension in ['.txt']:
            return cls._read_txt(file_path)
        else:
            raise Exception('Unsupported file extension: %s' % file_extension)

    # References: https://github.com/numpy/numpy/blob/master/numpy/lib/format.py
    @classmethod
    def _read_npy(cls, file_path):
        return np.load(file_path)
       
    # References: https://github.com/dimatura/pypcd/blob/master/pypcd/pypcd.py#L275
    # Support PCD files without compression ONLY!
    @classmethod
    def _read_pcd(cls, file_path):
        try:
            import open3d
        except (ImportError, OSError) as exc:
            if os.path.splitext(file_path)[1] == '.pcd':
                return cls._read_pcd_without_open3d(file_path)
            raise ImportError(
                "Open3D is required for .ply files, but it failed to load. "
                "On headless servers this is often caused by missing system "
                "libraries such as libX11. Use .pcd/.npy/.h5/.txt data or "
                "install the required system libraries."
            ) from exc
        pc = open3d.io.read_point_cloud(file_path)
        ptcloud = np.array(pc.points)
        return ptcloud

    @classmethod
    def _read_pcd_without_open3d(cls, file_path):
        header = {}

        with open(file_path, 'rb') as f:
            while True:
                line = f.readline()
                if not line:
                    raise ValueError('Invalid PCD file without DATA header: %s' % file_path)

                decoded = line.decode('utf-8', errors='ignore').strip()
                if not decoded or decoded.startswith('#'):
                    continue

                key, *values = decoded.split()
                key = key.upper()
                header[key] = values

                if key == 'DATA':
                    break

            fields = header.get('FIELDS')
            if not fields or 'x' not in fields or 'y' not in fields or 'z' not in fields:
                raise ValueError('PCD file must contain x/y/z fields: %s' % file_path)

            points = int(header.get('POINTS', [0])[0])
            if points == 0:
                width = int(header.get('WIDTH', [0])[0])
                height = int(header.get('HEIGHT', [1])[0])
                points = width * height

            data_type = header['DATA'][0].lower()
            if data_type == 'ascii':
                data = np.loadtxt(f, dtype=np.float32)
                if data.ndim == 1:
                    data = data.reshape(1, -1)
                return data[:, [fields.index('x'), fields.index('y'), fields.index('z')]]

            if data_type != 'binary':
                raise ValueError('Unsupported compressed PCD file: %s' % file_path)

            dtype = cls._pcd_dtype(header)
            data = np.frombuffer(f.read(), dtype=dtype, count=points)
            return np.stack([data['x'], data['y'], data['z']], axis=1).astype(np.float32)

    @classmethod
    def _pcd_dtype(cls, header):
        fields = header['FIELDS']
        sizes = [int(v) for v in header.get('SIZE', ['4'] * len(fields))]
        types = header.get('TYPE', ['F'] * len(fields))
        counts = [int(v) for v in header.get('COUNT', ['1'] * len(fields))]

        dtype_fields = []
        for name, size, typ, count in zip(fields, sizes, types, counts):
            dtype = cls._pcd_numpy_dtype(size, typ)
            if count == 1:
                dtype_fields.append((name, dtype))
            else:
                dtype_fields.append((name, dtype, (count,)))
        return np.dtype(dtype_fields)

    @classmethod
    def _pcd_numpy_dtype(cls, size, typ):
        typ = typ.upper()
        if typ == 'F':
            return {4: '<f4', 8: '<f8'}[size]
        if typ == 'I':
            return {1: '<i1', 2: '<i2', 4: '<i4', 8: '<i8'}[size]
        if typ == 'U':
            return {1: '<u1', 2: '<u2', 4: '<u4', 8: '<u8'}[size]
        raise ValueError('Unsupported PCD field type: %s' % typ)

    @classmethod
    def _read_txt(cls, file_path):
        return np.loadtxt(file_path)

    @classmethod
    def _read_h5(cls, file_path):
        f = h5py.File(file_path, 'r')
        return f['data'][()]
