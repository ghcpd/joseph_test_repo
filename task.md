## 🟦 Frontend Card Display Project (Read-Only, Repo & Issue Title)

You are given a clean environment with **web development enabled**.
Your task is to create a **frontend-only application** with django to display records from a JSON dataset in card-style boxes.
dataset is ./data/merged_data.jsonl
Each record is a GitHub issue/PR entry with the following fields:

```json
{
    "repo": "0xERR0R/blocky",
    "issue_number": 1585,
    "issue_title": "...",
    "issue_body": "...",
    "pull_number": 1593,
    "created_at": "2024-08-30T22:44:53Z",
    "base_commit_sha": "...",
    "merge_commit_sha": "...",
    "instance_id": "...",
    "pr_url": "...",
    "issue_url": "..."
}
```

---

### 1. **Card Display**

* Each card should display **only**:

  * `repo`
  * `issue_title`
* Clicking a card opens a **detail view** showing all the record fields (`issue_body`, `pull_number`, `created_at`, etc.)

---

### 2. **Pagination**

* Default **20 cards per page**
* Users can choose page size (10/20/50)
* Include **Next / Previous / First / Last page controls**
* Display **current page / total pages**

---

### 3. **Responsive Layout**

* Cards should **rearrange automatically** depending on browser width
* Use **CSS Grid or Flexbox**
* Number of cards per row should adapt to screen size

---

### 4. **Style Customization**

* Provide a **left-side settings menu** to allow users to:

  * Choose **card text color**
  * Choose **card background color**
* Settings apply immediately to all visible cards
* Menu should be **fixed on the left side** and collapsible if necessary

---

### 5. **Interaction**

* Clicking a card shows full record details (modal or separate section)
* Pagination updates visible cards **without page reload**
* Style changes update all cards in real time

---

### 6. **Validation**

Ensure that:

* Cards display `repo` and `issue_title` correctly
* Pagination works and updates visible cards correctly
* Layout responds dynamically to browser resizing
* Style changes from the left menu are applied immediately
* Card detail view shows all fields on click

---

### ✅ Notes

* Input data is **read-only JSON**; no backend modification is required
* Focus is on **frontend layout, interactivity, pagination, styling, and responsiveness**
* Use HTML, CSS, and JavaScript (vanilla or libraries)
