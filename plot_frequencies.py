import argparse
import re
import subprocess
from collections import deque

import matplotlib.animation as animation  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import psutil  # type: ignore

MAX_LEGEND_ROWS = 20
BUFFER_SIZE = 30


def get_cpu_freq_range(cpu_i: int) -> tuple:
    try:
        with open(f'/sys/devices/system/cpu/cpu{cpu_i}/cpufreq/scaling_available_frequencies') as f:
            freqs = [int(freq) for freq in f.read().split()]
    except FileNotFoundError:
        raise RuntimeError('Cannot get scaling_available_frequencies. '
                           'Please add "intel_pstate=disable" to kernel parameters.')
    return min(freqs), max(freqs)


def get_current_cpu_freq() -> list[float]:
    with open('/proc/cpuinfo') as f:
        content = f.read()
    return [float(match.group(1)) for match in re.finditer(r'cpu MHz\s+:\s+(\d+.\d+)', content)]


def main(cpu_indices: list[int], no_lib: bool) -> None:
    # Initialize plot
    fig, ax = plt.subplots(figsize=(10, 4))
    num_cpus = len(cpu_indices)
    cpu_freqs = {cpu_i: deque(maxlen=BUFFER_SIZE) for cpu_i in cpu_indices}  # type: ignore
    lines = [plt.plot([], [], label=f'CPU {cpu_i}')[0] for cpu_i in cpu_indices]
    plt.subplots_adjust(right=0.75)
    ncol = (num_cpus + MAX_LEGEND_ROWS - 1) // MAX_LEGEND_ROWS
    ax.legend(loc='center right', fontsize='small', ncol=ncol, bbox_to_anchor=(1.33, 0.5))

    def init() -> list:
        ax.set_xlim(0, BUFFER_SIZE)
        if no_lib:
            min_freq_ghz = min(get_cpu_freq_range(cpu_i)[0] for cpu_i in cpu_indices) * 10**(-3)
            max_freq_ghz = max(get_cpu_freq_range(cpu_i)[1] for cpu_i in cpu_indices) * 10**(-3)
        else:
            freq_infos = [cpu_freq_info for cpu_i, cpu_freq_info in enumerate(
                psutil.cpu_freq(percpu=True)) if cpu_i in cpu_indices]
            min_freq_ghz = min([freq_info.min for freq_info in freq_infos]) * 10**(-3)
            max_freq_ghz = max([freq_info.max for freq_info in freq_infos]) * 10**(-3)
        margin = (max_freq_ghz - min_freq_ghz) * 0.01
        ax.set_ylim((min_freq_ghz - margin), (max_freq_ghz + margin))
        ax.set_ylabel('CPU Frequency [GHz]')
        return lines

    def update(frame) -> list:
        if no_lib:
            for cpu_i, freq_mhz in enumerate(get_current_cpu_freq()):
                cpu_freqs[cpu_i].append(freq_mhz)
        else:
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
    parser.add_argument('no_lib', action='store_true',
                        help='Not use psutil library', default=True)
    args = parser.parse_args()

    if args.cpu_indices:
        cpu_indices = args.cpu_indices
    elif args.no_lib:
        cpu_indices = list(range(int(subprocess.Popen(
            ['nproc'], shell=True, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip())))
    else:
        cpu_indices = list(range(psutil.cpu_count()))

    main(cpu_indices, args.no_lib)
