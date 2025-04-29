# Warbler


# 🐦 Warbler

Warbler is a Twitter-like microblogging web application built with Flask. Users can sign up, post short messages, follow others, and manage their profiles — all in a clean, responsive interface.

---

## 🚀 Features

- 📝 User registration & login
- 💬 Post short messages (warbles)
- 👥 Follow and unfollow other users
- 🔍 View a personalized message feed from followed users
- 🧑‍💼 View and edit user profile information (bio, image, etc.)
- 🔐 Secure password handling and session management


---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, PostgreSQL, SQLAlchemy
- **Frontend**: HTML, CSS (custom + Bootstrap)
- **Auth**: Flask-Login
- **Database**: Supabase (PostgreSQL hosted)

---

## ⚙️ Setup Instructions

1. **Clone the repo**
   ```bash
   git clone https://github.com/your-username/warbler.git
   cd warbler

   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
    createdb warbler
    psql warbler < seed.sql
   flask run
