import abjad
from abjad import Rest, Note, Staff, Score, Measure, Duration as D, show
from fractions import Fraction as F
import random
import copy

NOTES = ["c'", "d'", "e'", "f'", "g'", "a'", "b'",
         "c''", "d''", "e''", "f''", "g''", "a''", "b''"]

# List of pairs duration/probability. A duration with probability 5
# compared to a duration with probability 3 will appear 5/3 times more.
DURATIONS = [(D(1), F(1)), (D(1, 2), F(3)), (D(1, 4), F(5)), (D(1, 8), F(5))]

REST_PROBABILITY = F(1, 5)


def generate_random_score(length=4):
    staff = Staff([])
    score = Score([staff])
    for measure_number in xrange(length):
        measure = generate_random_measure()
        staff.append(measure)
    return score


def generate_random_measure(measure_size=4, notes=None, durations=None):
    if notes is None:
        notes = []
    if durations is None:
        durations = copy.deepcopy(DURATIONS)
    measure_space_left = F(measure_size, 4)
    while measure_space_left > 0:
        durations = filter_duration_probabilities(durations, measure_space_left)
        duration = pick_random_duration(durations)
        if random.random() < REST_PROBABILITY:
            note = Rest(duration)
        else:
            note = Note(random.choice(NOTES), duration)
        notes.append(note)
        measure_space_left -= duration

    assert measure_space_left == 0
    return Measure((measure_size, 4), notes)


def filter_duration_probabilities(durations, space_left):
    total_probability = 0
    filtered_durations = []
    for duration, probability in durations:
        if duration <= space_left:
            filtered_durations.append((duration, probability))
            total_probability += probability

    normalized_durations = []
    for duration, probability in filtered_durations:
        new_probability = F(probability, total_probability)
        normalized_durations.append((duration, new_probability))

    new_total_probability = 0
    for duration, probability in normalized_durations:
        new_total_probability += probability
    assert new_total_probability == 1

    return normalized_durations


def pick_random_duration(durations):
    r = random.random()
    current_probability = 0
    for duration, probability in durations:
        current_probability += probability
        if current_probability >= r:
            return duration


def main():
    score = generate_random_score(20)
    score.add_double_bar()
    lilypond_file = abjad.lilypondfiletools.make_basic_lilypond_file(score)
    abjad.f(lilypond_file)
    show(score)


if __name__ == '__main__':
    main()
