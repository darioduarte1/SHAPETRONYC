from django.test import SimpleTestCase

from exercises.services.weight_scale import get_exercise_weight_scale


class WeightScaleTests(SimpleTestCase):
    def test_micro_weight_counts_generate_real_combinations(self):
        scale = get_exercise_weight_scale({
            "main_weight_options": [20],
            "micro_weight_options": [
                {"count": 2, "weight": 1},
                {"count": 1, "weight": 2},
            ],
        })

        self.assertEqual(scale["micro_weight_options"], [1.0, 1.0, 2.0])
        self.assertEqual(scale["micro_weight_sums"], [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(scale["available_weights"], [20.0, 21.0, 22.0, 23.0, 24.0])

    def test_micro_weight_decimal_values_are_not_rounded_to_half_kilos(self):
        scale = get_exercise_weight_scale({
            "main_weight_options": [20],
            "micro_weight_options": [
                {"count": 2, "weight": "2,3"},
            ],
        })

        self.assertEqual(scale["micro_weight_options"], [2.3, 2.3])
        self.assertEqual(scale["micro_weight_sums"], [2.3, 4.6])
        self.assertEqual(scale["available_weights"], [20.0, 22.3, 24.6])
