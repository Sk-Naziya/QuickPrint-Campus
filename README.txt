QUICKPRINT CAMPUS - WEBSITE SETUP
=================================

FILES INCLUDED
--------------
index.html       Main landing page
style.css        Landing-page styling
script.js        Mobile navigation + scroll animations
interest.html    Interest-list form
interest.css     Interest form + success-page styling
success.html     Submission success page
assets/          Local website assets folder

1. RUN THE LANDING PAGE
-----------------------
In VS Code, open this folder and use Live Server on index.html.
Do NOT open the HTML by double-clicking the file if you want to test FormSubmit.

2. FORM EMAIL
-------------
The form sends submissions to:
quickprintcampus@gmail.com

FormSubmit requires the destination email to be activated the first time you submit.
Check your inbox and click the activation/confirmation link if FormSubmit asks for it.

3. IMPORTANT: SET THE SUCCESS PAGE URL
--------------------------------------
Open interest.html and find:

https://YOUR-GITHUB-USERNAME.github.io/QuickPrint-Campus/success.html

Replace YOUR-GITHUB-USERNAME with your real GitHub username.
Example:
https://naziya123.github.io/QuickPrint-Campus/success.html

This is required for the hosted GitHub Pages redirect after a successful submission.

4. PUBLISH ON GITHUB PAGES
--------------------------
Create a GitHub repository named:
QuickPrint-Campus

Upload:
index.html
style.css
script.js
interest.html
interest.css
success.html
assets/

Then go to:
Repository > Settings > Pages

Choose:
Source: Deploy from a branch
Branch: main
Folder: / (root)

Save and wait for GitHub Pages to publish.
Your website will normally be:
https://YOUR-GITHUB-USERNAME.github.io/QuickPrint-Campus/

5. WADHWANI LINK
-----------------
Paste ONLY your public GitHub Pages LANDING PAGE URL into Wadhwani.
Example:
https://YOUR-GITHUB-USERNAME.github.io/QuickPrint-Campus/

Do NOT paste:
- http://127.0.0.1:5500/
- http://localhost:5500/
- the FormSubmit URL

6. STUDENT CONFIRMATION EMAIL
-----------------------------
The form includes FormSubmit's _autoresponse feature, which sends a confirmation email to the email address entered by the student.

Important: FormSubmit states that autoresponse does not work when CAPTCHA is disabled or when submitting through AJAX. This package therefore uses a normal POST form and does not disable CAPTCHA.

7. GOOGLE SHEETS NOTE
---------------------
This version intentionally does NOT use Google Apps Script because you requested a no-Apps-Script solution.
FormSubmit sends the form submission by email. It is not a Google Sheets database.

If you later need automatic Google Sheets storage as well, use a dedicated integration/backend instead of changing this landing page into a Google Form.
