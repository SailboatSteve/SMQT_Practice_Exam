import base64

icon_data = """iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAGwSURBVFhH7ZY7SwNBEMf/d7lLNCABG0s7wUpsBcHOR2Oj4AewsPMrWFgKfgULwc7aRvALWFhZiYVoq4VoXi95mN3N3O0lFwKXhFxMtPCH5XZv7vY3szOze4RvaHRjQRBgGiil4HkepG3b8H0f0whN04q+70MIAWYMwzBgmiYMw4Cu65hEsixDkiRIkoTnOI4RRRGiKEIYhrAsC7Zto91u/0sJwzBCHMfI8xxZliGOY4RhiCAIEIYhkiTB3t4lzs6usL6+gU6ng06ng3a7DVVVMQlUVYVlWTg8PMPJyQV2di6wvX2O/f1rHBxcYXf3Ep1OFysry1hfX4emaX+LgBAC0zSxtraKVquFpaUlzM/PY3Z2FoqiQJZlSJKELMsQBAF5niNNU8RxjDzPkec5CCHQdR2macI0TViWBV3XYRgGVFWFoigYFymlYIxB0zQQQooRUEqLOeecI89zUEqRpimyLEOWZUXwNE2RJAmSJEGapkjTFEmSIE1TpGmKPM+hlEJRFBBCwBgDpRSUUjDGQCkFY6wYASEEnHMQQsA5ByGkCM45B2MMjDFwzsE5B2MMnPMiOOe8CM45x6QghHwCwFHWxOqHT0IAAAAASUVORK5CYII="""

with open('static/favicon.ico', 'wb') as f:
    f.write(base64.b64decode(icon_data))
