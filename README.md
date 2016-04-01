# Worlds At War

Welcome to the repository containing the source code for Worlds at War, the multiplayer online browser game found [here](https://wawgame.eu). This was my first decent-scale project and more or less how I learnt Python, so the code will be obtuse and likely not very good in places. Apologies for this.

Everyone is free to contribute, and you can best do that by reading up on Python (an excellent first-timer's guide can be found [here](http://learnpythonthehardway.org/book/index.html)), and Django (the reference guide can be found [here](https://docs.djangoproject.com/en/1.8/)). If on the other hand you are better with HTML and CSS, you can help out with that too.

The source is licensed under the MIT licence. There is a separate file containing the full license, but in short: a) you can do anything you want with this as long as I receive the proper attribution, and b) this code comes without warranty.

Questions about this repository (e.g. what does so and so bit of code do?) should be posted [here](https://wawgame.eu/forums/index.php?board=71).
Suggestions, bugs and exploits should be reported [here](https://wawgame.eu/forums/index.php?board=10), [here](https://wawgame.eu/forums/index.php?board=9) and [here](https://wawgame.eu/forums/index.php?board=24) respectively.

Issues on this repository should be focused on specific sections of code rather than a general complaint. Issues raised by non-admins should have a link to the relevant thread on the forums. Please post a suggestion or bug report in the forums before making an issue here.

Please claim a todo task in [this thread](https://wawgame.eu/forums/index.php?topic=10905) before starting to code.

### Overview of contents

* settings.py - General settings file. You'll need to customise this if you're running a local copy of WaW.
* urls.py - Dispatches URL requests to functions.
* templates - Contains HTML which is manipulated by the functions to render a complete webpage.
* wawmembers - Everything else.
  * admin.py - Not much in this file: ban/delete functions and display of objects in the admin view.
  * ajax.py - Anything that needs interaction with the server outside of a page refresh.
  * decorators.py - Misc checks that apply to more than one function.
  * display.py - Converts numbers to text descriptions.
  * forms.py - The logic behind every html form. Names should be self-explanatory.
  * interactions.py - Everything that deals with one world interacting with another. Wars, attacks, spies, etc.
  * loggers.py - Various logs. Ideally to be more comprehensive for all actions.
  * middleware.py - Functions that run for every single request.
  * models.py - All objects live here. This is the interface between Python and database data.
  * news.py - All news items and their effects are here.
  * newsgenerator.py - HTML generation for news items.
  * outcomes_policies.py - Text results from the outcomes of policies.
  * policies.py - Display and actions for policy pages: economic, domestic, diplomatic and fleet.
  * taskgenerator.py - Text generation for tasks.
  * tasks.py - Everything on a timer is here: recurring tasks + tasks after a delay.
  * turnupdates.py - Misc utility functions for turnchange.
  * urls.py - Dispatches URL requests to functions.
  * utilities.py - Misc functions that are used by other files.
  * variables.py - Misc variables and simple functions used in a lot of places.
  * views.py - The main file. Most page functions are carried out here.
  * templatetags - Functions used by the template system.
    * basetags.py - Changes to the base template.
    * filters.py - Simple text manipulation filters.
    * lastonline.py - Implements the last online feature.
    * mildisplay.py - Text manipulation for the military policies page.
    * nextspyaction.py - Notifies when a spy can next take an action.
    * random_quote.py - Quotes that display at the bottom of the page.
    * resourcemine.py - Name and description for trade resources.
    * shipbuildtype.py - HTML for ship building options.
    * tradetable.py - HTML for trade table display.
    * warstatus.py - War status for the galatic search.
  * static - All files served directly by the server.
    * actionnews - Images used by random events.
    * avatarsnflags - Avatar and flag images.
    * backgrounds - Selfexplanatory.
    * cards - Card images for use by the first 52 accounts.
    * css - HTML stylesheets
    * js - HTML javascript
    * personalships - Personal ship images
    * settings - Smaller versions of avatars, flags, backgrounds and personal ship images for use in selecting.
    * wawmembers - Everything else goes here.
