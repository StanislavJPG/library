def is_jumping(number: int) -> str:
    lst = [int(x) for x in str(number)]
    return [(k,v) for k,v in zip(lst, lst[1:])]



print(is_jumping(23454))

