from collections import deque

import matplotlib.animation as animation  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import psutil  # type: ignore

MAX_LEGEND_ROWS = 20

fig, ax = plt.subplots(figsize=(10, 4))
num_cpus = psutil.cpu_count()
cpu_freqs = deque(maxlen=30)  # type: ignore
lines = [plt.plot([], [], label=f'CPU {i}')[0] for i in range(num_cpus)]

plt.subplots_adjust(right=0.75)
ncol = (num_cpus + MAX_LEGEND_ROWS-1) // MAX_LEGEND_ROWS
ax.legend(
    loc='center right', fontsize='small', ncol=ncol,
    framealpha=1.0, fancybox=True, facecolor='white', bbox_to_anchor=(1.33, 0.5)
)


def init() -> list:
    for line in lines:
        line.set_data([], [])
    ax.set_xlim(0, cpu_freqs.maxlen)
    ax.set_ylim(((psutil.cpu_freq().min / 10**3) * 0.99), ((psutil.cpu_freq().max / 10**3) * 1.01))
    ax.set_ylabel('CPU Frequency [GHz]')
    return lines


def update(frame) -> list:
    freqs = [f.current for f in psutil.cpu_freq(percpu=True)]
    cpu_freqs.append(freqs)

    for i, line in enumerate(lines):
        line.set_data(range(len(cpu_freqs)), [f[i] for f in cpu_freqs])
    return lines


ani = animation.FuncAnimation(fig, update, init_func=init, blit=True, interval=100)
plt.show()
