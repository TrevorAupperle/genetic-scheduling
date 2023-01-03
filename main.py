import json
from copy import deepcopy
from random import randint, sample, random
from typing import List

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def read_json(filename: str) -> List:
    with open(filename, "r") as f:
        return json.load(f)


SHIFTS = read_json("shifts.json")
SHIFT_LEADERS = read_json("shiftLeaders.json")


def create_shift_ids():
    index = 0
    for shift in SHIFTS:
        for _ in range(shift["slots"]):
            index += 1
    return [None] * index


def get_person_by_name(name, people=SHIFT_LEADERS):
    for _, person in enumerate(people):
        if person["name"] == name:
            return person
    return -1


def test_availability(shift_start, shift_end, shift_day, person):
    availability = person["availability"][DAYS[shift_day]]
    for frame in availability:
        if frame[0] <= shift_start and frame[1] >= shift_end:
            return True
    return False


def check_hard_constraints(shift, person):
    # check if person is available during shift time
    if not test_availability(
        shift["start"], shift["start"] + shift["approxDuration"], shift["day"], person
    ):
        return False

    # if shift is type 3, check if person has car available
    if shift["type"] == 3 and not person["car"]:
        return False

    # TODO: check if person has already been scheduled

    return True


def check_soft_constraints(shift, person):
    return True


def calculate_fitness(genome):
    score = MAX_FITNESS_SCORE
    for shift in genome:
        for slot in shift["assigned"]:
            person = get_person_by_name(slot, SHIFT_LEADERS)
            if person != -1:
                if not check_hard_constraints(shift, person):
                    score -= HARD_CONFLICT
                if not check_soft_constraints(shift, person):
                    score -= SOFT_CONFLICT
    return score


def sort_by_fitness(population):
    population = population = sorted(
        population, key=lambda genome: calculate_fitness(genome), reverse=True
    )


def selection_pair(population):
    return sample(
        population=population,
        k=2,
    )


def tournament_selection(population):
    parents = []
    for _ in range(2):
        tourney = sample(population=population, k=int(len(population) / 4))
        sort_by_fitness(tourney)
        parents.append(tourney[0])
    return parents


def single_point_crossover(a, b):
    if len(a) != len(b):
        raise ValueError("Genomes a and b must be of same length")

    length = len(a)
    if length < 2:
        return a, b

    p = randint(1, length - 1)
    return a[0:p] + b[p:], b[0:p] + a[p:]


def multi_point_crossover(a, b):
    if len(a) != len(b):
        raise ValueError("Genomes a and b must be of same length")

    length = len(a)
    if length < 2:
        return a, b

    p1 = randint(1, int((length / 2) - 1))
    p2 = randint(p1 + 1, length - 1)
    return a[0:p1] + b[p1:p2] + a[p2:], b[0:p1] + a[p1:p2] + b[p2:]


def custom_crossover(a, b):
    a_remaining = []
    a_mask = []
    b_remaining = []
    b_mask = []
    for idx in range(len(a)):
        for p_idx in range(len(a[idx]["assigned"])):
            # perform swap on genome a with b
            if not check_hard_constraints(
                a[idx], get_person_by_name(a[idx]["assigned"][p_idx])
            ):
                if check_hard_constraints(
                    b[idx], get_person_by_name(b[idx]["assigned"][p_idx])
                ):
                    a[idx]["assigned"][p_idx] = b[idx]["assigned"][p_idx]
                else:
                    a_remaining.append(a[idx]["assigned"][p_idx])
            # perform swap on genome b with a
            if not check_hard_constraints(
                b[idx], get_person_by_name(b[idx]["assigned"][p_idx])
            ):
                if check_hard_constraints(
                    a[idx], get_person_by_name(a[idx]["assigned"][p_idx])
                ):
                    b[idx]["assigned"][p_idx] = a[idx]["assigned"][p_idx]
                else:
                    b_remaining.append(a[idx]["assigned"][p_idx])

    for idx in range(len(a)):
        for p_idx in range(len(a[idx]["assigned"])):
            if check_hard_constraints(
                a[idx], get_person_by_name(a[idx]["assigned"][p_idx])
            ):
                if a[idx]["assigned"][p_idx] not in a_mask:
                    a_mask.append(a[idx]["assigned"][p_idx])
                else:
                    if len(a_remaining) <= 0:
                        continue
                    if len(a_remaining) == 1:
                        a[idx]["assigned"][p_idx] = a_remaining[0]
                    rand = randint(0, len(a_remaining) - 1)
                    a[idx]["assigned"][p_idx] = a_remaining[rand]
                    del a_remaining[rand]
            if check_hard_constraints(
                b[idx], get_person_by_name(b[idx]["assigned"][p_idx])
            ):
                if b[idx]["assigned"][p_idx] not in b_mask:
                    b_mask.append(b[idx]["assigned"][p_idx])
                else:
                    if len(b_remaining) <= 0:
                        continue
                    if len(b_remaining) == 1:
                        b[idx]["assigned"][p_idx] = b_remaining[0]
                    rand = randint(0, len(b_remaining) - 1)
                    b[idx]["assigned"][p_idx] = b_remaining[rand]
                    del b_remaining[rand]

    return a, b


def mutation(genome):
    for shift in genome:
        target = randint(0, shift["slots"] - 1)
        temp_person = shift["assigned"][target]
        if random() > MUTATION_PROBABILITY:
            swap_index = randint(0, len(genome) - 1)
            shift["assigned"][target] = genome[swap_index]["assigned"][0]
            genome[swap_index]["assigned"][0] = temp_person
    return genome


def generate_population(size: int):
    # x amount of schedules randomly generated
    population = []
    for _ in range(size):
        # randomly generated schedule
        genome = deepcopy(SHIFTS)
        # shift leaders to assign
        dna = deepcopy(SHIFT_LEADERS)
        # iterate through shifts
        for shift in genome:
            # iterate through slots for current shift
            for _ in range(shift["slots"]):
                # if no shift leaders left, continue
                if len(dna) <= 0:
                    continue
                # if 1 shift leader left, assign that shift leader
                elif len(dna) == 1:
                    shift["assigned"].append(dna[0]["name"])
                # otherwise, get a random shift leader from remaining list
                else:
                    rand = randint(0, len(dna) - 1)
                    # assign random shift leader to the current shift
                    shift["assigned"].append(dna[rand]["name"])
                    # delete the person from the remaining list
                    del dna[rand]

        population.append(genome)
    return population


def schedule_to_string(genome):
    result = ""

    for shift in genome:
        for i in range(75):
            result += "-"
            if i == 74:
                result += "\n"
        result += (
            "|"
            + shift["name"]
            + "\t| "
            + DAYS[shift["day"]]
            + "\t| Slots: "
            + str(shift["slots"])
            + "\t| Type: "
            + str(shift["type"])
            + "\n"
        )
        result += "|Assigned SLs: "
        for j, sl in enumerate(shift["assigned"]):
            result += sl
            if j == len(shift["assigned"]) - 1:
                result += "\n"
            else:
                result += ", "

    return result


def schedule_to_txt_file(genome):
    txt_file = open("Schedule.txt", "w")
    txt_file.write(schedule_to_string(genome))
    txt_file.close()


def run_evolution():
    # shift_ids = create_shift_ids()
    population = generate_population(100)

    for _ in range(GENERATION_LIMIT):
        sort_by_fitness(population)

        next_generation = population[0:2]

        # crossover and mutate
        for _ in range(int(len(population) / 2) - 1):
            parents = tournament_selection(population)
            offspring_a, offspring_b = custom_crossover(parents[0], parents[1])
            # offspring_a = mutation(offspring_a)
            # offspring_b = mutation(offspring_b)
            next_generation += [offspring_a, offspring_b]

        population = next_generation

    population = sorted(
        population, key=lambda genome: calculate_fitness(genome), reverse=True
    )
    schedule_to_txt_file(population[0])
    print("Max Fitness Score: ", calculate_fitness(population[0]))
    print(
        "{0:.0%}".format(
            calculate_fitness(population[0]) / (MAX_FITNESS_SCORE * HARD_CONFLICT)
        )
    )


GENERATION_LIMIT = 5
MAX_FITNESS_SCORE = 84
HARD_CONFLICT = 0.9
SOFT_CONFLICT = 0.1
MUTATION_PROBABILITY = 0.5

run_evolution()
