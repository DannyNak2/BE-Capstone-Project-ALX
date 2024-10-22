# Blogging Platform API

**Blogging Platform API** is a backend solution built with **Django** and **Django REST Framework (DRF)**. This API enables users to create, view, and manage blog posts with features like rating, liking, sharing, searching, filtering, and posting comments. It serves as a robust foundation for any application that requires user-generated blog content.

---

## Features

- **User Authentication** (JWT)
- **Post Management**: Create, update, delete, and view blog posts
- **Draft Management**: Save posts as drafts before publishing
- **Commenting System**: Add, update, delete, and view comments on posts
- **Post Rating and Liking**
- **Post Sharing**: Share posts via email or social media
- **Filtering by Category and Author**
- **Subscription System**: Notify users about new posts from subscribed authors or categories
- **Search and Filter**: Search posts by title, tags, and more

---

## Installation

Follow these steps to set up the **Blogging Platform API** locally:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DannyNak2/BE-Capstone-Project-ALX/blogging_platform_api.git
   cd blogging_platform_api

2. **Create and activate a virtual environment:**
    
 - On Windows:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate

 - On macOS/Linux:
   ```bash
    python -m venv .venv
    source .venv/bin/activate

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt

4. **Apply database migrations:**
    ```bash
    python manage.py migrate

5. **Create a superuser:**
    ```bash
    python manage.py createsuperuser

6. **Run the development server:**
    ```bash
    python manage.py runserver

---

## API Endpoints

Here are the main API endpoints available in the Blogging Platform API:

**User Registration and Authentication**

- POST /register/ – Register a new user
- POST /login/ – Log in a user
- POST /token/refresh/ – Refresh JWT token
- GET /profile/ – Get logged-in user's profile

**Post Management**

- GET /posts/ – List all published blog posts
- POST /posts/ – Create a new blog post
- GET /posts/drafts/ – List user's draft posts
- GET, PUT, DELETE /posts/<id>/ – Retrieve, update, or delete a specific post

**Comments Management**

- GET, POST /posts/<post_id>/comments/ – List or add comments to a post
- PUT, DELETE /posts/<post_id>/comments/<comment_id>/ – Update or delete a specific comment

**Post Features**

- GET /posts/top-liked/ – List top liked posts
- GET /posts/top-rated/ – List top rated posts
- POST /posts/<id>/like/ – Like a specific post
- POST /posts/<id>/rate/ – Rate a specific post
- POST /posts/<id>/share/ – Share a specific post

**Subscription Management**

- OST /subscribe/ – Subscribe to a category or author
- DELETE /unsubscribe/<id>/ – Unsubscribe from a category or author
- POST /new-post/ – Notify users of new posts from subscribed authors/categories

**Search and Filtering**

- GET /posts/category/<category_id>/ – Filter posts by category
- GET /posts/author/<author_id>/ – Filter posts by author


---


## Authentication

This project uses JWT (JSON Web Token) for authentication. To access protected endpoints, include a valid JWT token in the Authorization header:

    ``makefile
    Authorization: Bearer <your-token>

---

## Testing

To run the test suite:

    ``bash
    python manage.py test

---

## Deployment

To deploy the **Blogging Platform API** on platforms like **Heroku** or **PythonAnywhere**, follow these steps:

1.**Create an account** on your chosen platform.

2.**Create a new** app in the platform's dashboard.

3.**Set environment variables:**
- SECRET_KEY
- DEBUG (set to False for production)
- Database settings (e.g., PostgreSQL for production)

4.**Deploy your code using Git:**
On Heroku: git push heroku main
On PythonAnywhere: Follow their Django deployment guide.

5.**Test your deployed API** by accessing the public URL provided by the platform.

---

## Contributing

Contributions are welcome! To contribute to the **Blogging Platform API**:

1.**Fork the repository**.
2.**Create a new branch** for your feature:

    ``bash
    git checkout -b feature/your-feature-name

3.**Make your changes** and commit them:

    ``bash
    git commit -m "Add your feature"

4.**Push your changes**:

    ``bash
    git push origin feature/your-feature-name

5.**Submit a pull request**.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## Contact

For any inquiries or feedback, please reach out to: danielnakachew1@gmail.com


