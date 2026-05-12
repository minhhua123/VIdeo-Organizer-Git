from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import os

from helpers import apology, get_instagram_thumbnail, get_tiktok_thumbnail, get_youtube_thumbnail, get_instagram_title, get_tiktok_title, get_youtube_title, shorten_title, login_required, extract_urls

# Configure application
app = Flask(__name__)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///video.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET"])
@login_required
def index():
    user_id = session["user_id"]

    # Load filter options
    types = [row["content_type"] for row in db.execute(
        "SELECT DISTINCT content_type FROM videos WHERE user_id = ? AND TRIM(content_type) <> ''",
        user_id
    )]

    moods_list = [row["mood"] for row in db.execute(
        "SELECT DISTINCT mood FROM videos WHERE user_id = ? AND TRIM(mood) <> ''",
        user_id
    )]

    tags = [row["tag"] for row in db.execute(
        "SELECT DISTINCT tag FROM videos WHERE user_id = ? AND TRIM(tag) <> ''",
        user_id
    )]

    # Read filters from GET
    search_query = request.args.get("q")
    platforms = request.args.getlist("platform[]")
    selected_types = request.args.getlist("type[]")
    selected_moods = request.args.getlist("mood[]")
    selected_tag = request.args.get("tag")
    sort = request.args.get("sort")

    # Base query
    query = "SELECT * FROM videos WHERE user_id = ?"
    params = [user_id]

    #search
    if search_query:
        query += " AND (LOWER(title) LIKE ? OR LOWER(content_type) LIKE ?)"
        params.extend([f"%{search_query.lower()}%", f"%{search_query.lower()}%"])

    # Platform filter
    if platforms:
        placeholders = ",".join("?" * len(platforms))
        query += f" AND LOWER(platform) IN ({placeholders})"
        params.extend(platforms)

    # Content type filter
    if selected_types:
        placeholders = ",".join("?" * len(selected_types))
        query += f" AND content_type IN ({placeholders})"
        params.extend(selected_types)

    # Mood filter
    if selected_moods:
        placeholders = ",".join("?" * len(selected_moods))
        query += f" AND mood IN ({placeholders})"
        params.extend(selected_moods)

    # Tag filter
    if selected_tag and selected_tag != "all":
        query += " AND tag = ?"
        params.append(selected_tag)

    # Sorting
    if sort == "recent":
        query += " ORDER BY id DESC"
    elif sort == "oldest":
        query += " ORDER BY id ASC"

    # Execute
    rows = db.execute(query, *params)

    # Build video objects for template
    videos = []
    for row in rows:
        videos.append({
            "id": row["id"],
            "title": row["title"],
            "link": row["link"],
            "thumbnail_url": row["thumbnail"],
            "platform": row["platform"],
            "mood": row["mood"],
            "content_type": row["content_type"],
            "tags": [{"name": row["tag"]}] if row["tag"] else []
        })

    return render_template(
        "index.html",
        videos=videos,
        types=types,
        moods=moods_list,
        tags=tags
    )



@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    mood_options = db.execute("SELECT DISTINCT mood FROM videos WHERE user_id = ? AND mood IS NOT NULL AND TRIM(mood) <> ''", session["user_id"])
    cleaned_moods = []
    for row in mood_options:
        mood = row["mood"]
        if mood.startswith("{") and "mood" in mood:
            # crude but effective cleanup
            mood = mood.replace('{"mood": "', '').replace('"}', '')
        cleaned_moods.append(mood)


    tag_options = db.execute("SELECT DISTINCT tag FROM videos WHERE user_id = ? AND tag IS NOT NULL AND TRIM(tag) <> ''", session["user_id"])
    cleaned_tags = []
    for row in tag_options:
        tag = row["tag"]
        if tag.startswith("{") and "tag" in tag:
            # crude but effective cleanup
            tag = tag.replace('{"tag": "', '').replace('"}', '')
        cleaned_tags.append(tag)

    content_type_options = db.execute("SELECT DISTINCT content_type FROM videos WHERE user_id = ?", session["user_id"])
    cleaned_content_types = []
    for row in content_type_options:
        ct = row["content_type"]
        if ct.startswith("{") and "content_type" in ct:
            # crude but effective cleanup
            ct = ct.replace('{"content_type": "', '').replace('"}', '')
        cleaned_content_types.append(ct)

    if request.method == "GET":
        return render_template("add.html", mood_options=cleaned_moods, tag_options=cleaned_tags, content_type_options=cleaned_content_types)
    # POST
    title = request.form.get("title")
    link = request.form.get("link")
    notes = request.form.get("notes")

    # --- PREVENT DUPLICATE LINKS ---
    existing = db.execute(
        "SELECT id FROM videos WHERE user_id = ? AND link = ?",
        session["user_id"], link
    )

    if existing:
        flash("This video already exists in your library.")
        return render_template(
            "add.html",
            mood_options=cleaned_moods,
            tag_options=cleaned_tags,
            content_type_options=cleaned_content_types
        )



    # --- CONTENT TYPE ---
    selected_ct = request.form.get("content_type")
    new_ct = request.form.get("new_content_type")

    if selected_ct == "__other__" and new_ct and new_ct.strip():
        content_type = new_ct.strip()
    else:
        content_type = selected_ct

    # --- MOOD ---
    selected_mood = request.form.get("mood")
    new_mood = request.form.get("new_mood")

    if selected_mood == "__other__" and new_mood and new_mood.strip():
        mood = new_mood.strip()
    else:
        mood = selected_mood

    # --- TAG ---
    selected_tag = request.form.get("tag")
    new_tag = request.form.get("new_tag")

    if selected_tag == "__other__" and new_tag and new_tag.strip():
        tag = new_tag.strip()
    else:
        tag = selected_tag

    # --- PLATFORM + THUMBNAIL ---
    link_lower = link.lower()
    if "youtube" in link_lower or "youtu.be" in link_lower:
        platform = "YouTube"
        thumbnail = get_youtube_thumbnail(link)
    elif "tiktok" in link_lower:
        platform = "TikTok"
        thumbnail = get_tiktok_thumbnail(link)
    elif "instagram" in link_lower:
        platform = "Instagram"
        thumbnail = get_instagram_thumbnail(link)
    else:
        return apology("Unsupported platform", 400)

    if not thumbnail:
        thumbnail = "/static/thumbnail.jpg"

    # --- AUTO TITLE FETCH (only if user left it blank) ---
    if not title or title.strip() == "":
        if platform == "YouTube":
            raw_title = get_youtube_title(link)
        elif platform == "TikTok":
            raw_title = get_tiktok_title(link)
        elif platform == "Instagram":
            raw_title = get_instagram_title(link)
        else:
            raw_title = None

        title = shorten_title(raw_title) if raw_title else "Untitled"


    # --- INSERT ---
    db.execute(
        "INSERT INTO videos (title, link, thumbnail, platform, content_type, mood, tag, notes, user_id) VALUES (?,?,?,?,?,?,?,?,?)",
        title, link, thumbnail, platform, content_type, mood, tag, notes, session["user_id"]
    )

    flash("Video added successfully!")
    return redirect("/")

@app.route("/bulk_add", methods=["GET", "POST"])
@login_required
def bulk_add():
    mood_options = db.execute("SELECT DISTINCT mood FROM videos WHERE user_id = ? AND mood IS NOT NULL AND TRIM(mood) <> ''", session["user_id"])
    cleaned_moods = []
    for row in mood_options:
        mood = row["mood"]
        if mood.startswith("{") and "mood" in mood:
            # crude but effective cleanup
            mood = mood.replace('{"mood": "', '').replace('"}', '')
        cleaned_moods.append(mood)


    tag_options = db.execute("SELECT DISTINCT tag FROM videos WHERE user_id = ? AND tag IS NOT NULL AND TRIM(tag) <> ''", session["user_id"])
    cleaned_tags = []
    for row in tag_options:
        tag = row["tag"]
        if tag.startswith("{") and "tag" in tag:
            # crude but effective cleanup
            tag = tag.replace('{"tag": "', '').replace('"}', '')
        cleaned_tags.append(tag)

    content_type_options = db.execute("SELECT DISTINCT content_type FROM videos WHERE user_id = ?", session["user_id"])
    cleaned_content_types = []
    for row in content_type_options:
        ct = row["content_type"]
        if ct.startswith("{") and "content_type" in ct:
            # crude but effective cleanup
            ct = ct.replace('{"content_type": "', '').replace('"}', '')
        cleaned_content_types.append(ct)

    if request.method == "GET":
        return render_template("bulk_add.html", mood_options=cleaned_moods, tag_options=cleaned_tags, content_type_options=cleaned_content_types)
    if request.method == "POST":
        links_text = request.form.get("links")
        links = extract_urls(links_text)
        if not links:
            flash("No valid URLs found.")
            return redirect("/bulk_add")
        # --- CONTENT TYPE ---
        selected_ct = request.form.get("content_type")
        new_ct = request.form.get("new_content_type")

        if selected_ct == "__other__" and new_ct and new_ct.strip():
            content_type = new_ct.strip()
        else:
            content_type = selected_ct
        if not content_type:
            flash("Content type is required.")
            return redirect("/bulk_add")
        # --- MOOD ---
        selected_mood = request.form.get("mood")
        new_mood = request.form.get("new_mood")

        if selected_mood == "__other__" and new_mood and new_mood.strip():
            mood = new_mood.strip()
        else:
            mood = selected_mood
        # --- TAG ---
        selected_tag = request.form.get("tag")
        new_tag = request.form.get("new_tag")

        if selected_tag == "__other__" and new_tag and new_tag.strip():
            tag = new_tag.strip()
        else:
            tag = selected_tag

        added_count = 0
        for link in links:
            # Prevent duplicate links
            existing = db.execute(
                "SELECT id FROM videos WHERE user_id = ? AND link = ?",
                session["user_id"], link
            )
            if existing:
                continue

            # Determine platform and thumbnail
            link_lower = link.lower()
            if "youtube" in link_lower or "youtu.be" in link_lower:
                platform = "YouTube"
                thumbnail = get_youtube_thumbnail(link)
                raw_title = get_youtube_title(link)
            elif "tiktok" in link_lower:
                platform = "TikTok"
                thumbnail = get_tiktok_thumbnail(link)
                raw_title = get_tiktok_title(link)
            elif "instagram" in link_lower:
                platform = "Instagram"
                thumbnail = get_instagram_thumbnail(link)
                raw_title = get_instagram_title(link)
            else:
                continue  # Unsupported platform

            if not thumbnail:
                thumbnail = "/static/thumbnail.jpg"

            title = shorten_title(raw_title) if raw_title else "Untitled"

            # Insert into database
            db.execute(
                "INSERT INTO videos (title, link, content_type, mood, tag, thumbnail, platform, user_id) VALUES (?,?,?,?,?,?,?,?)",
                title, link, content_type, mood, tag, thumbnail, platform, session["user_id"]
            )
            added_count += 1

        flash(f"Successfully added {added_count} videos!")
        return redirect("/")

# code generated by VScode, refined by Jack Hua
@app.route("/delete/<int:video_id>", methods=["GET", "POST"])
def delete(video_id):
    video = db.execute("SELECT * FROM videos WHERE id = ?", video_id)
    if not video:
        return apology("Video not found", 404)
    if request.method == "GET":
        return render_template("delete.html", video=video[0])
    elif request.method == "POST":
        thumbnail_url = video[0]["thumbnail"]
        file_path = thumbnail_url.lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)
            print("File deleted.")
        else:
            print("The thumbnail file does not exist.")
        db.execute("DELETE FROM videos WHERE id = ?", video_id)
        flash("Video deleted successfully!")
        return redirect("/")

# code generated by VScode, refined by Jack Hua and Copilot
@app.route("/edit/<int:video_id>", methods=["GET", "POST"])
def edit(video_id):
    # Fetch the video
    rows = db.execute("SELECT * FROM videos WHERE id = ?", video_id)
    if not rows:
        return apology("Video not found", 404)
    video = rows[0]

    # Fetch dropdown options
    content_type_options = [row["content_type"] for row in db.execute(
        "SELECT DISTINCT content_type FROM videos WHERE content_type IS NOT NULL AND content_type != ''"
    )]

    mood_options = [row["mood"] for row in db.execute(
        "SELECT DISTINCT mood FROM videos WHERE mood IS NOT NULL AND mood != ''"
    )]

    tag_options = [row["tag"] for row in db.execute(
        "SELECT DISTINCT tag FROM videos WHERE tag IS NOT NULL AND tag != ''"
    )]

    # GET → render edit page
    if request.method == "GET":
        return render_template(
            "edit.html",
            video=video,
            content_type_options=content_type_options,
            mood_options=mood_options,
            tag_options=tag_options
        )

    # POST → process form submission
    title = request.form.get("title")
    notes = request.form.get("notes")

    # --- CONTENT TYPE ---
    selected_ct = request.form.get("content_type")
    new_ct = request.form.get("new_content_type")

    if selected_ct == "__other__":
        content_type = new_ct.strip() if new_ct else None
    else:
        content_type = selected_ct or video["content_type"]

    # --- MOOD ---
    selected_mood = request.form.get("mood")
    new_mood = request.form.get("new_mood")

    if selected_mood == "__other__":
        mood = new_mood.strip() if new_mood else None
    else:
        mood = selected_mood or video["mood"]

    # --- TAG ---
    selected_tag = request.form.get("tag")
    new_tag = request.form.get("new_tag")

    if selected_tag == "__other__":
        tag = new_tag.strip() if new_tag else None
    else:
        tag = selected_tag or video["tag"]

    # Update the database
    db.execute(
        """
        UPDATE videos
        SET title = ?, content_type = ?, mood = ?, tag = ?, notes = ?
        WHERE id = ?
        """,
        title, content_type, mood, tag, notes, video_id
    )

    flash("Video updated successfully!")
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/reset", methods=["GET", "POST"])
def reset():
    """Reset password"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure old password was submitted
        elif not request.form.get("oldpassword"):
            return apology("must provide old password", 403)

        # Ensure new password was submitted
        elif not request.form.get("newpassword"):
            return apology("must provide new password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("oldpassword")
        ):
            return apology("invalid username and/or old password", 403)
        elif request.form.get("oldpassword") == request.form.get("newpassword"):
            return apology("new password must be different from old password", 403)

        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(request.form.get("newpassword")), rows[0]["id"])
        # Forget any user_id
        session.clear()
        return redirect("/login")
    else:
        return render_template("reset.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()
    # User reached route via GET, display registration form
    if request.method == "GET":
        return render_template("register.html")
    # User reached route via POST (submitting registration form)
    elif request.method == "POST":
        # Query database for username
        username = request.form.get("username")
        password = request.form.get("password")
        # Ensure username is entered
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not password:
            return apology("must provide password", 400)
        elif password != request.form.get("confirmation"):
            return apology("password must match password confirmation", 400)
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?,?)", username, generate_password_hash(password))
        except ValueError:
            return apology("username is already taken", 400)

        # Remember which user has logged in
        rows = db.execute(
            "SELECT id FROM users WHERE username = ?", request.form.get("username")
        )
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")


