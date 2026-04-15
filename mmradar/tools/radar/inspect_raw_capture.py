#!/usr/bin/env python3
import argparse
import array
import os
import statistics
import sys


def load_words(path):
    with open(path, "rb") as f:
        raw = f.read()
    odd_byte = len(raw) % 2
    if odd_byte:
        raw = raw[:-1]

    words = array.array("H")
    words.frombytes(raw)
    if sys.byteorder != "little":
        words.byteswap()
    return words, odd_byte


def marker_gaps(words, mask):
    indices = [idx for idx, word in enumerate(words) if word & mask]
    if len(indices) < 2:
        return indices, []
    return indices, [indices[i] - indices[i - 1] for i in range(1, len(indices))]


def estimate_trip_len(words):
    if not words:
        return None

    now_pt = 0
    first_mux = (words[now_pt] & 0x0002) >> 1
    while now_pt < len(words) and first_mux == ((words[now_pt] & 0x0002) >> 1):
        now_pt += 1
    if now_pt >= len(words):
        return None

    pre_mux = (words[now_pt] & 0x0002) >> 1
    pre_trip_flag = now_pt
    distances = []

    while now_pt < len(words):
        mux = (words[now_pt] & 0x0002) >> 1
        if pre_mux != mux:
            pre_mux = mux
            gap = now_pt - pre_trip_flag
            if gap > 20:
                distances.append(gap)
                pre_trip_flag = now_pt
        now_pt += 1

    if not distances:
        return None

    avg_gap = sum(distances) / len(distances)
    return {
        "toggle_count": len(distances),
        "avg_gap_words": avg_gap,
        "estimated_trip_len": avg_gap / 4.0 * 0.995,
        "min_gap_words": min(distances),
        "max_gap_words": max(distances),
    }


def main():
    parser = argparse.ArgumentParser(description="检查原始雷达采样文件 sar_*.bin")
    parser.add_argument("file", help="原始采样文件路径")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在：{args.file}", file=sys.stderr)
        return 1

    words, odd_byte = load_words(args.file)
    file_size = os.path.getsize(args.file)

    bit0_idx, bit0_gaps = marker_gaps(words, 0x0001)
    bit1_idx, bit1_gaps = marker_gaps(words, 0x0002)
    estimate = estimate_trip_len(words)

    print(f"文件: {args.file}")
    print(f"文件大小(bytes): {file_size}")
    print(f"16位样本数: {len(words)}")
    print(f"尾部残余奇数字节: {odd_byte}")
    print(f"bit0 标记数: {len(bit0_idx)}")
    print(f"bit1 置位数: {len(bit1_idx)}")

    if bit0_gaps:
        print(f"bit0 间隔统计: min={min(bit0_gaps)} max={max(bit0_gaps)} avg={statistics.mean(bit0_gaps):.3f}")
    else:
        print("bit0 间隔统计: 不足以计算")

    if bit1_gaps:
        print(f"bit1 间隔统计: min={min(bit1_gaps)} max={max(bit1_gaps)} avg={statistics.mean(bit1_gaps):.3f}")
    else:
        print("bit1 间隔统计: 不足以计算")

    if estimate is None:
        print("估计 trip 长度: 无法从 mux 翻转中得到稳定结果")
    else:
        print(
            "估计 trip 长度(每通道样本数): "
            f"{estimate['estimated_trip_len']:.3f} "
            f"(toggle_count={estimate['toggle_count']}, "
            f"avg_gap_words={estimate['avg_gap_words']:.3f}, "
            f"min_gap_words={estimate['min_gap_words']}, "
            f"max_gap_words={estimate['max_gap_words']})"
        )

    preview = [int(word) for word in words[:8]]
    print(f"前8个原始字: {preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
