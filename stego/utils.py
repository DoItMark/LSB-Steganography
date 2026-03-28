import struct
import numpy as np


def bytes_to_bits(data):
    """Convert bytes to a sequence of bits.

    Useful in LSB steganography for expanding payload bytes into a bit stream
    that can be embedded into image pixel channels.
    """
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def bits_to_bytes(bits):
    """Convert a sequence of bits back into a bytes object.

    Used to reconstruct payload bytes from extracted bit stream during decoding.
    Pads a partial final byte with zeros if necessary.
    """
    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            chunk = chunk + [0] * (8 - len(chunk))
        val = 0
        for b in chunk:
            val = (val << 1) | b
        out.append(val)
    return bytes(out)


def parse_scheme(scheme_str):
    """Parse a scheme string like '2-3-1' into integer R/G/B bit allocations."""
    parts = scheme_str.split('-')
    return int(parts[0]), int(parts[1]), int(parts[2])


def scheme_to_byte(scheme_str):
    """Encode a scheme string into a compact single byte for header storage."""
    r, g, b = parse_scheme(scheme_str)
    return (r << 4) | (g << 2) | b


def byte_to_scheme(val):
    """Decode compact header scheme byte back into 'R-G-B' string."""
    r = (val >> 4) & 0xF
    g = (val >> 2) & 0x3
    b = val & 0x3
    return f"{r}-{g}-{b}"


def pack_header(is_file, is_encrypted, is_random, scheme_str, payload_len, filename):
    """Pack metadata header for payload embedding.

    Header contains version, flags, scheme, payload length, filename length and filename bytes.
    """
    flags = 0
    if is_file: flags |= 0x01
    if is_encrypted: flags |= 0x02
    if is_random: flags |= 0x04

    scheme_byte = scheme_to_byte(scheme_str)
    fname_bytes = filename.encode('utf-8') if filename else b''
    fname_len = len(fname_bytes)

    header = bytearray()
    header.append(0x01)  # version
    header.append(flags)
    header.append(scheme_byte)
    header += struct.pack('>I', payload_len)
    header += struct.pack('>H', fname_len)
    header += fname_bytes
    return bytes(header)


def unpack_header_from_bits(bits):
    """Unpack and validate header data from an extracted bit stream.

    Returns metadata plus the number of header bits consumed by the payload.
    """
    if len(bits) < 72:
        raise ValueError("Not enough data to read header")

    hdr_bytes = bits_to_bytes(bits[:72])
    version = hdr_bytes[0]
    if version != 0x01:
        raise ValueError(f"Unknown stego version: {version}")

    flags = hdr_bytes[1]
    is_file = bool(flags & 0x01)
    is_encrypted = bool(flags & 0x02)
    is_random = bool(flags & 0x04)

    scheme_byte = hdr_bytes[2]
    scheme_str = byte_to_scheme(scheme_byte)

    payload_len = struct.unpack('>I', hdr_bytes[3:7])[0]
    fname_len = struct.unpack('>H', hdr_bytes[7:9])[0]

    total_hdr_bytes = 9 + fname_len
    total_hdr_bits = total_hdr_bytes * 8

    if len(bits) < total_hdr_bits:
        raise ValueError("Not enough data for filename in header")

    fname_raw = bits_to_bytes(bits[72:total_hdr_bits])
    filename = fname_raw[:fname_len].decode('utf-8', errors='replace')

    return {
        'is_file': is_file, 'is_encrypted': is_encrypted,
        'is_random': is_random, 'scheme': scheme_str,
        'payload_len': payload_len, 'filename': filename,
        'header_bits': total_hdr_bits
    }


def calc_mse_psnr(orig, stego):
    """Calculate MSE and PSNR between original and stego image arrays.

    Used to report image quality degradation after LSB embedding.
    """
    diff = orig.astype(np.float64) - stego.astype(np.float64)
    mse = np.mean(diff ** 2)
    if mse == 0:
        return 0.0, float('inf')
    psnr = 10 * np.log10(255**2 / mse)
    return mse, psnr