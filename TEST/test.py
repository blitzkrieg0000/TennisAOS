
def generator():
    for x in range(5):
        yield x

gen = generator()

first_item = next(gen)
print("First_Item: ", first_item)

for item in gen:
    print(item)