# Lessume

Lessume takes a PDF file of the users resume and interprets the text. It then organizes the information in a database with which companies and recruiters can use to search for the right applicants.

# Installation

- Create virtual environment
  ```
  python3 -m venv env
  ```
- Open virtual environment
  bash:

  ```
  source  env/bin/activate
  ```

  powershell:

  ```
  .\env\Scripts\Activate
  ```

- install dependencies

  ```
  pip3 install -r requirements.txt
  ```

- Create .env

```
OPENAI_KEY = "add key"
OPENAI_PROMPT = "add prompt"
```