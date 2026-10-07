"""Bounded food-constraint follow-ups; no ingredient or medical inference.

Only explicit simple meal/restriction clauses are supported. Recent learner turns
supply constraints; tutor text never supplies facts. Unsupported current syntax
returns None so callers do not mistake keyword matches for understanding.
"""

import re

SUBJECT = r"(?:I|my [a-z-]+|he|she|they)"
RESOURCE = r"[a-z][a-z -]{0,35}?"


def _clean(text):
    return text.replace("’", "'").strip()


def _person(subject, relatives):
    subject = subject.casefold()
    if subject == "i":
        return "learner"
    if subject.startswith("my "):
        return subject[3:]
    # Resolve only a single explicitly named person in this same learner turn.
    return next(iter(relatives)) if len(relatives) == 1 else None


def _subject(person):
    return "You" if person == "learner" else f"Your {person}"


def _parse_turn(text):
    text = _clean(text)
    relatives = set(re.findall(r"\bmy ([a-z-]+)\b", text, re.IGNORECASE))
    relatives = {value.casefold() for value in relatives}
    # These separators apply only to the limited declarative grammar below.
    clauses = re.split(r"[.;]+\s*|,?\s+but\s+|,?\s+and\s+", text, flags=re.IGNORECASE)
    events = []
    for raw in clauses:
        clause = re.sub(r"^actually,?\s*", "", raw.strip(), flags=re.IGNORECASE).rstrip(
            "! "
        )
        if not clause:
            continue
        reassignment = re.fullmatch(
            rf"the ({RESOURCE})-free meal is for my ([a-z-]+), not me",
            clause,
            re.IGNORECASE,
        )
        if reassignment:
            resource, person = (s.casefold() for s in reassignment.groups())
            events.append({"kind": "reassign", "person": person, "resource": resource})
            continue
        free = re.fullmatch(
            rf"({SUBJECT}) (need|needs|don't need|do not need|doesn't need|does not need) "
            rf"(?:a |an )?({RESOURCE})-free meal(?: anymore)?",
            clause,
            re.IGNORECASE,
        )
        if free:
            person = _person(free[1], relatives)
            if person is None:
                return None
            events.append(
                {
                    "kind": "free"
                    if free[2].lower() in {"need", "needs"}
                    else "clear_free",
                    "person": person,
                    "resource": free[3].casefold(),
                }
            )
            continue
        restriction = re.fullmatch(
            rf"({SUBJECT}) (?:just )?(can't eat|cannot eat|can eat|avoid|avoids|"
            rf"don't avoid|do not avoid|doesn't avoid|does not avoid|"
            rf"don't like|do not like|doesn't like|does not like) ({RESOURCE})"
            r"(?: anymore| now)?",
            clause,
            re.IGNORECASE,
        )
        if restriction:
            person = _person(restriction[1], relatives)
            if person is None:
                return None
            action, resource = restriction[2].casefold(), restriction[3].casefold()
            kind = (
                "cannot"
                if action in {"can't eat", "cannot eat"}
                else "can"
                if action == "can eat"
                else "avoid"
                if action in {"avoid", "avoids"}
                else "dislike"
                if action.endswith("like")
                else "clear_avoid"
            )
            events.append({"kind": kind, "person": person, "resource": resource})
            continue
        meal = re.fullmatch(
            rf"({SUBJECT})(?:'d like| would like| want| wants) "
            r"([a-z][a-z -]{0,45}?)(?: because ([a-z][a-z ', -]{0,65}))?",
            clause,
            re.IGNORECASE,
        )
        if meal:
            person = _person(meal[1], relatives)
            dish = meal[2].casefold()
            if person is None or dish.startswith(("to ", "you ")):
                return None
            events.append(
                {"kind": "meal", "person": person, "meal": dish, "reason": meal[3]}
            )
            continue
        return None
    return events or None


def _ack(event):
    person, kind, resource = event["person"], event["kind"], event["resource"]
    subject = _subject(person)
    if kind == "free":
        target = "you" if person == "learner" else f"your {person}"
        return f"The {resource}-free meal is for {target}."
    verb = {
        "cannot": "can't eat",
        "can": "can eat",
        "avoid": "avoid" if person == "learner" else "avoids",
        "dislike": "don't like" if person == "learner" else "doesn't like",
    }[kind]
    return f"{subject} {verb} {resource}."


def plan_food(text, history=()):
    """Return explicit known facts and authored unanswered choices, or None.

    History is limited to four learner turns. A current reassignment removes a
    previous learner restriction before acknowledging the new person. Positive
    'can eat' retracts a prior inability; it is not a food-safety recommendation.
    """
    current = _parse_turn(text)
    if current is None:
        return None
    constraints = {}
    remembered_meals = {}

    def apply(events):
        for event in events:
            person, kind = event["person"], event["kind"]
            if kind == "meal":
                remembered_meals[(person, event["meal"])] = event
                continue
            resource = event["resource"]
            if kind == "reassign":
                for key in list(constraints):
                    if key[:2] == ("learner", resource):
                        del constraints[key]
                event = {**event, "kind": "free"}
                kind = "free"
            category = "ability" if kind in {"cannot", "can"} else kind
            if kind.startswith("clear_"):
                constraints.pop((person, resource, kind.removeprefix("clear_")), None)
            else:
                # Ability and preference are distinct: can eat does not mean likes.
                constraints[(person, resource, category)] = event

    for row in history[-4:]:
        source = row.get("learner_text", "")
        events = _parse_turn(source)
        if events:
            apply(events)
        elif re.search(r"\b(?:eat|avoid|food|meal|free)\b", source, re.IGNORECASE):
            # An unparsed later restriction/revision must not preserve stale facts.
            constraints.clear()
    old_meals = dict(remembered_meals)
    apply(current)
    meals = [e for e in current if e["kind"] == "meal"]
    active = [e for e in constraints.values() if e["kind"] != "can"]
    if not meals or not active:
        return None
    # Prefer the learner's explicit current meal; never assign someone else's dish.
    meal = next((m for m in meals if m["person"] == "learner"), meals[0])
    person, dish = meal["person"], meal["meal"]
    target = "you" if person == "learner" else f"your {person}"
    # A reason from the same person and exact dish is already known.
    reason = meal["reason"] or old_meals.get((person, dish), {}).get("reason")
    choices = []
    bare = re.sub(r"^(?:a|an|the|some|my) ", "", dish)
    if " " not in bare:
        choices.append(
            {
                "intent": "meal_preference",
                "question": f"What kind of {bare} would {target} like?",
            }
        )
    if not reason:
        choices.append(
            {"intent": "meal_reason", "question": f"What made {target} choose {dish}?"}
        )
    choices.extend(
        [
            {
                "intent": "meal_pairing",
                "question": f"What would {target} like to have with {dish}?",
            },
            {
                "intent": "other_meals",
                "question": f"Apart from {dish}, what other meals {'do you' if person == 'learner' else f'does your {person}'} enjoy?",
            },
        ]
    )
    if not choices:
        return None
    # Acknowledge explicit permissions too when a separate active preference exists.
    acknowledged = list(constraints.values())
    return {
        "prefix": " ".join(_ack(e) for e in acknowledged),
        "known_information": {
            "meals": meals,
            "constraints": acknowledged,
            "meal_reason": reason,
            "evidence_scope": "explicit learner clauses; latest four turns",
        },
        "choices": choices,
    }
