# Video Inspo
## Video Demo:  <URL HERE> https://youtu.be/79cgQiZo6z8
## Description:
Video Inspo is a streamlined web application for content creators to collect, categorize, and revisit video inspiration across platforms. It allows you to register, login, logout and reset your account's password. It lets you add and remove video links from YouTube, TikTok, and Instagram. You can assign moods, content types, and tags, add personal notes, and use those as filters to organize. Whether you’re planning campaigns, building edits, or tracking creative references, the organizer keeps your entire inspiration library searchable, structured, and ready whenever you need it.

The project folder includes a static folder, which contains the necessary image files and a css file in case I wanted to customize any element's style (I didn't use it in this case because Bootstrap's styling is sufficient enough). It also has a template folder including all the html templates:
- Layout.html is the base html file that other templates are built based upon because it contains the consistent head, nav bar and footer.
- Login.html and register.html allow user to register and log into their account, while reset.html allows user to reset their password if needed.
- Index.html is the main dashboard of the web application. It displays a collection of videos that were saved by the user and can be filtered out by social platforms (Youtube, Tiktok and Instagram), content types, moods and tags. User can also sort the list in order of oldest or latest. There are also buttons to edit or delete on each video card.
- Add.html displays a form for user to add a video link to the database and metadata like content type, mood, etc. is also added here.
- Delete.html is a confirmation page to delete a video that user chooses to delete on index.html.
- Edit.html displays a form that contains the current metadata about a video that user chooses to edit on index.html. User can then make any changes to this video.
- Apology.html displays an error message whenever something goes wrong (borrowed from Finance in Week 9)

App.py is the core Python file that handles the backend of this web application. It begins by configuring the Flask app, importing the necessary functions, session handling, and SQLite database connection, ensuring each user’s data is stored securely and isolated through login‑protected routes. The file defines several key routes that power the app’s functionality:
- Index route loads filter options that are already in the database (table videos) to display to users to choose. It then takes the chosen filter options by user and puts together a query to get the appropriate videos from the database. Finally, it passes these videos onto the index.html page.
- Add route load up all the existing moods, tags and content types in the database if they exist for the users to choose when adding a video. If not, they can choose "Other" and enter a new value. The function also checks to see if the video already exists in the database. After filling out the form and submitting, the function takes the input and insert a new video into table videos. The video's thumbnail is generated using function get_instagram_thumbnail, get_tiktok_thumbnail or get_youtube_thumbnail from helpers.py depending on the platform.
- Delete route handles the logic of removing a video from table videos along with deleting the local thumbnail files linked to it. It checks whether the video exists in the database. If it does, the function renders a confirmation page to ask the user to the confirm the deletion. If not, the function returns an apology error message.
- Edit route allows users to update the details of an existing video. If method is GET, it retrieves the video's current data and displays it to the user via a form. Similar to add, user can either choose a different value from the dropdown or choose "Other" and enter a new value. If method is POST, the function takes in the input (changes made to the video) and update it in the database. After saving the changes, the function flashes a success message and redirects the user back to the homepage.
- Login, logout, register and reset are borrowed almost completely from week 9 Finance problem set. The login function clears any existing session before validating username and password, checking the database and storing the user's ID in the session to log user in. The logout function clears the session and redirects the user back to the login page. The reset function verifies the username and old password and ensures the new one is different before updating the stored hash password for the user and sending them to the login page. The register functions validates the username, password and password (again) before inserting it into the database and logging the user in.

Helpers.py contains 2 functions from Finance as well, including apology and login_required. Using Copilot, I generated and refined 3 functions to fetch thumbnail urls for each video depending their platforms.

Schema.sql contains all the SQL statements I use to create the database video.db used for this web application.



