import string, random



def gen_ref_code(length=4):
    return ''.join(random.choice(string.ascii_letters+string.digits) for _ in range(length))
