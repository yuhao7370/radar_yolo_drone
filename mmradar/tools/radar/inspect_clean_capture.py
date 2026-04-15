#!/usr/bin/env python3
import argparse
import os
import struct
import sys


def main():
    parser = argparse.ArgumentParser(description="检查清洗后的雷达文件 clean.bin")
    parser.add_argument("file", help="clean.bin 文件路径")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在：{args.file}", file=sys.stderr)
        return 1

    file_size = os.path.getsize(args.file)
    if file_size < 4:
        print(f"错误：文件太小，无法读取 trip_len：{args.file}", file=sys.stderr)
        return 1

    with open(args.file, "rb") as f:
        raw = f.read()

    trip_len = struct.unpack_from("<i", raw, 0)[0]
    if trip_len <= 0:
        print(f"错误：trip_len 非法：{trip_len}", file=sys.stderr)
        return 1

    channel_block_bytes = 8 + 2 * trip_len
    trip_bytes = 4 * channel_block_bytes
    payload_bytes = file_size - 4
    trip_count = payload_bytes // trip_bytes
    remainder = payload_bytes % trip_bytes

    first_now_pt = struct.unpack_from("<Q", raw, 4)[0] if file_size >= 12 else None
    preview_count = min(8, trip_len)
    samples = struct.unpack_from(f"<{preview_count}H", raw, 12) if file_size >= 12 + 2 * preview_count else ()

    print(f"文件: {args.file}")
    print(f"文件大小(bytes): {file_size}")
    print(f"trip_len: {trip_len}")
    print(f"单通道块大小(bytes): {channel_block_bytes}")
    print(f"单 trip 大小(bytes): {trip_bytes}")
    print(f"trip_count: {trip_count}")
    print(f"尾部余数(bytes): {remainder}")

    if first_now_pt is not None:
        print(f"首个 now_pt: {first_now_pt}")
    else:
        print("首个 now_pt: 无法读取")

    if samples:
        print(f"首个通道块前{preview_count}个采样: {list(samples)}")
    else:
        print("首个通道块采样预览: 无法读取")

    print("单 trip 字节布局:")
    print("  offset 0x00..0x03: int32 trip_len")
    print("  trip[n].ch[k] = <uint64 now_pt><uint16 samples[trip_len]>")
    print(f"  ch0 offset = 4 + n * {trip_bytes} + 0 * {channel_block_bytes}")
    print(f"  ch1 offset = 4 + n * {trip_bytes} + 1 * {channel_block_bytes}")
    print(f"  ch2 offset = 4 + n * {trip_bytes} + 2 * {channel_block_bytes}")
    print(f"  ch3 offset = 4 + n * {trip_bytes} + 3 * {channel_block_bytes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
