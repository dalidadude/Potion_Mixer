# Potion Mixing Mechanics
# 2 modes - Manual and Automatic
# Uses dnd "Potion Miscibility" as a base template

import random
import copy
import streamlit as st

STATS = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

ROLL_TABLE = [
    (1, 2, "Explosion"),
    (3, 6, "Poison"),
    (7, 8, "Blinded"),
    (9, 10, "Deafened"),
    (11, 14, "Vomiting"),
    (15, 16, "Stunned"),
    (17, 20, "Nauseous"),
    (21, 25, "Delusion"),
    (26, 30, "Double Null"),
    (31, 40, "Potion Null"),
    (41, 50, "Weak Potions"),
    (51, 55, "Delayed"),
    (56, 60, "Draining"),
    (61, 62, "Healing"),
    (63, 64, "Flying"),
    (65, 66, "Speed"),
    (67, 68, "Unseen"),
    (69, 70, "Courage"),
    (71, 80, "Excess Energy"),
    (81, 85, "Boosting"),
    (86, 90, "Cantrip Energy"),
    (91, 95, "Increased Duration"),
    (96, 98, "Potent Potions"),
    (99, 100, "Life Changing"),
]

DESTROY_RESULTS = ["Explosion", "Poison", "Double Null"]

ADD_ON_RESULTS = [
    "Blinded",
    "Deafened",
    "Vomiting",
    "Stunned",
    "Nauseous",
    "Draining",
    "Boosting",
    "Cantrip Energy"
]

REPLACE_INCOMING_RESULTS = [
    "Healing",
    "Flying",
    "Speed",
    "Unseen",
    "Courage"
]

MODIFY_EXISTING_RESULTS = [
    "Delusion",
    "Potion Null",
    "Weak Potions",
    "Delayed",
    "Increased Duration",
    "Potent Potions",
    "Life Changing"
]

SPECIAL_RESULTS = ["Excess Energy"]

ARCANA_BONUS_TEST = 11
EXCESS_ENERGY_DC = 15

BAD_REROLL_RESULTS = [
    "Explosion",
    "Poison",
    "Double Null",
    "Delusion",
    "Potion Null",
    "Weak Potions"
]

OFFICIAL_POISONS = [
    "Assassin's Blood",
    "Burnt Othur Fumes",
    "Crawler Mucus",
    "Drow Poison",
    "Essence of Ether",
    "Malice",
    "Midnight Tears",
    "Oil of Taggit",
    "Pale Tincture",
    "Purple Worm Poison",
    "Serpent Venom",
    "Torpor",
    "Truth Serum",
    "Wyvern Poison"
]

KEEP_POISONS = [
    "Purple Worm Poison",
    "Wyvern Poison",
    "Midnight Tears"
]

AUTO_REROLL_RESULTS = [
    "Double Null",
    "Explosion"
]

class Effect:
    def __init__(self, name, effect_type, duration_min = None, stat = None, condition = None, delay_rounds=0, num_dice=0,dice_size=0,bonus=0, bonus2 = 0, speed_multiplier = 0):
        self.name = name
        self.effect_type = effect_type
        self.duration_min = duration_min
        self.delay_rounds = delay_rounds

        self.speed_multiplier = speed_multiplier #haste and climb
        self.num_dice = num_dice #heal
        self.dice_size = dice_size #heal

        self.bonus = bonus #for heal, stat changes, str pots, haste AC any Save DCs
        self.bonus2 = bonus2
        self.stat = stat
        self.condition = condition

    def get_text(self):
        text = ""

        if self.effect_type == "Healing":
            text = f"Heals for {clean_number(self.num_dice)}d{self.dice_size} + {clean_number(self.bonus)}"

        elif self.effect_type == "Speed":
            text = f"For {clean_number(self.duration_min)} minutes, speed is x{clean_number(self.speed_multiplier)}, AC +{clean_number(self.bonus)}, and gain {clean_number(self.bonus2)} extra action"

        elif self.effect_type == "Climbing":
            text = f"For {clean_number(self.duration_min)} minutes, gain climb speed equal to {clean_number(self.speed_multiplier)}x your speed and advantage on climbing checks"

        elif self.effect_type == "Invisibility":
            text = f"Become invisible for {clean_number(self.duration_min)} minutes"

        elif self.effect_type == "Stat":
            text = f"{self.stat} modified by {clean_number(self.bonus):+} for {clean_number(self.duration_min)} minutes"

        elif self.effect_type == "Fear Immunity":
            text = "Immune to fear"

        elif self.effect_type == "Condition":
            text = f"Gain condition: {self.condition} for {clean_number(self.duration_min)} minutes"

        elif self.effect_type == "Giant Strength":
            text = f"Strength becomes {clean_number(self.bonus)} for {clean_number(self.duration_min)} minutes"

        elif self.effect_type == "Flight":
            text = f"For {clean_number(self.duration_min)} minutes, gain fly speed equal to {clean_number(self.speed_multiplier)}x your speed"

        elif self.effect_type == "Cantrip Energy":
            text = f"Can cast a cantrip-level magical effect for {clean_number(self.duration_min)} minutes"

        else:
            text = f"{self.name}: no description yet"

        if self.delay_rounds > 0:
            text += f" (Delayed by {clean_number(self.delay_rounds)} rounds)"

        if hasattr(self, "permanent") and self.permanent:
            text += " (PERMANENT)"

        return text

class Potion:
    def __init__(self, name, effects):
        self.name = name
        self.effects = effects


class FinalPotion:
    def __init__(self, first_effect):
        self.effects = [copy.deepcopy(first_effect)]
        self.notes = []
        self.destroyed = False

    def add_effect(self, effect):
        self.effects.append(copy.deepcopy(effect))

    def get_full_text(self):
        if self.destroyed:
            output = ["💀 POTION DESTROYED 💀"]
        else:
            output = ["FINAL POTION:"]
            for effect in self.effects:
                output.append("- " + effect.get_text())

        if self.notes:
            output.append("\nNOTES:")
            for note in self.notes:
                output.append("- " + note)

        return "\n".join(output)


healing_common_effect = Effect(
    name = "Healing",
    effect_type = "Healing",
    duration_min = 0,
    delay_rounds = 0,
    num_dice = 2,
    dice_size = 4,
    bonus = 2,
    bonus2 = 0,
    speed_multiplier = 0
)

healing_uncommon_effect = Effect(
    name = "Greater Healing",
    effect_type = "Healing",
    duration_min = 0,
    delay_rounds = 0,
    num_dice = 4,
    dice_size = 4,
    bonus = 4,
    bonus2 = 0,
    speed_multiplier = 0
)

healing_rare_effect = Effect(
    name = "Superior Healing",
    effect_type = "Healing",
    duration_min = 0,
    delay_rounds = 0,
    num_dice = 8,
    dice_size = 4,
    bonus = 8,
    bonus2 = 0,
    speed_multiplier = 0
)

healing_legendary_effect = Effect(
    name = "Supreme Healing",
    effect_type = "Healing",
    duration_min = 0,
    delay_rounds = 0,
    num_dice = 10,
    dice_size = 4,
    bonus = 20,
    bonus2 = 0,
    speed_multiplier = 0
)

speed_effect = Effect(
    name="Speed",
    effect_type="Speed",
    duration_min=1,
    speed_multiplier=2,
    bonus = 2,
    bonus2 = 1
)

climbing_effect = Effect(
    name = "Climbing",
    effect_type = "Climbing",
    duration_min = 60,
    speed_multiplier=1,
)

flying_effect = Effect(
    name = "Flying",
    effect_type = "Flying",
    duration_min=60,
    speed_multiplier=1
)

invisibility_effect = Effect(
    name="Invisibility",
    effect_type="Invisibility",
    duration_min=60
)

fear_immunity_effect = Effect(
    name="Fear Immunity",
    effect_type="Fear Immunity"
)

hill_giant_strength_effect = Effect(
    name="Hill Giant Strength",
    effect_type="Giant Strength",
    duration_min=60,
    bonus=21
)


ALL_EFFECTS = {
    "Healing": healing_common_effect,
    "Greater Healing": healing_uncommon_effect,
    "Superior Healing": healing_rare_effect,
    "Supreme Healing": healing_legendary_effect,
    "Speed": speed_effect,
    "Climbing": climbing_effect,
    "Flying": flying_effect,
    "Invisibility": invisibility_effect,
    "Fear Immunity": fear_immunity_effect,
    "Hill Giant Strength": hill_giant_strength_effect
}



def clean_number(value):
    if value is None:
        return None
    if value == int(value):
        return int(value)
    return value


def apply_miscibility(final_potion, incoming_effect, roll, poison_override=None):

    result = resolve_roll(roll)

    final_potion.notes.append(
        f"Rolled {roll} → {result} while mixing in {incoming_effect.name}."
    )

    # =========================
    # AUTO REROLLS
    # =========================

    if reroll_var.get() and (result == "Explosion" or result == "Double Null"):

        reroll = random.randint(1, 100)

        final_potion.notes.append(
            f"Auto-reroll triggered for {result}: rerolled into {reroll} → {resolve_roll(reroll)}."
        )

        apply_miscibility(final_potion, incoming_effect, reroll)
        return


    elif result == "Poison":

        chosen_poison = poison_override if poison_override else random.choice(OFFICIAL_POISONS)

        KEEP_POISONS = [
            "Purple Worm Poison",
            "Wyvern Poison",
            "Midnight Tears"
        ]

        if reroll_var.get() and chosen_poison not in KEEP_POISONS:

            reroll = random.randint(1, 100)

            final_potion.notes.append(
                f"Auto-reroll triggered for Poison ({chosen_poison}): rerolled into {reroll} → {resolve_roll(reroll)}."
            )

            apply_miscibility(final_potion, incoming_effect, reroll)
            return

        final_potion.notes.append(
            f"Poison result: the destroyed potion becomes {chosen_poison}."
        )

        final_potion.destroyed = True
        return


    # =========================
    # NORMAL DESTROY RESULTS
    # =========================

    elif result in DESTROY_RESULTS:

        final_potion.notes.append("This result destroys the entire potion.")
        final_potion.destroyed = True


    # =========================
    # ADD ON RESULTS
    # =========================

    elif result in ADD_ON_RESULTS:

        final_potion.add_effect(incoming_effect)

        extra_effect = create_add_on_effect(result)

        if extra_effect is not None:
            final_potion.add_effect(extra_effect)

        final_potion.notes.append(
            f"Added {incoming_effect.name} plus extra effect: {result}."
        )


    # =========================
    # REPLACEMENT RESULTS
    # =========================

    elif result in REPLACE_INCOMING_RESULTS:

        replacement_effect = create_replacement_effect(result)

        if replacement_effect is not None:

            final_potion.add_effect(replacement_effect)

            final_potion.notes.append(
                f"{incoming_effect.name} was replaced with {replacement_effect.name}."
            )

        else:

            final_potion.notes.append(
                f"{incoming_effect.name} was replaced, but no replacement effect was found."
            )


    # =========================
    # MODIFY EXISTING RESULTS
    # =========================

    elif result in MODIFY_EXISTING_RESULTS:

        final_potion.add_effect(incoming_effect)

        if result == "Delusion" or result == "Potion Null":

            if final_potion.effects:

                removed = random.choice(final_potion.effects)

                final_potion.effects.remove(removed)

                final_potion.notes.append(f"{result}: removed {removed.name}.")

            else:

                final_potion.notes.append(f"{result}: no effects to remove.")


        elif result == "Weak Potions":

            for effect in final_potion.effects:
                halve_effect(effect)

            final_potion.notes.append(
                "Weak Potions: halved all numerical effects and durations."
            )


        elif result == "Delayed":

            if final_potion.effects:

                chosen = random.choice(final_potion.effects)

                delay = random.randint(1, 4)

                chosen.delay_rounds += delay

                final_potion.notes.append(
                    f"Delayed: {chosen.name} delayed by {delay} round(s)."
                )


        elif result == "Increased Duration":

            if final_potion.effects:

                chosen = random.choice(final_potion.effects)

                added = random.randint(1, 100)

                if chosen.duration_min is not None:

                    chosen.duration_min += added

                    final_potion.notes.append(
                        f"Increased Duration: added {added} minutes to {chosen.name}."
                    )

                else:

                    final_potion.notes.append(
                        f"Increased Duration wasted on {chosen.name} because it has no duration."
                    )


        elif result == "Potent Potions":

            for effect in final_potion.effects:
                double_effect(effect)

            final_potion.notes.append(
                "Potent Potions: doubled all numerical effects and durations."
            )


        elif result == "Life Changing":

            if final_potion.effects:

                chosen = choose_permanent_effect(final_potion)

                chosen.duration_min = None
                chosen.permanent = True

                final_potion.notes.append(
                    f"Life Changing: {chosen.name} became permanent."
                )


    # =========================
    # SPECIAL RESULTS
    # =========================

    elif result in SPECIAL_RESULTS:

        excess_roll = roll_excess_energy(ARCANA_BONUS_TEST)

        excess_result = resolve_roll(excess_roll)

        while excess_result == "Excess Energy":

            final_potion.notes.append(
                f"Excess Energy rolled {excess_roll} → Excess Energy again, rerolling to avoid loop."
            )

            excess_roll = roll_excess_energy(ARCANA_BONUS_TEST)
            excess_result = resolve_roll(excess_roll)

        final_potion.notes.append(
            f"Excess Energy triggered additional roll {excess_roll} → {excess_result}."
        )

        apply_miscibility(final_potion, incoming_effect, excess_roll)


    # =========================
    # FALLBACK
    # =========================

    else:

        final_potion.notes.append("Unknown result.")
        final_potion.add_effect(incoming_effect)


def mix_in_effect(final_potion, incoming_effect):
    if final_potion.destroyed:
        return

    result = roll_d100_with_auto_reroll()

    if len(result) == 3:
        roll, note, poison_override = result
    else:
        roll, note = result
        poison_override = None

    if note:
        final_potion.notes.append(note)

    apply_miscibility(final_potion, incoming_effect, roll, poison_override)

def mix_multiple_effects(final_potion, incoming_effect, number_of_times):
    for i in range(number_of_times):
        if final_potion.destroyed:
            final_potion.notes.append("Mixing stopped because the potion was destroyed.")
            break

        mix_in_effect(final_potion, incoming_effect)

def get_random_stat():
    return random.choice(STATS)

def create_random_stat_effect(amount):
    stat = get_random_stat()

    if amount > 0:
        name = f"{stat} Boost"
    else:
        name = f"{stat} Drain"

    return Effect(
        name=name,
        effect_type="Stat",
        duration_min=60,
        bonus=amount,
        stat=stat
    )

def create_add_on_effect(result):
    if result == "Blinded":
        return Effect("Blinded", "Condition", duration_min=random.randint(1, 100), condition="Blinded")

    elif result == "Deafened":
        return Effect("Deafened", "Condition", duration_min=random.randint(1, 10) * 60, condition="Deafened")

    elif result == "Vomiting":
        return Effect("Vomiting", "Condition", duration_min=random.randint(1, 10), condition="Vomiting")

    elif result == "Stunned":
        return Effect("Stunned", "Condition", duration_min=random.randint(1, 10), condition="Stunned")

    elif result == "Nauseous":
        return Effect("Nauseous", "Condition", duration_min=random.randint(1, 10) * 60, condition="Nauseous")

    elif result == "Draining":
        return create_random_stat_effect(-2)

    elif result == "Boosting":
        return create_random_stat_effect(2)

    elif result == "Cantrip Energy":
        return Effect("Cantrip Energy", "Cantrip Energy", duration_min=60)

    return None

def create_replacement_effect(result):
    if result == "Healing":
        return copy.deepcopy(healing_rare_effect)

    elif result == "Flying":
        return copy.deepcopy(flying_effect)

    elif result == "Speed":
        return copy.deepcopy(speed_effect)

    elif result == "Unseen":
        return copy.deepcopy(invisibility_effect)

    elif result == "Courage":
        return copy.deepcopy(fear_immunity_effect)

    return None

def halve_effect(effect):
    effect.num_dice /= 2
    effect.bonus /= 2
    effect.bonus2 /= 2
    effect.speed_multiplier /= 2

    if effect.duration_min is not None:
        effect.duration_min /= 2


def double_effect(effect):
    effect.num_dice *= 2
    effect.bonus *= 2
    effect.bonus2 *= 2
    effect.speed_multiplier *= 2

    if effect.duration_min is not None:
        effect.duration_min *= 2

def roll_excess_energy(arcana_bonus):

    first_d20 = random.randint(1, 20)
    total = first_d20 + arcana_bonus

    if reroll_var.get() and total < EXCESS_ENERGY_DC:

        second_d20 = random.randint(1, 20)
        total = second_d20 + arcana_bonus

    if total >= EXCESS_ENERGY_DC:
        return random.randint(81, 100)

    else:
        return random.randint(1, 20)

def resolve_roll(roll):
    for low, high, result in ROLL_TABLE:
        if low <= roll <= high:
            return result
    return "ERROR"

def roll_d100_with_auto_reroll():
    first_roll = random.randint(1, 100)
    first_result = resolve_roll(first_roll)

    if first_result in AUTO_REROLL_RESULTS:
        second_roll = random.randint(1, 100)
        return second_roll, f"Auto-rerolled {first_roll} → {first_result}."

    if first_result == "Poison":
        poison = random.choice(OFFICIAL_POISONS)

        if poison not in KEEP_POISONS:
            second_roll = random.randint(1, 100)
            return second_roll, f"Auto-rerolled {first_roll} → Poison ({poison})."

        return first_roll, f"Kept Poison result because it became {poison}.", poison

    return first_roll, None

def run_mixing():
    global ARCANA_BONUS_TEST
    global manual_final_potion, manual_mixing_effect, manual_current_mix, manual_total_mixes

    starting_name = starting_var.get()
    mixing_name = mixing_var.get()

    number_of_potions = int(mix_count_var.get())
    number_of_mixes = max(0, number_of_potions - 1)

    ARCANA_BONUS_TEST = int(arcana_bonus_var.get())

    starting_effect = ALL_EFFECTS[starting_name]
    mixing_effect = ALL_EFFECTS[mixing_name]

    if mode_var.get() == "Automatic":
        final_potion = FinalPotion(starting_effect)
        mix_multiple_effects(final_potion, mixing_effect, number_of_mixes)

        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, final_potion.get_full_text())

    else:
        manual_final_potion = FinalPotion(starting_effect)
        manual_mixing_effect = mixing_effect
        manual_current_mix = 0
        manual_total_mixes = number_of_mixes

        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, "Manual mode started.\n")
        output_text.insert(tk.END, manual_final_potion.get_full_text())

        continue_button.config(state=tk.NORMAL)


def continue_manual_mix():

    global manual_current_mix
    global manual_pending_roll
    global manual_pending_note
    global manual_pending_poison_override
    global manual_reroll_used

    if manual_final_potion is None:
        return

    if manual_final_potion.destroyed:
        continue_button.config(state=tk.DISABLED)
        reroll_button.config(state=tk.DISABLED)
        return

    if manual_current_mix >= manual_total_mixes:

        output_text.delete("1.0", tk.END)

        output_text.insert(
            tk.END,
            manual_final_potion.get_full_text()
        )

        output_text.insert(
            tk.END,
            "\n\nManual mixing complete."
        )

        continue_button.config(state=tk.DISABLED)
        reroll_button.config(state=tk.DISABLED)

        return


    # =========================
    # FIRST PRESS = GENERATE ROLL
    # =========================

    if manual_pending_roll is None:

        manual_pending_roll = random.randint(1, 100)
        manual_reroll_used = False

        if not reroll_var.get():

            manual_current_mix += 1

            apply_miscibility(
                manual_final_potion,
                manual_mixing_effect,
                manual_pending_roll,
                manual_pending_poison_override
            )

            manual_pending_roll = None
            manual_pending_note = None
            manual_pending_poison_override = None

            output_text.delete("1.0", tk.END)

            output_text.insert(
                tk.END,
                f"Manual mix {manual_current_mix}/{manual_total_mixes}\n\n"
            )

            output_text.insert(
                tk.END,
                manual_final_potion.get_full_text()
            )

            if manual_final_potion.destroyed or manual_current_mix >= manual_total_mixes:
                continue_button.config(state=tk.DISABLED)
                reroll_button.config(state=tk.DISABLED)

            return

        output_text.delete("1.0", tk.END)

        output_text.insert(
            tk.END,
            f"Manual roll ready: {manual_pending_roll} → {resolve_roll(manual_pending_roll)}\n\n"
        )

        if reroll_var.get():

            output_text.insert(
                tk.END,
                "Press Reroll? to reroll once, or Continue Manual Mix again to apply."
            )

            reroll_button.config(state=tk.NORMAL)

        else:

            reroll_button.config(state=tk.DISABLED)

        return


    # =========================
    # SECOND PRESS = APPLY ROLL
    # =========================

    manual_current_mix += 1

    if manual_pending_note:
        manual_final_potion.notes.append(manual_pending_note)

    apply_miscibility(
        manual_final_potion,
        manual_mixing_effect,
        manual_pending_roll,
        manual_pending_poison_override
    )

    manual_pending_roll = None
    manual_pending_note = None
    manual_pending_poison_override = None

    output_text.delete("1.0", tk.END)

    output_text.insert(
        tk.END,
        f"Manual mix {manual_current_mix}/{manual_total_mixes}\n\n"
    )

    output_text.insert(
        tk.END,
        manual_final_potion.get_full_text()
    )

    reroll_button.config(state=tk.DISABLED)

    if manual_final_potion.destroyed or manual_current_mix >= manual_total_mixes:

        continue_button.config(state=tk.DISABLED)
        reroll_button.config(state=tk.DISABLED)


manual_final_potion = None
manual_mixing_effect = None
manual_current_mix = 0
manual_total_mixes = 0

manual_pending_roll = None
manual_pending_note = None
manual_pending_poison_override = None
manual_reroll_used = False


def choose_permanent_effect(final_potion):
    first_choice = random.choice(final_potion.effects)

    if reroll_var.get() and len(final_potion.effects) > 1:
        second_choice = random.choice(final_potion.effects)
        return second_choice

    return first_choice

def reroll_manual_roll():
    global manual_pending_roll
    global manual_pending_note
    global manual_pending_poison_override
    global manual_reroll_used

    if manual_pending_roll is None:
        return

    if manual_reroll_used:
        return

    manual_pending_roll = random.randint(1, 100)
    manual_pending_note = "Manual reroll used."
    manual_pending_poison_override = None
    manual_reroll_used = True

    output_text.delete("1.0", tk.END)

    output_text.insert(
        tk.END,
        f"Manual reroll result: {manual_pending_roll} → {resolve_roll(manual_pending_roll)}\n\n"
    )

    output_text.insert(
        tk.END,
        "Reroll used. Press Continue Manual Mix again to apply this roll."
    )

    reroll_button.config(state=tk.DISABLED)

# =========================
# STREAMLIT GUI
# =========================

st.title("🧪 Potion Mixer")

starting_name = st.selectbox(
    "Starting Potion",
    list(ALL_EFFECTS.keys()),
    index=4
)

mixing_name = st.selectbox(
    "Mixing Potion",
    list(ALL_EFFECTS.keys()),
    index=0
)

number_of_potions = st.number_input(
    "Total Number of Potions",
    min_value=2,
    value=2,
    step=1
)

ARCANA_BONUS_TEST = st.number_input(
    "Arcana Bonus",
    value=11,
    step=1
)

mode = st.selectbox(
    "Mode",
    ["Automatic", "Manual"]
)

reroll_enabled = st.checkbox(
    "Enable Rerolls",
    value=False
)


# =========================
# Fake tkinter replacement
# =========================

class FakeBool:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

reroll_var = FakeBool(reroll_enabled)


# =========================
# SESSION STATE
# =========================

if "manual_final_potion" not in st.session_state:
    st.session_state.manual_final_potion = None

if "manual_current_mix" not in st.session_state:
    st.session_state.manual_current_mix = 0

if "manual_total_mixes" not in st.session_state:
    st.session_state.manual_total_mixes = 0

if "manual_pending_roll" not in st.session_state:
    st.session_state.manual_pending_roll = None

if "manual_reroll_used" not in st.session_state:
    st.session_state.manual_reroll_used = False

if "output" not in st.session_state:
    st.session_state.output = ""


# =========================
# START MIXING
# =========================

if st.button("Mix Potions"):

    starting_effect = ALL_EFFECTS[starting_name]
    mixing_effect = ALL_EFFECTS[mixing_name]

    number_of_mixes = max(0, number_of_potions - 1)

    if mode == "Automatic":

        final_potion = FinalPotion(starting_effect)

        mix_multiple_effects(
            final_potion,
            mixing_effect,
            number_of_mixes
        )

        st.session_state.output = (
                f"Manual mix "
                f"{st.session_state.manual_current_mix}/"
                f"{st.session_state.manual_total_mixes}\n\n"
                + final_potion.get_full_text()
        )

    else:

        st.session_state.manual_final_potion = FinalPotion(starting_effect)

        st.session_state.manual_mixing_effect = mixing_effect

        st.session_state.manual_current_mix = 0

        st.session_state.manual_total_mixes = number_of_mixes

        st.session_state.manual_pending_roll = None

        st.session_state.manual_reroll_used = False

        st.session_state.output = "Manual mode started."


# =========================
# MANUAL MODE
# =========================

if mode == "Manual" and st.session_state.manual_final_potion is not None:

    final_potion = st.session_state.manual_final_potion

    if st.button("Continue Manual Mix"):

        if st.session_state.manual_current_mix < st.session_state.manual_total_mixes:

            # =========================
            # REROLL MODE ENABLED
            # =========================

            if reroll_enabled:

                if st.session_state.manual_pending_roll is None:

                    st.session_state.manual_pending_roll = random.randint(1, 100)

                    st.session_state.manual_reroll_used = False

                    st.session_state.output = (
                        f"Manual roll ready: "
                        f"{st.session_state.manual_pending_roll} → "
                        f"{resolve_roll(st.session_state.manual_pending_roll)}"
                    )

                else:

                    apply_miscibility(
                        final_potion,
                        st.session_state.manual_mixing_effect,
                        st.session_state.manual_pending_roll
                    )

                    st.session_state.manual_current_mix += 1

                    st.session_state.manual_pending_roll = None

                    st.session_state.output = final_potion.get_full_text()

            # =========================
            # REROLLS DISABLED
            # =========================

            else:

                roll = random.randint(1, 100)

                apply_miscibility(
                    final_potion,
                    st.session_state.manual_mixing_effect,
                    roll
                )

                st.session_state.manual_current_mix += 1

                st.session_state.output = (
                        f"Manual mix "
                        f"{st.session_state.manual_current_mix}/"
                        f"{st.session_state.manual_total_mixes}\n\n"
                        + final_potion.get_full_text()
                )


    # =========================
    # REROLL BUTTON
    # =========================

    if (
        reroll_enabled
        and st.session_state.manual_pending_roll is not None
        and not st.session_state.manual_reroll_used
    ):

        if st.button("Reroll?"):

            st.session_state.manual_pending_roll = random.randint(1, 100)

            st.session_state.manual_reroll_used = True

            st.session_state.output = (
                f"Rerolled into "
                f"{st.session_state.manual_pending_roll} → "
                f"{resolve_roll(st.session_state.manual_pending_roll)}"
            )


# =========================
# OUTPUT
# =========================

st.text_area(
    "Potion Result",
    st.session_state.output,
    height=500
)