import random
import json

from BaseFuzzer import BaseFuzzer


class MutationFuzzer(BaseFuzzer):
    """Base class for mutational fuzzing"""

    def __init__(self, seed: list[str], min_mutations: int = 1, max_mutations: int = 5) -> None:
        """Constructor.
        `seed` - a list of (input) strings to mutate.
        `min_mutations` - the minimum number of mutations to apply.
        `max_mutations` - the maximum number of mutations to apply.
        """
        self.seed = seed
        self.population = self.seed
        self.seed_index = 0

        self.min_mutations = min_mutations
        self.max_mutations = max_mutations

    def create_candidate(self) -> str:
        """Create a new candidate by mutating a population member"""
        candidate = random.choice(self.population)
        trials = random.randint(self.min_mutations, self.max_mutations)

        for i in range(trials):
            candidate = self.mutate(candidate)

        return candidate

    def fuzz(self) -> str:
        if self.seed_index < len(self.seed):
            # Still seeding
            self.inp = self.seed[self.seed_index]
            self.seed_index += 1
        else:
            # Mutating
            self.inp = self.create_candidate()
        return self.inp

    def mutate(self, inp: str) -> str:
        """Apply a random mutation to the JSON input string"""

        mutators = [
            self.mutation1,
            self.mutation2,
            self.mutation3,
        ]

        mutator = random.choice(mutators)
        return mutator(inp)

    # Q2.6:
    def ma_mutation(self, inp: str) -> str:
        """
        Applique une mutation structurelle respectant ou testant la grammaire JSON :
        - Sur un JSON valide : modification des dictionnaires et listes (ajout, suppression,
          remplacement de type, imbrication).
        - Sur un JSON invalide (fallback) : manipulation structurelle de syntaxe
          (ajouts/suppressions de délimiteurs).
        """
        try:
            data = json.loads(inp)

            def mutate_structure(obj):
                if isinstance(obj, dict):
                    if not obj:
                        obj[f"key_{random.randint(0, 100)}"] = random.choice([None, True, 123, "fuzz"])
                        return obj

                    choice = random.choice(['add', 'delete', 'replace', 'nest'])
                    if choice == 'add':
                        obj[f"fuzz_{random.randint(0, 1000)}"] = random.choice([[], {}, random.randint(-100, 100)])
                    elif choice == 'delete' and obj:
                        k = random.choice(list(obj.keys()))
                        del obj[k]
                    elif choice == 'replace' and obj:
                        k = random.choice(list(obj.keys()))
                        obj[k] = random.choice([None, [], {}, "malformed_type"])
                    elif choice == 'nest' and obj:
                        k = random.choice(list(obj.keys()))
                        obj[k] = {f"nested_{k}": obj[k]}

                    for k, v in list(obj.items()):
                        if isinstance(v, (dict, list)) and random.random() < 0.3:
                            obj[k] = mutate_structure(v)

                elif isinstance(obj, list):
                    choice = random.choice(['add', 'delete', 'nest_item'])
                    if choice == 'add':
                        obj.append(random.choice([None, 42, "item", {}]))
                    elif choice == 'delete' and obj:
                        obj.pop(random.randint(0, len(obj) - 1))
                    elif choice == 'nest_item' and obj:
                        idx = random.randint(0, len(obj) - 1)
                        obj[idx] = [obj[idx]]

                return obj

            mutated_data = mutate_structure(data)
            return json.dumps(mutated_data)

        except (json.JSONDecodeError, TypeError):
            mutations = [
                lambda s: s + '}',
                lambda s: s + ']',
                lambda s: s.replace(':', ',') if ':' in s else s + ':',
                lambda s: s.replace(',', ''),
                lambda s: '{' + s + '}'
            ]
            if inp:
                func = random.choice(mutations)
                return func(inp)
            return "{}"

    def mutation1(self, inp: str) -> str:
        if len(inp) == 0:
            return inp
        chars = list(inp)
        random.shuffle(chars)
        return ''.join(chars)

    def mutation2(self, inp: str) -> str:
        if len(inp) == 0:
            return inp
        index = random.randint(0, len(inp) - 1)
        char = chr(random.randint(32, 126))
        return inp[:index] + char + inp[index:]

    def mutation3(self, inp: str) -> str:
        if len(inp) == 0:
            return inp
        index = random.randint(0, len(inp) - 1)
        return inp[:index] + inp[index].upper() + inp[index:]
