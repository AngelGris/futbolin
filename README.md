# Futbolin (under development)
## Soccer matches simulator in Python 3

The Futbolin soccer matches simulator takes 2 teams and simmulates a match between them showing the most important plays in text form.

The teams information is hardcoded but in the future will be loaded from a DB.

The Stats class takes an argument in the constructor to indicated which plays should be included in the match's relatory (0 = shows only important plays, 2 = shows all plays). Value 3 shows every play and wait for the user to press enter to continue, for debugging purposes.

The UI is been developed using **Laravel 5.4** and can be found here in it's repository: [Futbolin UI](https://github.com/AngelGris/futbolin-ui)