from django.db import migrations


EXERCISE_CROP_URLS = {
    "Lat Pulldown": "/exercise-crops/lat_pulldown.PNG",
    "Seated Row Machine": "/exercise-crops/seated_row_machine.PNG",
    "Assisted Pull Up Machine": "/exercise-crops/assisted_pull_up_machine.PNG",
    "Rear Delt Fly": "/exercise-crops/rear_delt_fly.PNG",
    "Barbell Curl": "/exercise-crops/barbell_curl.PNG",
    "Hammer Curl": "/exercise-crops/hammer_curl.PNG",
    "Chest Press Machine": "/exercise-crops/chest_press_machine.PNG",
    "Pec Deck": "/exercise-crops/pec_deck.PNG",
    "Shoulder Press": "/exercise-crops/shoulder_press.PNG",
    "Triceps Pushdown": "/exercise-crops/triceps_pushdown.PNG",
    "Dumbbell Lateral Raise": "/exercise-crops/dumbbell_lateral_raise.PNG",
    "Leg Press": "/exercise-crops/leg_press.PNG",
    "Seated Leg Curl": "/exercise-crops/seated_leg_curl.PNG",
    "Adductor Machine": "/exercise-crops/adductor_machine.PNG",
    "Twenty One Curl": "/exercise-crops/twenty_one_curl.PNG",
    "Scissor Crunch": "/exercise-crops/scissor_crunch.PNG",
    "Ab Wheel": "/exercise-crops/ab_wheel.PNG",
    "Treadmill Incline Walk": "/exercise-crops/treadmill_incline_walk.PNG",
    "Air Bike": "/exercise-crops/air_bike.PNG",
    "Arnold Press": "/exercise-crops/arnold_press.PNG",
    "Dumbbell Pullover": "/exercise-crops/dumbbell_pullover.PNG",
    "Smith Machine Bench Press": "/exercise-crops/smith_machine_bench_press.PNG",
    "Band Bent Over Row": "/exercise-crops/band_bent_over_row.PNG",
    "Barbell Bent Over Row": "/exercise-crops/barbell_bent_over_row.PNG",
    "Dumbbell Bent Over Row": "/exercise-crops/dumbbell_bent_over_row.PNG",
    "Cable Curl": "/exercise-crops/cable_curl.PNG",
    "Dumbbell Curl": "/exercise-crops/dumbbell_curl.PNG",
    "Biceps Curl Machine": "/exercise-crops/biceps_curl_machine.PNG",
}


def apply_crop_urls(apps, schema_editor):
    Exercise = apps.get_model("exercises", "Exercise")

    for name, image_url in EXERCISE_CROP_URLS.items():
        Exercise.objects.filter(name=name).update(image_url=image_url)


class Migration(migrations.Migration):

    dependencies = [
        ("exercises", "0003_exercise_image_localized_name"),
    ]

    operations = [
        migrations.RunPython(apply_crop_urls, migrations.RunPython.noop),
    ]
