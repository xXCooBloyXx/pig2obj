import ctypes
import os

zstd = ctypes.CDLL("./utils/libzstd.dll")

def zstd_decompress(data, uncompressed_size=None):
    if uncompressed_size is None:
        uncompressed_size = zstd.ZSTD_getDecompressedSize(data, len(data))

    decompressed_buffer = ctypes.create_string_buffer(uncompressed_size)

    result = zstd.ZSTD_decompress(decompressed_buffer, uncompressed_size, data, len(data))
    if zstd.ZSTD_isError(result):
        raise ValueError(f"Decompression error: {zstd.ZSTD_getErrorName(result)}")

    return decompressed_buffer.raw[:result]
