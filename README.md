census-mockups
==============

Starting to build out some page skeletons here, using importd to run things through a little local server. (This gives us access to Django template tricks and some Python processing, and will help avoid domain issues when we start using D3 to play with data.)

To run locally:

>> clone this repository
>> cd census-mockups
>> mkvirtualenv census --no-site-packages
>> workon census
>> pip install -r requirements.txt
>> python demo.py
>> open http://localhost:8000/profile/