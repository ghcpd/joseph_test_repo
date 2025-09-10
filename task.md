# 🔹 Frontend webpage form data format Validation

### 1. **Backend (Django + SQLite)**

* Use **SQLite** as the database.
* Create a Django project and one app.
* Implement a `User` model with fields:

  * `name` (CharField, required)
  * `email` (EmailField, unique)
  * `age` (IntegerField)
  * `gender` (CharField, choices = \[Male, Female, Other])
* Expose REST API endpoints:

  * `GET /api/users/` → return all users (support pagination with `?page=1&size=10`)
  * `POST /api/users/` → create a new user (validate input, return 400 on invalid data)
  * `DELETE /api/users/<id>/` → delete a user

---

### 2. **Frontend (index.html)**

* Page contains:

  * **Form** with Name, Email, Age, Gender, and Register button
  * **Table** displaying registered users, each row with a Delete button

* Required features:

  * **Client-side validation (must-have):**

    * Name cannot be empty
    * Email must be valid format
    * Age must be between 10–120
    * Gender must be selected
    * ❗ If input is invalid, show a **popup alert** specifying which field is wrong (e.g., “Email is invalid” or “Age must be between 10 and 120”).
  * **Search bar** to filter users by name
  * **Sort dropdown** for age ascending/descending
  * **Counter** showing number of displayed users
  * **Delete confirmation** dialog before removing a row

---

### 3. **UI/UX Enhancements**

* **Dark/Light theme toggle** (save preference in `localStorage`, persist after refresh).
* **Notifications** (toast/alert) for success, error, or validation failure.
* **Loading indicator** when fetching or submitting data.
* **Animations:**

  * Fade-in for new rows
  * Fade-out for deleted rows
  * Smooth transitions for theme switching

---

### 4. **Validation & Behavior**

* Client-side validation **must run before submission**, and popup alerts must clearly describe the errors.
* Successfully submitted users should appear immediately in the table.
* Search, sort, and counter must update dynamically.
* Delete action requires confirmation and updates the counter correctly.
* Theme toggle persists after page reload.


