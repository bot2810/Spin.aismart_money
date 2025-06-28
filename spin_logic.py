import random

def generate_spin_amounts():
    category = random.choices(['low', 'mid', 'high'], weights=[90, 8, 2], k=1)[0]
    total = 2.5 if category=='low' else random.choice([3.0,3.5,4.0]) if category=='mid' else 5.0
    parts = [round(random.uniform(0.05, 0.4), 2) for _ in range(14)]
    last = round(total - sum(parts), 2)
    parts.append(last)
    random.shuffle(parts)
    return parts

def get_user_total(spins):
    return round(sum(spins), 2)

def should_block_user():
    return False
