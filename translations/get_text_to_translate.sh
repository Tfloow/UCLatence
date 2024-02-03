pybabel extract -F babel.cfg -k _ -o to_translate.pot ..

pybabel update -i to_translate.pot -d . -l fr

pybabel compile -d .