import itertools
import tkinter as tk
from tkinter import ttk
import pandas as pd
from random import randint

# Входные параметры
num_initial_buses = 10
num_routes = 5
route_times = [randint(50, 70) for _ in range(num_routes)]
num_drivers = 18
working_hours_start = 6
working_hours_end = 27  # 3:00 следующего дня
peak_hours = [(7 * 60, 9 * 60), (17 * 60, 19 * 60)]
passenger_flow = 1000

# Типы водителей
driver_types = {
    'A': {'max_hours': 8, 'break_time': 60},
    'B': {'max_hours': 12, 'rest_days': 2, 'break_time': 20, 'long_break': 40}
}

# Дни недели
weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]


# Проверка, является ли время часом пик
def is_peak_hour(time):
    for start, end in peak_hours:
        if start <= time <= end:
            return True
    return False


# Генерация типа маршрута (цикличный или конечный)
def generate_route_type(route_id):
    if route_id % 2 == 0:
        return "Цикличный путь"
    else:
        return "Конечный путь"


# Форматирование времени (часы и минуты)
def format_time(minutes):
    hours = minutes // 60
    mins = minutes % 60
    if hours >= 24:
        hours -= 24
    return f"{hours:02}:{mins:02}"


# Генерация расписания (метод в лоб)
def generate_brute_force_schedule():
    schedule = {
        "Водитель": [],
        "Смена": [],
        "Понедельник": [], "Вторник": [], "Среда": [], "Четверг": [], "Пятница": [], "Суббота": [], "Воскресенье": []
    }

    bus_allocation = itertools.cycle(range(1, num_initial_buses + 1))
    shift_start_times = itertools.cycle(range(working_hours_start, working_hours_end - 8, 6))

    for driver in range(1, num_drivers + 1):
        driver_type = "Тип А" if driver <= num_drivers // 2 else "Тип Б"
        max_hours = driver_types['A']['max_hours'] if driver_type == "Тип А" else driver_types['B']['max_hours']
        shift_start = next(shift_start_times)
        shift_end = shift_start + max_hours

        if shift_end > working_hours_end:
            shift_end = working_hours_end

        schedule["Водитель"].append(f"Водитель {driver} ({driver_type})")
        schedule["Смена"].append(f"{format_time(shift_start * 60)} - {format_time(shift_end * 60)}")

        for day_index, day in enumerate(weekdays):
            shifts = []

            if driver_type == "Тип Б" and day_index % 3 != 0:  # График 1 день работы / 2 дня отдыха
                schedule[day].append("Выходной")
                continue

            if driver_type == "Тип А" and day in ["Суббота", "Воскресенье"]:
                schedule[day].append("Выходной")
                continue

            current_time = shift_start * 60
            long_break_taken = False

            while current_time < shift_end * 60:
                bus_number = next(bus_allocation)
                route_type = generate_route_type(randint(1, num_routes))
                route_time = randint(50, 70)

                if current_time + route_time > shift_end * 60:
                    break

                if driver_type == "Тип Б" and not long_break_taken and current_time >= (shift_start + 4) * 60:
                    shifts.append(f"Длинный перерыв, {format_time(current_time)} - {format_time(current_time + 40)}")
                    current_time += 40
                    long_break_taken = True
                    continue

                if driver_type == "Тип Б" and current_time % (2 * 60) == 0:
                    shifts.append(f"Перерыв, {format_time(current_time)} - {format_time(current_time + 15)}")
                    current_time += 15
                    continue

                if driver_type == "Тип А" and current_time >= 13 * 60 and current_time < 14 * 60:
                    shifts.append(
                        f"{route_type}, Автобус {bus_number}, {format_time(current_time)} - {format_time(current_time + route_time)} (Обед)")
                else:
                    shifts.append(
                        f"{route_type}, Автобус {bus_number}, {format_time(current_time)} - {format_time(current_time + route_time)}")

                current_time += route_time + 15

            schedule[day].append("; ".join(shifts))

    return pd.DataFrame(schedule)


# Интерфейс для отображения расписания
def display_schedule_gui(schedule):
    def on_closing():
        root.destroy()

    root = tk.Tk()
    root.title("Расписание автобусов")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky="nsew")

    tree = ttk.Treeview(frame, columns=list(schedule.columns), show="headings")
    for col in schedule.columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)

    for _, row in schedule.iterrows():
        tree.insert("", "end", values=list(row))

    tree.grid(row=0, column=0, sticky="nsew")

    h_scroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(xscrollcommand=h_scroll.set)
    h_scroll.grid(row=1, column=0, sticky="ew")

    exit_button = ttk.Button(frame, text="Выход", command=on_closing)
    exit_button.grid(row=2, column=0, pady=10)

    root.mainloop()


# Генерация расписания
brute_force_schedule = generate_brute_force_schedule()

# Отображение расписания
display_schedule_gui(brute_force_schedule)
