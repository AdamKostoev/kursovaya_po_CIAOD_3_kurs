import tkinter as tk
from tkinter import ttk
from random import randint, random, sample, choice

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


# Функция приспособленности (fitness_function)
def fitness_function(schedule):
    penalty = 0
    for day in weekdays:
        for driver_shifts in schedule[day]:
            if "Выходной" in driver_shifts:
                continue
            if any("Перерыв" in shift for shift in driver_shifts):
                penalty -= 1  # Штраф за перерыв
            if len(driver_shifts) > driver_types["A"]["max_hours"]:
                penalty += 5  # Больший штраф за превышение времени
    return max(1, 10 - penalty)  # Базовая приспособленность


# Генерация случайного расписания
def generate_random_schedule():
    schedule = {
        "Водитель": [],
        "Смена": [],
        "Понедельник": [], "Вторник": [], "Среда": [], "Четверг": [], "Пятница": [], "Суббота": [], "Воскресенье": []
    }

    for driver in range(1, num_drivers + 1):
        driver_type = "A" if driver <= num_drivers // 2 else "B"
        max_hours = driver_types[driver_type]['max_hours']
        shift_start = randint(working_hours_start, working_hours_end - max_hours)
        shift_end = shift_start + max_hours

        # Корректируем начало и конец смены, чтобы они укладывались в рамки
        shift_start = max(working_hours_start, shift_start)
        shift_end = min(working_hours_end, shift_end)

        schedule["Водитель"].append(f"Водитель {driver} (Тип {driver_type})")
        schedule["Смена"].append(f"{format_time(shift_start * 60)} - {format_time(shift_end * 60)}")

        for day in weekdays:
            if driver_type == "B" and weekdays.index(day) % 3 != 0:
                schedule[day].append("Выходной")
                continue
            if driver_type == "A" and day in ["Суббота", "Воскресенье"]:
                schedule[day].append("Выходной")
                continue

            shifts = []
            current_time = shift_start * 60
            long_break_taken = False

            while current_time < shift_end * 60:
                route_time = randint(50, 70)
                if current_time + route_time > shift_end * 60:
                    break

                bus_number = randint(1, num_initial_buses)

                if driver_type == "B" and not long_break_taken and current_time >= (shift_start + 4) * 60:
                    shifts.append(f"Длинный перерыв, {format_time(current_time)} - {format_time(current_time + 40)}")
                    current_time += 40
                    long_break_taken = True
                    continue

                if driver_type == "B" and current_time % (2 * 60) == 0:
                    shifts.append(f"Перерыв, {format_time(current_time)} - {format_time(current_time + 15)}")
                    current_time += 15
                    continue

                route_type = generate_route_type(randint(1, num_routes))
                shifts.append(
                    f"{route_type}, Автобус {bus_number}, {format_time(current_time)} - {format_time(current_time + route_time)}")
                current_time += route_time + 15

            schedule[day].append("; ".join(shifts))

    return schedule


# Скрещивание двух расписаний
def crossover(schedule1, schedule2):
    new_schedule = {key: [] for key in schedule1.keys()}
    for key in schedule1.keys():
        if key in ["Водитель", "Смена"]:
            new_schedule[key] = schedule1[key]
        else:
            for d1, d2 in zip(schedule1[key], schedule2[key]):
                new_schedule[key].append(d1 if random() > 0.5 else d2)
    return new_schedule


# Мутация расписания
def mutate(schedule):
    day = choice(weekdays)
    driver_idx = randint(0, num_drivers - 1)
    if day in schedule:
        schedule[day][driver_idx] = generate_random_schedule()[day][driver_idx]
    return schedule


# Генетический алгоритм
def genetic_algorithm(generations=100, population_size=10):
    population = [generate_random_schedule() for _ in range(population_size)]

    for generation in range(generations):
        population = sorted(population, key=fitness_function, reverse=True)
        new_population = population[:2]  # Сохранение лучших решений

        for _ in range(population_size - 2):
            parent1, parent2 = sample(population[:5], 2)
            child = crossover(parent1, parent2)
            if random() < 0.1:  # Вероятность мутации
                child = mutate(child)
            new_population.append(child)

        population = new_population

    best_schedule = max(population, key=fitness_function)
    return best_schedule


# Интерфейс для отображения расписания
def display_schedule_gui(schedule):
    def on_closing():
        root.destroy()

    root = tk.Tk()
    root.title("Расписание автобусов")

    # Основной фрейм
    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky="nsew")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Treeview
    tree = ttk.Treeview(frame, columns=list(schedule.keys()), show="headings", height=20)
    for col in schedule.keys():
        tree.heading(col, text=col)
        tree.column(col, width=200)

    for i in range(len(schedule["Водитель"])):
        row = [schedule[col][i] for col in schedule.keys()]
        tree.insert("", "end", values=row)

    tree.grid(row=0, column=0, sticky="nsew")

    # Скроллбары
    h_scroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    v_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

    h_scroll.grid(row=1, column=0, sticky="ew")
    v_scroll.grid(row=0, column=1, sticky="ns")

    # Кнопка выхода
    exit_button = ttk.Button(frame, text="Выход", command=on_closing)
    exit_button.grid(row=2, column=0, pady=10, sticky="ew")

    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    root.mainloop()


# Генерация расписания
optimized_schedule = generate_random_schedule()

# Отображение расписания
display_schedule_gui(optimized_schedule)

