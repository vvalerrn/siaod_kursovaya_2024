from datetime import datetime, timedelta
import random


START_TIME = 6  # 6:00
END_TIME = 27  # 3:00 следующего дня (27 часов от начала суток)

ROUTE_DURATION = 60  # минут +-10
ROUTE_VARIATION = 10

DRIVER_TYPE_A = "A"
DRIVER_TYPE_B = "B"

PEAK_HOURS = [(7, 9), (17, 19)]

LOAD_PEAK = 0.7
LOAD_NORMAL = 0.3


WEEK_DAYS = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]


def is_peak_hour(current_time, is_weekend):
    if is_weekend:
        return False
    hour = current_time.seconds // 3600
    return any(start <= hour < end for start, end in PEAK_HOURS) #принимает генератор или последовательность и возвращает True,
                                                                # если хотя бы один элемент в последовательности — это True


def count_active_buses(schedule, current_time):
    return sum(
        1 for entry in schedule
        if entry["start_time"] <= current_time and entry["end_time"] > current_time
    )


def generate_schedule_for_week(num_buses, drivers_type_a, drivers_type_b):
    weekly_schedule = [] #cписок расписаний для каждого дня недели
    daily_driver_info = {day: set() for day in WEEK_DAYS}  # хранение водителей для каждого дня

    driver_b_work_days = {}
    for i in range(drivers_type_b):
        start_day = i % 3  #водители типа Б сдвигаются по дням недели, чтобы равномерно распределить рабочие дни
        driver_b_work_days[f"{DRIVER_TYPE_B}{i + 1}"] = [ # создает ID водителя, например B1,B2 и тд по индексу
            WEEK_DAYS[j] for j in range(start_day, len(WEEK_DAYS), 3) #генерация расписания в зависимости от дня начала работы с шагом три
        ]

    for day_index, day in enumerate(WEEK_DAYS):
        is_weekend = day in ["СБ", "ВС"]
        schedule = []
        current_time = timedelta(hours=START_TIME)


        driver_next_free_time = {
            DRIVER_TYPE_A: [timedelta(hours=8)] * drivers_type_a if not is_weekend else [], #водители типа А свободны всегда с 8 утра
            DRIVER_TYPE_B: [timedelta(hours=0)] * drivers_type_b, #доступны всегда с начала до конца
        }
        bus_next_free_time = [current_time] * num_buses #список из кол-ва автобусов с 6 утра

        #обед водителей типа А
        driver_lunch_taken = [False] * drivers_type_a

        while current_time < timedelta(hours=END_TIME):
            required_buses = int(num_buses * (LOAD_PEAK if is_peak_hour(current_time, is_weekend) else LOAD_NORMAL))
            active_buses = count_active_buses(schedule, current_time)

            for bus in range(num_buses):
                if bus_next_free_time[bus] <= current_time and active_buses < required_buses:
                    driver_type, driver_id = None, None

                    #пытаемся найти водителя типа А
                    for i, free_time in enumerate(driver_next_free_time.get(DRIVER_TYPE_A, [])):
                        if free_time <= current_time and current_time < timedelta(hours=17):
                            # Проверяем, взял ли водитель уже обед
                            if not driver_lunch_taken[i]:
                                # Проверяем, что текущее время >= 12:00
                                absolute_hour = START_TIME + (current_time.seconds // 3600)
                                if absolute_hour >= 12:
                                    driver_type = DRIVER_TYPE_A
                                    driver_id = f"{DRIVER_TYPE_A}{i + 1}"
                                    break
                            else:
                                driver_type = DRIVER_TYPE_A
                                driver_id = f"{DRIVER_TYPE_A}{i + 1}"
                                break


                    #нет доступного водителя типа А, ищем водителя типа Б
                    if driver_type is None:
                        for i, free_time in enumerate(driver_next_free_time[DRIVER_TYPE_B]):
                            driver_b_id = f"{DRIVER_TYPE_B}{i + 1}"
                            if free_time <= current_time and day in driver_b_work_days[driver_b_id]:
                                driver_type = DRIVER_TYPE_B
                                driver_id = driver_b_id
                                break

                    #если нет доступных водителей, пропускаем этот автобус
                    if driver_type is None:
                        continue

                    #генерируем время маршрута
                    route_time = ROUTE_DURATION + random.randint(-ROUTE_VARIATION, ROUTE_VARIATION)
                    start_time = current_time
                    end_time = current_time + timedelta(minutes=route_time)


                    schedule.append({
                        "bus": bus + 1,
                        "driver_id": driver_id,
                        "driver_type": driver_type,
                        "start_time": start_time,
                        "end_time": end_time,
                        "active_buses": active_buses + 1
                    })


                    daily_driver_info[day].add(driver_id)


                    bus_next_free_time[bus] = end_time + timedelta(minutes=15)

                    if driver_type == DRIVER_TYPE_A:
                        if not driver_lunch_taken[int(driver_id[1:]) - 1]:
                            driver_lunch_taken[int(driver_id[1:]) - 1] = True
                            driver_next_free_time[DRIVER_TYPE_A][int(driver_id[1:]) - 1] = end_time + timedelta(
                                minutes=60)  # Обед
                        else:

                            driver_next_free_time[DRIVER_TYPE_A][int(driver_id[1:]) - 1] = end_time + timedelta(
                                minutes=15)
                    else:
                        driver_next_free_time[DRIVER_TYPE_B][int(driver_id[1:]) - 1] = end_time + timedelta(
                            minutes=15)

                    active_buses += 1

            #обновляем текущее время с шагом в 5 минут
            current_time += timedelta(minutes=5)
        weekly_schedule.append(schedule)

    return weekly_schedule, daily_driver_info

#для красивого вывода времени
def format_time(delta):
    base_time = datetime(2024, 1, 1) + delta
    return base_time.strftime("%H:%M")


def print_schedule(weekly_schedule, day_index):
    print(f"Расписание на {WEEK_DAYS[day_index]}:")
    print(
        f"{'Автобус':<10}{'Тип водителя':<15}{'ID водителя':<15}{'Начало маршрута':<20}{'Конец маршрута':<20}{'Активные автобусы':<20}")
    for record in weekly_schedule[day_index]:
        print(
            f"{record['bus']:<10}{record['driver_type']:<15}{record['driver_id']:<15}{format_time(record['start_time']):<20}{format_time(record['end_time']):<20}{record['active_buses']:<20}")


def print_driver_info(daily_driver_info, day_index):
    day = WEEK_DAYS[day_index]
    drivers = daily_driver_info[day]
    print(f"В {day} работали следующие сотрудники:")
    for driver in sorted(drivers):
        print(f" - {driver}")


# Генерация расписания на неделю
num_buses = 10
drivers_type_a = 5
drivers_type_b = 5

weekly_schedule, daily_driver_info = generate_schedule_for_week(num_buses, drivers_type_a, drivers_type_b)

# # Просмотр расписания через консольный ввод
# while True:
#     print("\nВыберите опцию:")
#     print("0-6: Просмотреть расписание на выбранный день недели")
#     print("7: Показать сотрудников, работающих в выбранный день")
#     print("-1: Выйти из программы")
#
#     try:
#         option = int(input("Введите номер опции: "))
#         if option == -1:
#             print("Выход из программы.")
#             break
#         elif 0 <= option <= 6:
#             print_schedule(weekly_schedule, option)
#         elif option == 7:
#             day_index = int(input("Введите номер дня недели (0-6): "))
#             if 0 <= day_index <= 6:
#                 print_driver_info(daily_driver_info, day_index)
#             else:
#                 print("Неверный номер дня. Попробуйте снова.")
#         else:
#             print("Неверный номер опции. Попробуйте снова.")
#     except ValueError:
#         print("Пожалуйста, введите корректное число.")