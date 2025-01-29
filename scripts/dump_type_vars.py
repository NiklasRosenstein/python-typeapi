import sys
import typing

assert (3, 7) <= sys.version_info[:2] < (3, 8), "Need Python 3.7 or 3.8."


print()
print("_SPECIAL_ALIAS_TYPEVARS = {")

for key, value in vars(typing).items():
    params = getattr(value, "__parameters__", None)
    if params:
        print(f"  {key!r}: [{', '.join(repr(str(x)) for x in params)}],")

print("}")
