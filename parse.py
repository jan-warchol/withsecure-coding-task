from enum import Enum
from collections import OrderedDict
import json

# define states the input parser can be in
ParserState = Enum(
    "ParserState",
    ["BEFORE_KEY", "INSIDE_KEY", "BEFORE_VAL", "INSIDE_VAL", "INSIDE_QUOTES"],
)
# hint for the challenge: "XOR with 0x17F"
MAGIC_VALUE = int("0x17F", 16)

class ParseError(Exception):
    pass

def parse(data):
    """Parse event data from string, returning a python dictionary."""

    # helper for seeing what's going on
    def debug():
        print(curr_char+next_char, state, key_acc, value_acc)

    # if we wanted to guarantee that key order will be preserved, we could use
    # OrderedDict
    result = {}
    key_acc = ""
    value_acc = ""
    curr_char = " "  # sentinel value to have something to start with
    state = ParserState.BEFORE_KEY

    # add sentinel value (we need to look 1 char ahead, so add 1 char)
    for next_char in data + " ":
        # debug()
        
        if state == ParserState.BEFORE_KEY:
            # note: there is no information on the key format. I assume that
            # a space must be present between every closing quote of a value
            # and next key, because that's how the sample data looks like.
            if curr_char == " " and next_char != " ":
                state = ParserState.INSIDE_KEY

        elif state == ParserState.INSIDE_KEY:
            if curr_char == ":" and next_char == " ":
                state = ParserState.BEFORE_VAL
            else:
                # It would be strange if spaces appeared inside key names, but
                # I decided to support them just in case, as JSON keys can be
                # arbitrary strings
                key_acc += curr_char

        elif state == ParserState.BEFORE_VAL:
            if curr_char == "\"":
                state = ParserState.INSIDE_VAL

        elif state == ParserState.INSIDE_VAL:
            if curr_char == "\\" and next_char == "\"":
                state = ParserState.INSIDE_QUOTES
                # drop the backslash
            else:
                value_acc += curr_char
                if next_char == "\"":
                    # Not an escaped quote -> value has just finished
                    result[key_acc] = value_acc
                    state = ParserState.BEFORE_KEY
                    key_acc = ""
                    value_acc = ""

        elif state == ParserState.INSIDE_QUOTES:
            if curr_char == "\\" and next_char == "\"":
                state = ParserState.INSIDE_VAL
                # drop the backslash
            else:
                value_acc += curr_char

        curr_char = next_char

    # we should end parsing after a value ends (so before next key), raise
    # an error if that's not the case
    if state != ParserState.BEFORE_KEY:
        raise ParseError

    return result


def dumps(parsed):
    """Export event data stored in a dictionary to our custom format."""
    return " ".join([
        '{0}: "{1}"'.format(k, v.replace('"', '\\"'))
        for k, v
        in parsed.items()
    ])


def calc_sequence(parsed_data):
    """Extract sequence of numbers from event data."""
    sequence = []
    for key in ["one", "two", "three", "four"]:
        value = int(parsed_data[key], 16) ^ MAGIC_VALUE
        sequence.append(value)

    return sequence


# Now this is tricky. First four values in the sequence are 43, 47, 53, 59
# with the differences betweeen them being 4, 6, 6. Both sequence numbers
# themselves and their differences are neither arithmetic sequences,
# geometric sequences, nor fibonacci sequences. However, first and fourth
# item have a difference of 16, which is equal to the base in which the
# numbers are written out, so perhaps that's what connects them.
def calc_next(sequence):
    """Find next value in the sequence."""
    value = sequence[-3] + 16
    encoded = value ^ MAGIC_VALUE # invert operation for XOR is XOR itself
    return "0x{0:x}".format(encoded)


###########################################


with open("event_data.txt") as f:
    data = f.read()

parsed = parse(data)
print("parsed event data:")
print(parsed)

with open("json_data.txt", "w") as f:
    f.write(json.dumps(parsed))

print("\nevent data encoded in json saved to json_data.txt")

sequence = calc_sequence(parsed)
parsed["fifth"] = calc_next(sequence)


print("\nevent with next sequence item added, in original format:")
print(dumps(parsed))
