#!/usr/bin/python3

# Imports
import sys
from classes.handler import Handler

# Arguments list:
# 0 = script name
# 1 = home team ID
# 2 = visit team ID
# 3 = debug level
# 4 = output file name (optional)

if len(sys.argv) < 4:
    print('Missing arguments (Home team ID, Visit team ID, Match type, Debug level)')
    exit()

args = []
for i in range(4):
    try:
        args.append(int(sys.argv[i + 1]))
    except ValueError:
        if (i == 0):
            print('Home team ID must be an integer')
        elif (i == 1):
            print('Visit team ID must be an integer')
        elif (i == 2):
            print('Match type must be an integer')
        elif (i == 3):
            print('Debug level must be an integer')
        exit()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

try:
    output_file = sys.argv[5]
except:
    output_file = ''

Handler.execute(args[0], args[1], args[2], args[3], output_file)