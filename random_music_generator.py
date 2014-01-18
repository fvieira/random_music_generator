import abjad
from abjad import Rest, Note, Staff, Score, Measure, Duration as D, show
from fractions import Fraction as F
import random
import copy

DEFAULT_NATURAL_PITCHES = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23]

# List of pairs duration/probability. A duration with probability 5
# compared to a duration with probability 3 will appear 5/3 times more.
DEFAULT_DURATIONS = [(D(1), F(1, 14)), (D(1, 2), F(3, 14)), (D(1, 4), F(5, 14)), (D(1, 8), F(5, 14))]

DEFAULT_SCORE_LENGTH = 20
DEFAULT_MEASURE_SIZE = 4

DEFAULT_REST_PROBABILITY = F(1, 5)
DEFAULT_DOT_PROBABILITY = F(1, 5)


class RandomMusicGenerator(object):
    def __init__(self, pitches=None, durations=None,
                 rest_probability=DEFAULT_REST_PROBABILITY, dot_probability=DEFAULT_DOT_PROBABILITY):
        if pitches is None:
            self.pitches = DEFAULT_NATURAL_PITCHES
        if durations is None:
            self.durations = DEFAULT_DURATIONS
        self.rest_probability = rest_probability
        self.dot_probability = dot_probability
        self.minimum_duration = min(self.durations, key=lambda d: d[0])[0]

    def generate_random_score(self, length=DEFAULT_SCORE_LENGTH, measure_size=DEFAULT_MEASURE_SIZE):
        staff = Staff([])
        score = Score([staff])
        for measure_number in xrange(length):
            measure = self.generate_random_measure(measure_size)
            staff.append(measure)
        return score

    def generate_random_measure(self, measure_size=DEFAULT_MEASURE_SIZE):
        durations = copy.deepcopy(self.durations)
        measure_space_left = F(measure_size, 4)
        notes = []
        while measure_space_left > 0:
            durations = self.filter_duration_probabilities(durations, measure_space_left)
            duration = self.pick_random_duration(durations)
            # Handle dots
            if (duration != self.minimum_duration and
                    duration * D(3, 2) <= measure_space_left and
                    random.random() < self.dot_probability):
                duration = duration * D(3, 2)
            # Handle rests
            if random.random() < self.rest_probability:
                if notes and isinstance(notes[-1], Rest):
                    try:
                        note = Rest(notes[-1].written_duration + duration)
                        notes.pop()
                    except abjad.AssignabilityError:
                        note = Rest(duration)
                else:
                    note = Rest(duration)
            else:
                pitch = random.choice(self.pitches)
                note = Note(pitch, duration)
            notes.append(note)
            measure_space_left -= duration

        assert measure_space_left == 0
        return Measure((measure_size, 4), notes)

    def filter_duration_probabilities(self, durations, space_left):
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
        assert len(normalized_durations) > 0

        new_total_probability = 0
        for duration, probability in normalized_durations:
            new_total_probability += probability
        assert new_total_probability == 1

        return normalized_durations

    def pick_random_duration(self, durations):
        r = random.random()
        current_probability = 0
        for duration, probability in durations:
            current_probability += probability
            if current_probability >= r:
                return duration


def main():
    random_music_generator = RandomMusicGenerator()
    score = random_music_generator.generate_random_score()
    score.add_double_bar()
    lilypond_file = abjad.lilypondfiletools.make_basic_lilypond_file(score)
    abjad.f(lilypond_file)
    show(score)


if __name__ == '__main__':
    main()
