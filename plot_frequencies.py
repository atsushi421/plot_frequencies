import argparse
from collections import deque

import matplotlib.animation as animation  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import psutil  # type: ignore

MAX_LEGEND_ROWS = 20
BUFFER_SIZE = 30


def main(cpu_indices: list[int]) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    num_cpus = len(cpu_indices)
    cpu_freqs = {cpu_i: deque(maxlen=BUFFER_SIZE) for cpu_i in cpu_indices}  # type: ignore
    lines = [plt.plot([], [], label=f'CPU {cpu_i}')[0] for cpu_i in cpu_indices]
    plt.subplots_adjust(right=0.75)
    ncol = (num_cpus + MAX_LEGEND_ROWS - 1) // MAX_LEGEND_ROWS
    ax.legend(loc='center right', fontsize='small', ncol=ncol, bbox_to_anchor=(1.33, 0.5))

    def init() -> list:
        ax.set_xlim(0, BUFFER_SIZE)
        freq_infos = [cpu_freq_info for cpu_i, cpu_freq_info in enumerate(
            psutil.cpu_freq(percpu=True)) if cpu_i in cpu_indices]
        min_freq_mhz = min([freq_info.min for freq_info in freq_infos])
        max_freq_mhz = max([freq_info.max for freq_info in freq_infos])
        margin = (max_freq_mhz - min_freq_mhz) * 0.01
        ax.set_ylim(((min_freq_mhz * 10**(-3)) - margin),
                    ((max_freq_mhz * 10**(-3)) + margin))
        ax.set_ylabel('CPU Frequency [GHz]')
        return lines

    def update(frame) -> list:
        for cpu_i, freq_info in enumerate(psutil.cpu_freq(percpu=True)):
            if cpu_i in cpu_indices:
                cpu_freqs[cpu_i].append(freq_info.current)

        for cpu_i, line in zip(cpu_indices, lines):
            line.set_data(range(len(cpu_freqs[cpu_i])), list(cpu_freqs[cpu_i]))
        return lines

    _ = animation.FuncAnimation(fig, update, init_func=init, blit=True, interval=100)
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('cpu_indices', nargs='*', type=int,
                        help='List of CPU indexes to plot', default=[])
    args = parser.parse_args()

    if args.cpu_indices:
        cpu_indices = args.cpu_indices
    else:
        cpu_indices = list(range(psutil.cpu_count()))

    main(cpu_indices)
