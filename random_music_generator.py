import abjad
from abjad import Rest, Note, Staff, Score, Measure, Tie
from fractions import Fraction as F
import random
import copy

DEFAULT_NATURAL_PITCHES = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23]

# List of pairs duration/probability. A duration with probability 5
# compared to a duration with probability 3 will appear 5/3 times more.
DEFAULT_DURATIONS = [
    (F(1), F(10)), (F(7, 8), F(1)), (F(6, 8), F(5)), (F(1, 2), F(30)),
    (F(3, 8), F(5)), (F(1, 4), F(50)), (F(1, 8), F(50)),
]


DEFAULT_SCORE_LENGTH = 50
DEFAULT_MEASURE_SIZE = 4

DEFAULT_REST_PROBABILITY = F(1, 5)
DEFAULT_TIE_PROBABILITY = F(1, 3)


class RandomMusicGenerator(object):
    def __init__(self, pitches=None, durations=None, measure_size=DEFAULT_MEASURE_SIZE,
                 rest_probability=DEFAULT_REST_PROBABILITY, tie_probability=DEFAULT_TIE_PROBABILITY):
        self.pitches = DEFAULT_NATURAL_PITCHES if (pitches is None) else pitches
        self.durations = DEFAULT_DURATIONS if (durations is None) else durations
        self.durations = self.filter_duration_probabilities(self.durations, F(measure_size, 4))
        self.measure_size = measure_size
        self.rest_probability = rest_probability
        self.tie_probability = tie_probability

    def generate_random_score(self, length=DEFAULT_SCORE_LENGTH):
        """
        Generates a random score with the given length in measures.
        """
        measure_list = []
        for _ in xrange(length):
            measure = self.generate_random_measure()
            measure_list.append(measure)
            # Handle ties
            if (len(measure_list) > 1 and isinstance(measure_list[-2][-1], Note) and
                    random.random() < self.tie_probability):
                measure_list[-1][0] = Note(measure_list[-2][-1].written_pitch, measure_list[-1][0].written_duration)
                abjad.attach(Tie(), [measure_list[-2][-1], measure_list[-1][0]])

        staff = Staff(measure_list)
        score = Score([staff])
        score.add_double_bar()
        return score

    def generate_random_measure(self):
        """
        Generates a random measure.
        """
        durations = copy.deepcopy(self.durations)
        measure_space_left = F(self.measure_size, 4)
        notes = []
        while measure_space_left > 0:
            duration = self.pick_random_duration(durations)
            # Handle rests
            if random.random() < self.rest_probability:
                if notes and isinstance(notes[-1], Rest):
                    # Merge rest to previous rest
                    try:
                        note = Rest(notes[-1].written_duration + duration)
                        notes.pop()
                    except abjad.exceptiontools.AssignabilityError:
                        note = Rest(duration)
                else:
                    note = Rest(duration)
            else:
                pitch = random.choice(self.pitches)
                note = Note(pitch, duration)
            notes.append(note)
            measure_space_left -= duration
            durations = self.filter_duration_probabilities(durations, measure_space_left)

        assert measure_space_left == 0
        return Measure((self.measure_size, 4), notes)

    def filter_duration_probabilities(self, durations, space_left):
        """
        Filter durations and recalculate probabilities.
        """

        # Filter durations based on whether they still fit
        # in the current measure.
        total_probability = 0
        filtered_durations = []
        for duration, probability in durations:
            if duration <= space_left:
                filtered_durations.append((duration, probability))
                total_probability += probability

        # Since some probability might have been filtered we need to
        # recalculate the probabilities of each duration so that the sum is 1
        normalized_durations = []
        new_total_probability = 0
        for duration, probability in filtered_durations:
            new_probability = F(probability, total_probability)
            normalized_durations.append((duration, new_probability))
            new_total_probability += new_probability

        # Test that the sum is 1 indeed
        if normalized_durations:
            assert new_total_probability == 1

        return normalized_durations

    def pick_random_duration(self, durations):
        """
        Pick a random duration respecting the probabilities associated
        with each duration.
        """
        r = random.random()
        current_probability = 0
        for duration, probability in durations:
            current_probability += probability
            if current_probability >= r:
                return duration


def output_score(score, ly_filepath, as_pdf=True, as_midi=True):
    """
    Output the score as a lilypond file,
    and optionally as a pdf and midi also.
    """
    illustration = score.__illustrate__()
    if as_midi:
        illustration.score_block.append(abjad.lilypondfiletools.MIDIBlock())
    if as_pdf:
        layout_block = abjad.lilypondfiletools.LayoutBlock()
        layout_block.indent = 0
        illustration.score_block.append(layout_block)
    lilypond_format = format(illustration, 'lilypond')
    with open(ly_filepath, 'w') as f:
        f.write(lilypond_format)
    if as_midi or as_pdf:
        abjad.systemtools.IOManager.run_lilypond(ly_filepath)


def main():
    random_music_generator = RandomMusicGenerator()
    score = random_music_generator.generate_random_score()
    ly_filepath = '/tmp/test.ly'
    output_score(score, ly_filepath)
    with open(ly_filepath) as f:
        print(f.read())
    abjad.systemtools.IOManager.open_file('/tmp/test.pdf')


if __name__ == '__main__':
    main()
