

# import json

# from pydantic import BaseModel
# import sys

# class Person(BaseModel):
#     name: str
#     age: int
#     sex: str


# def fun(person:Person):
#     print(f"name: {person.name}")
#     print(f"age: {person.age}")
#     print(f"sex: {person.sex}")


# if __name__ == "__main__":

#     param = sys.argv[1]
#     print(f"param: {param}")
#     person = json.loads(param)
#     p = Person(
#         name=person.get("name",""),
#         age=person.get("age",18),
#         sex=person.get("sex","男"))


#     fun(person=p)


# """
# linux:
# uv run .\task4\input_param.py '{"name":"xxx","age":18,"sex":"男"}'

# powershell: 
# $json = '{"name":"xxx","age":18,"sex":"男"}'
# uv run .\task4\input_param.py $json
# """


import argparse

from pydantic import BaseModel

parser = argparse.ArgumentParser()

parser.add_argument("--name",type=str)
parser.add_argument("--age",type=int)
parser.add_argument("--sex",type=str)

args = parser.parse_args()

class Person(BaseModel):
    name: str
    age: int
    sex: str


def fun(person:Person):
    print(f"name: {person.name}")
    print(f"age: {person.age}")
    print(f"sex: {person.sex}")


if __name__ == "__main__":


    p = Person(
        name=args.name,
        age=args.age,
        sex=args.sex
    )


    fun(person=p)