import random
from datetime import datetime, timedelta

START_TIME = 6  # 6:00
END_TIME = 27   # 3:00


ROUTE_DURATION = 60
ROUTE_VARIATION = 10


DRIVER_TYPE_A = "A"
DRIVER_TYPE_B = "B"


PEAK_HOURS = [(7, 9), (17, 19)]


LOAD_PEAK = 0.7
LOAD_NORMAL = 0.3


WEEK_DAYS = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]


POPULATION_SIZE = 50
GENERATIONS = 100
MUTATION_RATE = 0.1
CROSSING_RATE = 0.5

def is_peak_hour(current_time, is_weekend):
   if is_weekend:
       return False
   hour = current_time.seconds // 3600
   return any(start <= hour < end for start, end in PEAK_HOURS)

def format_time(delta):
   base_time = datetime(2024, 1, 1) + delta
   return base_time.strftime("%H:%M")

def fitness_function(schedule, num_buses, is_weekend):
   active_buses_count = {t: 0 for t in range(START_TIME * 60, END_TIME * 60 + 1, 5)} # t — это ключ (время в минутах, отслеживаем каждые 5 минкт с начала идо конца),
                                                                                        # значение —количество автобусов, работающих в этот момент времени.
   driver_assignments = {} #хранение всех рейсов для каждого водителя (их начало и конец) для отслеживания пересечения маршрутов для одного водителя.
   penalty = 0
   seen_trips = set()

   #для отслеживания обедов водителей A
   driver_lunch_taken = {driver: False for driver in driver_assignments}

   for entry in schedule:
       trip = (entry["bus"], entry["driver_id"], entry["start_time"], entry["end_time"])
       #проверка на дублирование рейсов
       if trip in seen_trips:
           penalty += 100
       else:
           seen_trips.add(trip)

       start_minutes = int(entry["start_time"].total_seconds() // 60)
       end_minutes = int(entry["end_time"].total_seconds() // 60)

       #проверяем часы работы водителя типа A
       if entry["driver_type"] == DRIVER_TYPE_A:
           if start_minutes < 8 * 60 or end_minutes > 17 * 60:
               penalty += 10
           #проверка на обеденный перерыв после 12:00
           if start_minutes >= 12 * 60 and not driver_lunch_taken.get(entry["driver_id"], False):
               penalty += 20  # Штраф за отсутствие обеда
               driver_lunch_taken[entry["driver_id"]] = True

       #проверяем пересечения рейсов для водителей
       driver = entry["driver_id"]
       if driver not in driver_assignments:
           driver_assignments[driver] = []
       for other_start, other_end in driver_assignments[driver]:
           if not (end_minutes <= other_start or start_minutes >= other_end):
               penalty += 5
       driver_assignments[driver].append((start_minutes, end_minutes))

       #проверяем количество автобусов на маршруте
       for t in range(start_minutes, end_minutes, 5):
           if t in active_buses_count:
               active_buses_count[t] += 1

   #штраф за отклонение от требуемого количества автобусов
   for t, count in active_buses_count.items():
       if is_peak_hour(timedelta(minutes=t), is_weekend):
           required = int(num_buses * LOAD_PEAK)
           if count < required:
               penalty += (required - count) * 2
       else:
           required = int(num_buses * LOAD_NORMAL)
           if count < required:
               penalty += (required - count) * 2

   # штраф за отсутствие 15-минутного перерыва у водителей B после 2 часов работы
   for driver, trips in driver_assignments.items():
       if driver.startswith(DRIVER_TYPE_B): #что водитель является водителем типа B
           sorted_trips = sorted(trips, key=lambda x: x[0]) #сортируем рейсы водителя по времени начала
           continuous_work = 0 #для отслеживания продолжительности непрерывной работы
           last_end = None #для хранения времени завершения последнего рейса
           for trip in sorted_trips:
               if last_end is None: #если это первый рейс, вычисляем продолжительность работы
                   continuous_work = trip[1] - trip[0]
               else:
                   # если этот перерыв больше или равен 15 минутам, то работа считается прерванной, и continuous_work сбрасывается на длительность текущего рейса
                   # если же перерыв меньше 15 минут, continuous_work увеличивается на продолжительность текущего рейса
                   gap = trip[0] - last_end #время "перерыва" между рейсами
                   if gap >= 15:
                       # Перерыв
                       continuous_work = trip[1] - trip[0]
                   else:
                       # Продолжение работы
                       continuous_work += (trip[1] - trip[0])
               if continuous_work > 120:  # больше 2 часов
                   penalty += 10
                   continuous_work = 0
               last_end = trip[1]

   return -penalty  # мы стремимся к меньшему штрафу (число меньшее без минуса)


def create_initial_population(num_buses, num_drivers_a, num_drivers_b, day_index, driver_b_schedule):
   is_weekend = WEEK_DAYS[day_index] in ["СБ", "ВС"]
   population = []

   for i in range(POPULATION_SIZE):
       schedule = []
       current_time = timedelta(hours=START_TIME)
       bus_next_free_time = [current_time] * num_buses
       driver_next_free_time_a = [timedelta(hours=8)] * num_drivers_a if not is_weekend else []
       driver_lunch_taken_a = [False] * num_drivers_a if not is_weekend else []
       driver_next_free_time_b = [timedelta(hours=0)] * num_drivers_b

       while current_time < timedelta(hours=END_TIME):
           for bus in range(num_buses):
               if bus_next_free_time[bus] <= current_time:
                   driver_type = random.choice([DRIVER_TYPE_A, DRIVER_TYPE_B])

                   if driver_type == DRIVER_TYPE_A:
                       if is_weekend:
                           continue  #тип A не работает в выходные

                       available_drivers = [i for i, ft in enumerate(driver_next_free_time_a) if ft <= current_time]
                       if not available_drivers:
                           continue
                       driver_num = random.choice(available_drivers)
                       driver_id = f"{DRIVER_TYPE_A}{driver_num + 1}"
                       # Проверка, не нужно ли водителю брать обед
                       if current_time >= timedelta(hours=12) and not driver_lunch_taken_a[driver_num]:
                           # Назначаем обед
                           start_time = current_time
                           end_time = current_time + timedelta(minutes=60)
                           schedule.append({
                               "bus": bus + 1,
                               "driver_id": driver_id,
                               "driver_type": driver_type,
                               "start_time": start_time,
                               "end_time": end_time,
                           })
                           driver_next_free_time_a[driver_num] = end_time + timedelta(minutes=60)
                           driver_lunch_taken_a[driver_num] = True
                           bus_next_free_time[bus] = end_time + timedelta(minutes=15)
                           continue

                   else:
                       available_drivers = [i for i, ft in enumerate(driver_next_free_time_b) if ft <= current_time]
                       driver_candidates = [i for i in available_drivers if WEEK_DAYS[day_index] in driver_b_schedule[f"{DRIVER_TYPE_B}{i + 1}"]]
                       if not driver_candidates:
                           continue
                       driver_num = random.choice(driver_candidates)
                       driver_id = f"{DRIVER_TYPE_B}{driver_num + 1}"


                   route_time = ROUTE_DURATION + random.randint(-ROUTE_VARIATION, ROUTE_VARIATION)
                   start_time = current_time
                   end_time = current_time + timedelta(minutes=route_time)

                   # для водителя A, не допускаем конец рейса позже 17:00
                   if driver_type == DRIVER_TYPE_A and end_time > timedelta(hours=17):
                       continue

                   # если хотя бы один рейс в расписании пересекается
                   if any(s["driver_id"] == driver_id and not (
                           s["end_time"] <= start_time or s["start_time"] >= end_time) for s in schedule):
                       continue

                   # Создаем запись в расписании
                   schedule.append({
                       "bus": bus + 1,
                       "driver_id": driver_id,
                       "driver_type": driver_type,
                       "start_time": start_time,
                       "end_time": end_time,
                   })


                   bus_next_free_time[bus] = end_time + timedelta(minutes=15)


                   if driver_type == DRIVER_TYPE_A:
                       driver_next_free_time_a[driver_num] = end_time
                   else:
                       driver_next_free_time_b[driver_num] = end_time + timedelta(minutes=15)

           #обновляем текущее время с шагом в 5 минут
           current_time += timedelta(minutes=5)
       population.append(schedule)

   return population

def crossover(parent1, parent2):
    if random.random() < CROSSING_RATE:
        if len(parent1) == 0 or len(parent2) == 0:
            return parent1.copy(), parent2.copy()
        point1 = random.randint(0, len(parent1) - 1)
        point2 = random.randint(0, len(parent2) - 1)
        child1 = parent1[:point1] + parent2[point2:]
        child2 = parent2[:point2] + parent1[point1:]
        return child1, child2
    else:
        return parent1.copy(), parent2.copy()


def mutate(schedule, num_drivers_a, num_drivers_b, day_index, driver_b_schedule):
   if random.random() < MUTATION_RATE:
       if not schedule:
           return schedule
       entry = random.choice(schedule) #выбираем случ. один рейс
       driver_type = entry["driver_type"]

       if driver_type == DRIVER_TYPE_A:
           available_drivers = list(range(1, num_drivers_a + 1))
           driver_num = random.choice(available_drivers)
           driver_id = f"{DRIVER_TYPE_A}{driver_num}"
       else:
           available_drivers = [i for i in range(1, num_drivers_b + 1) if
                                WEEK_DAYS[day_index] in driver_b_schedule[f"{DRIVER_TYPE_B}{i}"]] #можем выбрать В работающего только в этот день
           if not available_drivers:
               return schedule
           driver_num = random.choice(available_drivers)
           driver_id = f"{DRIVER_TYPE_B}{driver_num}"

       start_time = entry["start_time"]
       end_time = entry["end_time"]
       if any(s["driver_id"] == driver_id and not (s["end_time"] <= start_time or s["start_time"] >= end_time) for s in
              schedule): #не занят ли выбранный водитель другим рейсом
           return schedule

       #меняем водителя
       entry["driver_id"] = driver_id

   return schedule

def genetic_algorithm(num_buses, num_drivers_a, num_drivers_b, day_index, driver_b_schedule):
   population = create_initial_population(num_buses, num_drivers_a, num_drivers_b, day_index, driver_b_schedule)

   for generation in range(GENERATIONS):
       population = sorted(population,
                           key=lambda s: fitness_function(s, num_buses, WEEK_DAYS[day_index] in ["СБ", "ВС"]),
                           reverse=True) #сортируем популяции по фитнесу

       #выбираем лучшую половину популяции
       next_generation = population[:POPULATION_SIZE // 2]


       while len(next_generation) < POPULATION_SIZE:
           if len(next_generation) < 2:
               parents = next_generation.copy()
           else:
               parents = random.sample(next_generation, 2)
           parent1, parent2 = parents if len(parents) == 2 else (parents[0], parents[0])
           child1, child2 = crossover(parent1, parent2)
           child1 = mutate(child1, num_drivers_a, num_drivers_b, day_index, driver_b_schedule)
           child2 = mutate(child2, num_drivers_a, num_drivers_b, day_index, driver_b_schedule)
           next_generation.extend([child1, child2]) #добавляем в конец списка

       population = next_generation[:POPULATION_SIZE]

   #выбираем лучшее расписания по фитнесу
   best_schedule = max(population, key=lambda s: fitness_function(s, num_buses, WEEK_DAYS[day_index] in ["СБ", "ВС"]))
   return best_schedule

def generate_weekly_schedule(num_buses, num_drivers_a, num_drivers_b):
   driver_b_schedule = assign_driver_b_schedule(num_drivers_b)

   weekly_schedule = [] #список расписаний для каждого дня недели
   daily_driver_info = {day: set() for day in WEEK_DAYS} #какие водители работают в каждый день недели

   for day_index in range(len(WEEK_DAYS)):
       best_schedule = genetic_algorithm(num_buses, num_drivers_a, num_drivers_b, day_index, driver_b_schedule)
       weekly_schedule.append(best_schedule)
       for entry in best_schedule:
           daily_driver_info[WEEK_DAYS[day_index]].add(entry["driver_id"])

   return weekly_schedule, daily_driver_info

def assign_driver_b_schedule(num_drivers_b):
    driver_b_schedule = {}
    for i in range(num_drivers_b):
        schedule = []
        day = i % 3  #смещение для равномерного распределения рабочих дней среди водителей
        while day < len(WEEK_DAYS):
            schedule.append(WEEK_DAYS[day])
            day += 3  #пропускаем 2 дня после рабочего дня
        driver_b_schedule[f"{DRIVER_TYPE_B}{i + 1}"] = schedule
    return driver_b_schedule

def print_schedule(schedule):
   # Рассчитываем количество активных автобусов на начало каждого маршрута
   sorted_schedule = sorted(schedule, key=lambda x: x["start_time"])
   active_buses = []

   for trip in sorted_schedule:
       count = len([s for s in sorted_schedule if s["start_time"] <= trip["start_time"] < s["end_time"]])
       active_buses.append(count)

   print(
       f"{'Автобус':<10}{'Тип водителя':<15}{'ID водителя':<15}{'Начало маршрута':<20}{'Конец маршрута':<20}{'Активные автобусы':<20}")
   for i, record in enumerate(sorted_schedule):
       print(
           f"{record['bus']:<10}{record['driver_type']:<15}{record['driver_id']:<15}{format_time(record['start_time']):<20}{format_time(record['end_time']):<20}{active_buses[i]:<20}")

def print_driver_info(daily_driver_info, day_index):
   day = WEEK_DAYS[day_index]
   drivers = daily_driver_info[day]
   print(f"В {day} работали следующие сотрудники:")
   for driver in sorted(drivers):
       print(f" - {driver}")

if __name__ == "__main__":
   num_buses = 10
   drivers_type_a = 5
   drivers_type_b = 7

   # print("Генерация расписания на неделю...")
   # weekly_schedule, daily_driver_info = generate_weekly_schedule(num_buses, drivers_type_a, drivers_type_b)
   # print("Генерация завершена.")
   #
   # while True:
   #     print("\nВыберите опцию:")
   #     print("0-6: Просмотреть расписание на выбранный день недели")
   #     print("7: Показать сотрудников, работающих в выбранный день")
   #     print("-1: Выйти из программы")
   #     try:
   #         option = int(input("Введите номер опции: "))
   #         if option == -1:
   #             print("Выход из программы.")
   #             break
   #         elif 0 <= option <= 6:
   #             print_schedule(weekly_schedule[option])
   #         elif option == 7:
   #             day_index = int(input("Введите номер дня недели (0-6): "))
   #             if 0 <= day_index <= 6:
   #                 print_driver_info(daily_driver_info, day_index)
   #             else:
   #                 print("Неверный номер дня. Попробуйте снова.")
   #         else:
   #             print("Неверный выбор. Попробуйте снова.")
   #     except ValueError:
   #         print("Пожалуйста, введите корректное число.")

