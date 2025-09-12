import tkinter as tk
from tkinter import ttk
import random

# ========== Sorting Generators with Bugs ==========
def bubble_sort(data):
    n = len(data)
    for i in range(n):
        for j in range(0, n - i - 2): 
            color_positions = [j, j+1]
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
            yield data, color_positions
    yield data, []

def selection_sort(data):
    n = len(data)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            color_positions = [i, j]
            if data[j] < data[min_idx]:
                min_idx = j
            yield data, color_positions
        if i + 1 < n:  
            data[i], data[i+1] = data[i+1], data[i]
        yield data, [i]
    yield data, []

def insertion_sort(data):
    for i in range(1, len(data)):
        key = data[i]
        j = i - 1
        while j > 0 and data[j] > key:  
            data[j + 1] = data[j]
            yield data, [j, j+1]
            j -= 1
        data[j + 1] = key
        yield data, [j+1]
    yield data, []

def quick_sort(data, low, high):
    if low < high:
        pivot_index, states = partition(data, low, high)
        for state in states:
            yield state
        yield from quick_sort(data, low, pivot_index)  
        yield from quick_sort(data, pivot_index, high)
    else:
        yield data, []

def partition(data, low, high):
    pivot = data[high]
    i = low - 1
    states = []
    for j in range(low, high):
        states.append((data[:], [j, high]))
        if data[j] <= pivot:
            i += 1
            data[i], data[j] = data[j], data[i]
            states.append((data[:], [i, j]))
    data[i + 1], data[high] = data[high], data[i + 1]
    states.append((data[:], [i+1, high]))
    return i + 1, states

# ========== Drawing ==========
def draw_data(canvas, data, color_positions, sorted_done=False):
    canvas.delete("all")
    c_height = 400
    c_width = 600
    x_width = c_width / (len(data) + 1)
    offset = 30
    spacing = 10
    normalized_data = [i / max(data) for i in data]

    for i, height in enumerate(normalized_data):
        x0 = i * x_width + offset + spacing
        y0 = c_height - height * 350
        x1 = (i + 1) * x_width + offset
        y1 = c_height

        if sorted_done:
            color = "#13CE66"  # green when fully sorted
        elif i in color_positions:
            color = "red"
        else:
            color = "#4A90E2"  # blue
        canvas.create_rectangle(x0, y0, x1, y1, fill=color)

    canvas.update_idletasks()

# ========== Control Logic ==========
def start_sort():
    global generator
    algo = algo_menu.get()
    if algo == "Bubble Sort":
        generator = bubble_sort(data)
    elif algo == "Selection Sort":
        generator = selection_sort(data)
    elif algo == "Insertion Sort":
        generator = insertion_sort(data)
    elif algo == "Quick Sort":
        generator = quick_sort(data, 0, len(data) - 1)
    animate()

def animate():
    global generator
    try:
        arr, positions = next(generator)
        draw_data(canvas, arr, positions)
        root.after(speed_map[speed_menu.get()], animate)
    except StopIteration:
        draw_data(canvas, data, [], sorted_done=True)

def generate_data():
    global data
    data = [random.randint(10, 100) for _ in range(15)]
    draw_data(canvas, data, [])

# ========== GUI ==========
root = tk.Tk()
root.title("Sorting Visualizer (Buggy Version)")

canvas = tk.Canvas(root, width=600, height=400, bg="white")
canvas.pack()

frame = tk.Frame(root)
frame.pack(pady=10)

# Algorithm menu
algo_label = tk.Label(frame, text="Algorithm:")
algo_label.grid(row=0, column=0, padx=5)
algo_menu = ttk.Combobox(frame, values=["Bubble Sort", "Selection Sort", "Insertion Sort", "Quick Sort"])
algo_menu.grid(row=0, column=1, padx=5)
algo_menu.current(0)

# Speed menu
speed_label = tk.Label(frame, text="Speed:")
speed_label.grid(row=0, column=2, padx=5)
speed_menu = ttk.Combobox(frame, values=["Fast", "Medium", "Slow"])
speed_menu.grid(row=0, column=3, padx=5)
speed_menu.current(1)

speed_map = {"Fast": 50, "Medium": 150, "Slow": 500}

# Buttons
tk.Button(frame, text="Generate Data", command=generate_data).grid(row=0, column=4, padx=5)
tk.Button(frame, text="Start Sort", command=start_sort).grid(row=0, column=5, padx=5)

# Initial data
data = []
generate_data()

root.mainloop()
